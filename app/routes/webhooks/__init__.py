from flask import Blueprint, current_app, request, session
from asyncio import run as await_
from app.plugins import AskarStorage, AgentController, AnonCredsProcessor
from app.operations import template_anoncreds
from app.models.webhooks import Message, CredentialOffer, PresentationRequest, Notification
from config import Config

bp = Blueprint("webhooks", __name__)
askar = AskarStorage()
agent = AgentController()


@bp.before_request
def before_request_callback():
    api_key = request.headers.get('X-API-KEY')
    wallet_id = request.headers.get('X-WALLET-ID')
    
    if not api_key or not wallet_id:
        return {"message": "Unauthorized"}, 401
    
    elif api_key != Config.AGENT_ADMIN_API_KEY:
        return {"message": "Unauthorized"}, 401
    
    session['wallet_id'] = wallet_id
    
@bp.route("/topic/connections/", methods=["POST"])
def topic_connections():
    print('Webhook Connection')
    current_app.logger.warning('Webhook Connection')
    connection = request.json
    current_app.logger.warning(connection)
    if connection.get('state') == 'invitation':
        pass
    elif connection.get('state') == 'request':
        pass
    elif connection.get('state') == 'response':
        pass
    elif connection.get('state') == 'active':
        connection_name = connection.get('their_label')
        notification = Notification(
            type='connection',
            title=f'Connected with {connection_name}',
            details=connection
        ).model_dump()
        await_(askar.append('connections', session['wallet_id'], connection))
        await_(askar.append('notifications', session['wallet_id'], notification))
    else:
        current_app.logger.warning(connection.get('state'))
    return {}, 200
    
@bp.route("/topic/out_of_band/", methods=["POST"])
def topic_out_of_band():
    current_app.logger.warning('Webhook Out-of-Band')
    out_of_band = request.json
    current_app.logger.warning(out_of_band)
    if out_of_band.get('state') == 'initial':
        pass
    elif out_of_band.get('state') == 'done':
        pass
    elif out_of_band.get('state') == 'deleted':
        pass
    else:
        current_app.logger.warning(out_of_band.get('state'))
    return {}, 200

@bp.route("/topic/issue_credential/", methods=["POST"])
def webhook_issue_credential():
    current_app.logger.warning('Webhook Issue Credential')
    
    cred_ex = request.json
    anoncreds = AnonCredsProcessor(session['wallet_id'])
    current_app.logger.warning(cred_ex.get('state'))
    if cred_ex.get('state') == 'offer_received':
        await_(agent.set_agent_auth(session['wallet_id']))
        connection = agent.get_connection_info(cred_ex.get('connection_id'))
        schema_id = cred_ex.get('schema_id')
        cred_def_id = cred_ex.get('credential_definition_id')
        cred_template = {
            '@context': [
                'https://www.w3.org/ns/credentials/v2',
                {'@vocab': 'https://www.w3.org/ns/credentials/undefined-term#'}
            ],
            'type': ['VerifiableCredential'],
            'name': schema_id.split(':')[2].replace('_', ' ').title(),
            'issuer': {
                'id': cred_def_id.split('/')[0],
                'name': connection.get('their_label'),
                'image': connection.get('image'),
            },
            'credentialSubject': {}
        }
        await_(askar.store('template', cred_def_id, cred_template))
        current_app.logger.warning(cred_template)
    elif cred_ex.get('state') == 'request_sent':
        pass
    elif cred_ex.get('state') == 'credential_received':
        pass
    elif cred_ex.get('state') == 'credential_acked':
        cred_def_id = cred_ex.get('credential_definition_id')
        cred_template = await_(askar.fetch('template', cred_def_id))
        attributes = cred_ex.get('credential_offer_dict').get('credential_preview').get('attributes')
        for attribute in attributes:
            cred_template['credentialSubject'][attribute.get('name')] = attribute.get('value')
        await_(askar.append('credentials', session['wallet_id'], cred_template))
    return {}, 200
    

@bp.route("/topic/present_proof/", methods=["POST"])
def webhook_present_proof():
    current_app.logger.warning('Webhook Present Proof')
    pres_ex = request.json
    current_app.logger.warning(pres_ex.get('state'))
    if pres_ex.get('state') == 'offer-received':
        pass
    

@bp.route("/topic/issue_credential_v2_0/", methods=["POST"])
def webhook_issue_credential_v2_0():
    current_app.logger.warning('Webhook Issue Credential')
    cred_ex = request.json
    if cred_ex.get('state') == 'offer-received':
        preview = {}
        for attribute in cred_ex.get('cred_offer').get('credential_preview').get('attributes'):
            preview[attribute.get('name')] = attribute.get('value')
            
        cred_offer = CredentialOffer(
            timestamp=cred_ex.get('created_at'),
            exchange_id=cred_ex.get('cred_ex_id'),
            connection_id=cred_ex.get('connection_id'),
            comment=cred_ex.get('cred_offer').get('comment'),
            preview=preview,
        ).model_dump()
        
        await_(askar.append('cred_ex', cred_ex.get('connection_id'), cred_offer))
        
        wallet = await_(askar.fetch('wallet', session['wallet_id']))
        
        agent.set_token(wallet['token'])
        connection = agent.get_connection_info(cred_ex.get('connection_id'))
        

        schema_id = cred_ex.get('by_format').get('cred_offer').get('anoncreds').get('schema_id')
        cred_def_id = cred_ex.get('by_format').get('cred_offer').get('anoncreds').get('cred_def_id')
        
        schema = agent.get_schema_info(schema_id).get('schema')
        
        cred_name = schema.get('name')
        issuer_id = cred_def_id.split('/')[0]
        issuer_name = connection.get('their_label')
        
        cred_template = {
            '@context': [
                'https://www.w3.org/ns/credentials/v2'
            ],
            'type': ['VerifiableCredential'],
            'name': cred_name,
            'issuer': {
                'id': issuer_id,
                'name': issuer_name,
                'image': connection.get('image'),
            },
            'credentialSubject': {}
        }
        await_(askar.store('template', cred_def_id, cred_template))
        
        notification = Notification(
            type='cred_offer',
            title=f'{issuer_name} is offering {cred_name}',
            details=cred_offer
        ).model_dump()
        await_(askar.append('notifications', session['wallet_id'], notification))
        
    elif cred_ex.get('state') == 'request-sent':
        pass
    
    elif cred_ex.get('state') == 'credential-received':
        pass
    
    elif cred_ex.get('state') == 'done':
        attributes = cred_ex.get('cred_offer').get('credential_preview').get('attributes')
        cred_input = {
            'cred_def_id': cred_ex.get('by_format').get('cred_offer').get('anoncreds').get('cred_def_id'),
            'attrs': {}
        }
        for attribute in attributes:
            cred_input[attribute['name']] = attribute['value']
            
        credential = await_(template_anoncreds(cred_input))
        await_(askar.append('credentials', session['wallet_id'], credential))
    else:
        current_app.logger.warning(cred_ex.get('state'))
    return {}, 200
    

@bp.route("/topic/issue_credential_v2_0_anoncreds/", methods=["POST"])
def webhook_issue_credential_v2_0_anoncreds():
    current_app.logger.warning('Webhook Issue Credential')
    return {}, 200
    

@bp.route("/topic/present_proof_v2_0/", methods=["POST"])
def webhook_present_proof_v2_0():
    current_app.logger.warning('Webhook Present Proof')
    pres_ex = request.json
    if pres_ex.get('state') == 'request-received':
        pres_req = PresentationRequest(
            timestamp = pres_ex.get('created_at'),
            exchange_id = pres_ex.get('pres_ex_id'),
            connection_id = pres_ex.get('connection_id'),
            attributes = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('requested_attributes'),
            predicates = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('requested_predicates')
        ).model_dump()
        await_(askar.append('pres_ex', pres_ex.get('connection_id'), pres_req))
        
        
        wallet = await_(askar.fetch('wallet', session['wallet_id']))
        
        agent.set_token(wallet['token'])
        connection = agent.get_connection_info(pres_ex.get('connection_id'))
    
        verifier_name = connection.get('their_label')
        pres_name = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('name')
        notification = Notification(
            type='pres_request',
            title=f'{verifier_name} is requesting {pres_name}',
            details=pres_req
        ).model_dump()
        await_(askar.append('notifications', session['wallet_id'], notification))
        
    elif pres_ex.get('state') == 'presentation-sent':
        pass
    
    elif pres_ex.get('state') == 'done':
        pass
    
    return {}, 200
    