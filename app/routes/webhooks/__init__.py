from flask import Blueprint, abort,  render_template, url_for, current_app, session, redirect, jsonify, request
import asyncio
from asyncio import run as await_
from app.plugins import AskarStorage, AgentController
# from app.operations import beautify_anoncreds
from .manager import WebhookManager
from .models import Message, CredentialOffer, PresentationRequest, Notification
from config import Config

bp = Blueprint("webhooks", __name__)

askar = AskarStorage()


@bp.before_request
def before_request_callback():
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return {"message": "Unauthorized"}, 401
    elif api_key != Config.AGENT_ADMIN_API_KEY:
        return {"message": "Unauthorized"}, 401
    
@bp.route("/topic/connections/", methods=["POST"])
def topic_connections():
    wallet_id = request.headers.get('X-WALLET-ID')
    connection = request.json
    current_app.logger.info('Connection state: ' + connection.get('state'))
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
            title=f'New connection with {connection_name}',
            details=connection
        ).model_dump()
        await_(askar.append('notifications', wallet_id, notification))
    else:
        pass
    return {}, 200
    
@bp.route("/topic/out_of_band/", methods=["POST"])
def topic_out_of_band():
    out_of_band = request.json
    current_app.logger.info('Out of band state: ' + out_of_band.get('state'))
    if out_of_band.get('state') == 'initial':
        pass
    elif out_of_band.get('state') == 'done':
        pass
    elif out_of_band.get('state') == 'deleted':
        pass
    else:
        pass
    return {}, 200
    
@bp.route("/topic/basicmessages/", methods=["POST"])
def topic_basicmessages():
    wallet_id = request.headers.get('X-WALLET-ID')
    message = request.json
    if message.get('state') == 'received':
        entry = Message(
            content=message.get('content'),
            timestamp=message.get('sent_time'),
            inbound=True
        ).model_dump()
        await_(askar.append('messages', message.get('connection_id'), entry))
        
        wallet = await_(askar.fetch('wallet', wallet_id))
        
        agent = AgentController()
        agent.set_token(wallet['token'])
        
        connection = agent.get_connection_info(message.get('connection_id'))
        sender_name = connection.get('their_label')
        notification = Notification(
            type='connection',
            title=f'New message from {sender_name}',
            details=entry
        ).model_dump()
        await_(askar.append('notifications', wallet_id, notification))
    else:
        current_app.logger.warning(message.get('state'))
    return {}, 200
    

@bp.route("/topic/issue_credential/", methods=["POST"])
def webhook_issue_credential():
    wallet_id = request.headers.get('X-WALLET-ID')
    cred_ex = request.json
    current_app.logger.warning(cred_ex.get('state'))
    if cred_ex.get('state') == 'offer-received':
        pass
    

@bp.route("/topic/present_proof/", methods=["POST"])
def webhook_present_proof():
    wallet_id = request.headers.get('X-WALLET-ID')
    pres_ex = request.json
    current_app.logger.warning(pres_ex.get('state'))
    if pres_ex.get('state') == 'offer-received':
        pass
    

@bp.route("/topic/issue_credential_v2_0/", methods=["POST"])
def webhook_issue_credential_v2_0():
    wallet_id = request.headers.get('X-WALLET-ID')
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
        

        schema_id = cred_ex.get('by_format').get('cred_offer').get('anoncreds').get('schema_id')
        cred_def_id = cred_ex.get('by_format').get('cred_offer').get('anoncreds').get('cred_def_id')
        
        wallet = await_(askar.fetch('wallet', wallet_id))
        
        agent = AgentController()
        agent.set_token(wallet['token'])
        connection = agent.get_connection_info(cred_ex.get('connection_id'))
        schema = agent.get_schema_info(schema_id).get('schema')
        issuer_name = connection.get('their_label')
        cred_name = schema.get('name')
        cred_meta = {
            'issuer_name': issuer_name,
            'issuer_image': '',
            'cred_name': schema.get('name'),
            'cred_version': schema.get('version'),
        }
        await_(askar.store('cred_meta', cred_def_id, cred_meta))
        
        notification = Notification(
            type='cred_offer',
            title=f'{issuer_name} is offering {cred_name}',
            details=cred_offer
        ).model_dump()
        await_(askar.append('notifications', wallet_id, notification))
        
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
        credential = await_(beautify_anoncreds(cred_input))
        current_app.logger.warning(credential)
        await_(askar.append('credentials', wallet_id, credential))
    else:
        current_app.logger.warning(cred_ex.get('state'))
    return {}, 200
    

@bp.route("/topic/issue_credential_v2_0_anoncreds/", methods=["POST"])
def webhook_issue_credential_v2_0_anoncreds():
    return {}, 200
    

@bp.route("/topic/present_proof_v2_0/", methods=["POST"])
def webhook_present_proof_v2_0():
    pres_ex = request.json
    wallet_id = request.headers.get('X-WALLET-ID')
    if pres_ex.get('state') == 'request-received':
        pres_req = PresentationRequest(
            timestamp = pres_ex.get('created_at'),
            exchange_id = pres_ex.get('pres_ex_id'),
            connection_id = pres_ex.get('connection_id'),
            attributes = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('requested_attributes'),
            predicates = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('requested_predicates')
        ).model_dump()
        await_(askar.append('pres_ex', pres_ex.get('connection_id'), pres_req))
        
        
        wallet = await_(askar.fetch('wallet', wallet_id))
        
        agent = AgentController()
        agent.set_token(wallet['token'])
        connection = agent.get_connection_info(pres_ex.get('connection_id'))
    
        verifier_name = connection.get('their_label')
        pres_name = pres_ex.get('by_format').get('pres_request').get('anoncreds').get('name')
        notification = Notification(
            type='pres_request',
            title=f'{verifier_name} is requesting {pres_name}',
            details=pres_req
        ).model_dump()
        await_(askar.append('notifications', wallet_id, notification))
    elif pres_ex.get('state') == 'presentation-sent':
        pass
    elif pres_ex.get('state') == 'done':
        pass
    return {}, 200
    

# @bp.route("/topic/topic/", methods=["POST"])
# def webhook_topic_template():
#     current_app.logger.warning(request.json)
#     return {}, 200

@bp.route("/topic/<topic>/", methods=["POST"])
def webhook_topic(topic: str):
    return await_(
        WebhookManager(
            request.headers.get('X-WALLET-ID')
        ).handle_topic(topic, request.json)
    )