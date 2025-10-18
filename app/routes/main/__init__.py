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
from app.plugins import QRScanner
from app.operations import sync_session, sign_in_agent
from asyncio import run as await_

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if not session.get("client_id"):
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    await_(sync_session(session.get("client_id")))
    return render_template("pages/index.jinja")


@bp.route("/scanner", methods=["POST"])
def scan_qr_code():
    current_app.logger.warning("QR Scanner")
    result = await_(
        QRScanner(session["wallet_id"]).handle_payload(request.form["payload"])
    )
    
    # Return success with message about what was processed
    return jsonify({
        "status": "success", 
        "message": "QR code processed successfully",
        "result": result
    })


@bp.route("/connection-status", methods=["GET"])
def get_connection_status():
    """Get the current connection state"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    current_app.logger.info("=== Connection Status Check ===")
    
    try:
        # Get wallet_id from session
        wallet_id = session.get("wallet_id")
        current_app.logger.info(f"Wallet ID from session: {wallet_id}")
        
        if not wallet_id:
            current_app.logger.warning("No wallet_id in session")
            return jsonify({"state": "no_wallet", "connected": False})
        
        # Get the latest connection ID from session or most recent connection
        connections = session.get('connections', [])
        current_app.logger.info(f"Found {len(connections)} connections in session")
        
        if not connections:
            current_app.logger.warning("No connections found in session")
            return jsonify({"state": "no_connection", "connected": False})
        
        # Get the most recent connection
        latest_connection = connections[-1] if connections else {}
        current_app.logger.info(latest_connection)
        # connection_id = latest_connection.get('connection_id')
        # current_app.logger.info(f"Latest connection ID: {connection_id}")
        
        # if not connection_id:
        #     current_app.logger.warning("No connection_id in latest connection")
        #     return jsonify({"state": "no_connection", "connected": False})
        
        # # Sign in to agent
        # current_app.logger.info(f"Signing in to agent with wallet_id: {wallet_id}")
        # agent = await_(sign_in_agent(wallet_id))
        
        # if not agent:
        #     current_app.logger.error("Failed to sign in to agent")
        #     return jsonify({"state": "wallet_not_found", "connected": False})
        
        # # Get connection info from agent
        # current_app.logger.info(f"Fetching connection info for: {connection_id}")
        # connection_info = agent.get_connection_info(connection_id)
        
        state = latest_connection.get('state', 'unknown')
        their_label = latest_connection.get('their_label', 'Unknown')
        
        current_app.logger.info(f"Connection state: {state}, Their label: {their_label}")
        
        return jsonify({
            "state": state,
            "their_label": their_label
        })
    except Exception as e:
        current_app.logger.error(f"Error getting connection status: {e}", exc_info=True)
        return jsonify({"state": "error", "connected": False, "error": str(e)})


@bp.route("/credential-offers", methods=["GET"])
def get_credential_offers():
    """Get pending credential offers for the user"""
    from app.plugins import AskarStorage
    askar = AskarStorage()
    
    offers = await_(askar.fetch("cred_ex", session.get("client_id")))
    return jsonify({"offers": offers or []})


@bp.route("/credential-offer/<exchange_id>", methods=["GET"])
def credential_offer(exchange_id):
    """View credential offer details"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    current_app.logger.info(f"=== Viewing Credential Offer: {exchange_id} ===")
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet_id = session.get("wallet_id")
    current_app.logger.info(f"Wallet ID: {wallet_id}")
    
    wallet = await_(askar.fetch("wallet", wallet_id))
    if not wallet:
        current_app.logger.error("Wallet not found")
        return redirect(url_for("main.index"))
    
    agent.set_token(wallet["token"])
    
    try:
        # Fetch credential offer details from agent
        current_app.logger.info(f"Fetching credential exchange info for: {exchange_id}")
        offer_details = agent.get_credential_exchange(exchange_id)
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


@bp.route("/credential-offers/<exchange_id>/accept", methods=["POST"])
def accept_credential_offer(exchange_id):
    """Accept a credential offer"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Send credential request
        response = agent.send_credential_request(exchange_id)
        return jsonify({"status": "success", "message": "Credential request sent"})
    except Exception as e:
        current_app.logger.error(f"Error accepting credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/credential-offers/<exchange_id>/decline", methods=["POST"])
def decline_credential_offer(exchange_id):
    """Decline a credential offer"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Send decline message
        response = agent.send_credential_decline(exchange_id)
        return jsonify({"status": "success", "message": "Credential offer declined"})
    except Exception as e:
        current_app.logger.error(f"Error declining credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/presentation-requests/<exchange_id>/respond", methods=["POST"])
def respond_to_presentation_request(exchange_id):
    """Respond to a presentation request"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Get presentation request details
        pres_request = request.json
        # Send presentation response
        response = agent.send_presentation_response(exchange_id, pres_request)
        return jsonify({"status": "success", "message": "Presentation response sent"})
    except Exception as e:
        current_app.logger.error(f"Error responding to presentation request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
