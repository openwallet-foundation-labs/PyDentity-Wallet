from flask import (
    Blueprint,
    current_app,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
)
from app.plugins import AgentController, AskarStorage, AskarStorageKeys
from app.operations import sign_in_agent
from app.utils import notification_broadcaster, delete_notification
from asyncio import run as await_

bp = Blueprint("credentials", __name__, url_prefix="/credentials")


@bp.before_request
def before_request_callback():
    if not session.get("client_id"):
        return redirect(url_for("auth.index"))


@bp.route("/offers", methods=["GET"])
def get_credential_offers():
    """Get pending credential offers for the user"""
    wallet_id = session.get("wallet_id")
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    offers = await_(wallet_askar.fetch(AskarStorageKeys.CRED_OFFERS))
    return jsonify({"offers": offers or []})


@bp.route("/offers/<exchange_id>", methods=["GET"])
def view_credential_offer(exchange_id):
    """View credential offer details page"""
    current_app.logger.info(f"=== Viewing Credential Offer: {exchange_id} ===")
    
    agent = await_(sign_in_agent(session.get("wallet_id")))
    if not agent:
        current_app.logger.error("Failed to sign in to agent")
        return redirect(url_for("main.index"))
    
    try:
        # Fetch credential offer details from agent
        current_app.logger.info(f"Fetching credential exchange info for: {exchange_id}")
        offer_details = agent.get_credential_exchange_info(exchange_id)
        current_app.logger.info(f"Offer details: {offer_details}")
        
        # Extract credential exchange record
        cred_ex_record = offer_details.get('cred_ex_record', {})
        current_app.logger.info(f"Credential exchange state: {cred_ex_record.get('state')}")
        
        # Get credential preview attributes
        cred_offer = cred_ex_record.get('cred_offer', {})
        credential_preview = cred_offer.get('credential_preview', {})
        attributes_list = credential_preview.get('attributes', [])
        
        # Convert attributes list to dict
        attributes = {}
        for attr in attributes_list:
            attributes[attr.get('name')] = attr.get('value')
        
        current_app.logger.info(f"Attributes: {attributes}")
        
        # Get schema and issuer info
        schema_id = offer_details.get('by_format', {}).get('cred_offer', {}).get('anoncreds', {}).get('schema_id')
        connection_id = cred_ex_record.get('connection_id')
        
        schema_info = agent.get_schema_info(schema_id) if schema_id else {}
        connection_info = agent.get_connection_info(connection_id) if connection_id else {}
        
        # Parse offer data for display
        offer = {
            "exchange_id": exchange_id,
            "credential_name": schema_info.get('schema', {}).get('name', 'Credential'),
            "issuer": {
                "name": connection_info.get('their_label', 'Unknown Issuer'),
                "image": ""
            },
            "attributes": attributes,
            "state": cred_ex_record.get('state'),
        }
        
        current_app.logger.info(f"Rendering offer: {offer}")
        
        return render_template("pages/credential-offer.jinja", offer=offer, exchange_id=exchange_id)
    except Exception as e:
        current_app.logger.error(f"Error fetching credential offer: {e}", exc_info=True)
        return redirect(url_for("main.index"))


@bp.route("/offers/<exchange_id>/accept", methods=["POST"])
def accept_credential_offer(exchange_id):
    """Accept a credential offer"""
    agent = AgentController()
    
    # Get wallet and set token
    wallet_id = session.get("wallet_id")
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    wallet = await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))
    agent.set_token(wallet["token"])
    
    try:
        # Send credential request
        response = agent.send_credential_request(exchange_id)
        return jsonify({"status": "success", "message": "Credential request sent"})
    except Exception as e:
        current_app.logger.error(f"Error accepting credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/offers/<exchange_id>/decline", methods=["POST"])
def decline_credential_offer(exchange_id):
    """Decline a credential offer"""
    agent = AgentController()
    
    wallet_id = session.get("wallet_id")
    
    # Get wallet and set token
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    wallet = await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))
    agent.set_token(wallet["token"])
    
    try:
        # Send decline message
        response = agent.send_credential_decline(exchange_id)
        
        # Delete the notification using the new system
        deleted = await_(delete_notification(wallet_id, exchange_id))
        
        if deleted:
            current_app.logger.info(f"✅ Removed notification for declined offer: {exchange_id}")
            
            # Broadcast notification removal for real-time update
            notification_broadcaster.broadcast(
                wallet_id,
                'notification_removed',
                {'exchange_id': exchange_id, 'reason': 'declined'}
            )
        
        return jsonify({"status": "success", "message": "Credential offer declined"})
    except Exception as e:
        current_app.logger.error(f"Error declining credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/presentations/<exchange_id>", methods=["GET"])
def view_presentation_request(exchange_id):
    """View presentation request details page"""
    wallet_id = session.get("wallet_id")
    if not wallet_id:
        return redirect(url_for("main.index"))
    
    try:
        agent = AgentController()
        wallet_askar = AskarStorage.for_wallet(wallet_id)
        
        # Get wallet and set token
        wallet = await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))
        agent.set_token(wallet["token"])
        
        # Get presentation exchange info
        pres_ex = agent.get_presentation_exchange_info(exchange_id)
        current_app.logger.info(f"Presentation exchange: {pres_ex}")
        
        # Get presentation request details
        pres_record = pres_ex.get('pres_ex_record', {})
        by_format = pres_ex.get('by_format', {})
        anoncreds_request = by_format.get('pres_request', {}).get('anoncreds', {})
        
        connection_id = pres_ex.get('connection_id')
        connection_info = agent.get_connection_info(connection_id) if connection_id else {}
        
        # Parse requested attributes and predicates
        requested_attributes = anoncreds_request.get('requested_attributes', {})
        requested_predicates = anoncreds_request.get('requested_predicates', {})
        
        # Get user's credentials to match against request
        user_credentials = await_(wallet_askar.fetch(AskarStorageKeys.CREDENTIALS)) or []
        
        current_app.logger.info(f"=== PRESENTATION REQUEST MATCHING ===")
        current_app.logger.info(f"User has {len(user_credentials)} credentials")
        for i, cred in enumerate(user_credentials):
            current_app.logger.info(f"  Credential {i+1}: {cred.get('name')}")
            current_app.logger.info(f"    Attributes: {list(cred.get('credentialSubject', {}).keys())}")
        
        current_app.logger.info(f"Requested attributes: {list(requested_attributes.keys())}")
        for attr_id, attr_info in requested_attributes.items():
            current_app.logger.info(f"  {attr_id}: names={attr_info.get('names')}, name={attr_info.get('name')}")
        
        # Match credentials to requested attributes
        matched_attributes = []
        for attr_id, attr_info in requested_attributes.items():
            # AnonCreds uses 'names' (list) not 'name' (single string)
            attr_names = attr_info.get('names', [])
            if not attr_names:
                # Fallback to 'name' if 'names' not present
                single_name = attr_info.get('name')
                attr_names = [single_name] if single_name else []
            
            restrictions = attr_info.get('restrictions', [])
            
            current_app.logger.info(f"Looking for attributes: {attr_names}")
            
            # Process each attribute name in the request
            for attr_name in attr_names:
                # Find matching credential
                matching_cred = None
                value = None
                
                for cred in user_credentials:
                    cred_subject = cred.get('credentialSubject', {})
                    current_app.logger.info(f"  Checking credential: {cred.get('name')}, has {list(cred_subject.keys())}")
                    
                    # Check if credential has this attribute
                    if attr_name in cred_subject:
                        # Check restrictions if any
                        if restrictions:
                            # TODO: Implement restriction checking (schema_id, cred_def_id, issuer_id)
                            # For now, just use the first matching credential
                            matching_cred = cred
                            value = cred_subject[attr_name]
                            break
                        else:
                            matching_cred = cred
                            value = cred_subject[attr_name]
                            break
                
                matched_attributes.append({
                    'id': f"{attr_id}_{attr_name}",
                    'name': attr_name,
                    'value': value,
                    'credential_name': matching_cred.get('name') if matching_cred else None,
                    'issuer_name': matching_cred.get('issuer', {}).get('name') if matching_cred else None,
                    'has_match': matching_cred is not None,
                    'restrictions': restrictions
                })
        
        # Match predicates
        matched_predicates = []
        for pred_id, pred_info in requested_predicates.items():
            pred_name = pred_info.get('name')
            p_type = pred_info.get('p_type', '>=')
            p_value = pred_info.get('p_value')
            
            # Find matching credential
            matching_cred = None
            value = None
            meets_condition = False
            
            for cred in user_credentials:
                cred_subject = cred.get('credentialSubject', {})
                
                if pred_name in cred_subject:
                    matching_cred = cred
                    value = cred_subject[pred_name]
                    
                    # Check if predicate is satisfied
                    try:
                        if p_type == '>=':
                            meets_condition = int(value) >= int(p_value)
                        elif p_type == '>':
                            meets_condition = int(value) > int(p_value)
                        elif p_type == '<=':
                            meets_condition = int(value) <= int(p_value)
                        elif p_type == '<':
                            meets_condition = int(value) < int(p_value)
                    except (ValueError, TypeError):
                        meets_condition = False
                    
                    break
            
            matched_predicates.append({
                'id': pred_id,
                'name': pred_name,
                'p_type': p_type,
                'p_value': p_value,
                'actual_value': value,
                'meets_condition': meets_condition,
                'credential_name': matching_cred.get('name') if matching_cred else None,
                'issuer_name': matching_cred.get('issuer', {}).get('name') if matching_cred else None,
                'has_match': matching_cred is not None
            })
        
        # Parse request data
        request_data = {
            "exchange_id": exchange_id,
            "verifier_name": connection_info.get('their_label', 'Unknown Verifier'),
            "request_name": anoncreds_request.get('name', 'Presentation Request'),
            "matched_attributes": matched_attributes,
            "matched_predicates": matched_predicates,
            "can_respond": all(attr['has_match'] for attr in matched_attributes) and all(pred['has_match'] and pred['meets_condition'] for pred in matched_predicates),
            "connection_id": connection_id
        }
        
        return render_template("pages/presentation-request.jinja", **request_data)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching presentation request: {e}", exc_info=True)
        return redirect(url_for("main.index"))


@bp.route("/presentations/<exchange_id>/respond", methods=["POST"])
def respond_to_presentation_request(exchange_id):
    """Respond to a presentation request"""
    agent = AgentController()
    
    # Get wallet and set token
    wallet_id = session.get("wallet_id")
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    wallet = await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))
    agent.set_token(wallet["token"])
    
    try:
        # Get the original presentation request to know which referents are attributes vs predicates
        pres_ex = agent.get_presentation_exchange_info(exchange_id)
        by_format = pres_ex.get('by_format', {})
        anoncreds_request = by_format.get('pres_request', {}).get('anoncreds', {})
        
        # Get the attribute and predicate IDs from the request
        request_attr_ids = set(anoncreds_request.get('requested_attributes', {}).keys())
        request_pred_ids = set(anoncreds_request.get('requested_predicates', {}).keys())
        
        current_app.logger.info(f"Request attribute IDs: {request_attr_ids}")
        current_app.logger.info(f"Request predicate IDs: {request_pred_ids}")
        
        # Get matching credentials from ACA-Py
        matching_creds = agent.get_matching_credentials_for_presentation(exchange_id)
        current_app.logger.info(f"Matching credentials from ACA-Py: {matching_creds}")
        
        # Auto-select first matching credential for each requested attribute/predicate
        # Build the presentation spec in AnonCreds format
        requested_attributes = {}
        requested_predicates = {}
        
        # Process matching credentials returned by ACA-Py
        if matching_creds:
            for match in matching_creds:
                if 'cred_info' in match and 'presentation_referents' in match:
                    cred_id = match['cred_info'].get('referent')
                    
                    # Check if we need timestamp for revocation
                    timestamp = None
                    if match.get('interval', None) is not None:
                        timestamp = match['interval'].get('to')
                    
                    for referent in match['presentation_referents']:
                        # Determine if this referent is an attribute or predicate
                        if referent in request_attr_ids:
                            requested_attributes[referent] = {
                                'cred_id': cred_id,
                                'revealed': True
                            }
                            if timestamp:
                                requested_attributes[referent]['timestamp'] = timestamp
                        elif referent in request_pred_ids:
                            requested_predicates[referent] = {
                                'cred_id': cred_id
                            }
                            if timestamp:
                                requested_predicates[referent]['timestamp'] = timestamp
        
        # Build presentation spec
        presentation_spec = {
            "anoncreds": {
                "requested_attributes": requested_attributes,
                "requested_predicates": requested_predicates,
                "self_attested_attributes": {}
            },
            "trace": False
        }
        
        current_app.logger.info(f"Sending presentation spec: {presentation_spec}")
        
        # Send presentation response
        response = agent.send_presentation_response(exchange_id, presentation_spec)
        
        current_app.logger.info(f"Presentation response: {response}")
        
        return jsonify({"status": "success", "message": "Presentation response sent"})
    except Exception as e:
        current_app.logger.error(f"Error responding to presentation request: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/presentations/<exchange_id>/decline", methods=["POST"])
def decline_presentation_request(exchange_id):
    """Decline a presentation request"""
    agent = AgentController()
    
    wallet_id = session.get("wallet_id")
    
    # Get wallet and set token
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    wallet = await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))
    agent.set_token(wallet["token"])
    
    try:
        # Send decline message (delete the presentation exchange)
        response = agent.delete_presentation_exchange(exchange_id)
        
        # Delete the notification
        deleted = await_(delete_notification(wallet_id, exchange_id))
        
        if deleted:
            # Broadcast notification removal
            notification_broadcaster.broadcast(
                wallet_id,
                'notification_removed',
                {'exchange_id': exchange_id, 'reason': 'declined'}
            )
        
        return jsonify({"status": "success", "message": "Presentation request declined"})
    except Exception as e:
        current_app.logger.error(f"Error declining presentation request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

