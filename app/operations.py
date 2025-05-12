from flask import current_app, session
from app.plugins import AgentController, AskarStorage
from app.models.profile import Profile
import secrets

agent = AgentController()
askar = AskarStorage()


async def provision_wallet(client_id):
    wallet_key = str(secrets.token_hex(16))
    
    wallet = agent.create_subwallet(client_id, wallet_key)
    wallet['wallet_key'] = wallet_key
    agent.set_token(wallet['token'])
    
    did = agent.create_did().get("result").get('did')
    multikey = did.split(':')[-1]
    
    wallet_id = wallet['wallet_id']
    profile = Profile(
        client_id=client_id,
        wallet_id=wallet_id,
        multikey=multikey
    ).model_dump()

    await askar.store("profile", client_id, profile, {})
    await askar.store("wallet", wallet_id, wallet, {"did": [did]})
    await askar.store("messages", wallet_id, [], {})
    await askar.store("connections", wallet_id, [], {})
    await askar.store("credentials", wallet_id, [], {})
    await askar.store("notifications", wallet_id, [], {})

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")
    current_app.logger.warning(profile)
    current_app.logger.warning(wallet)

    return wallet

async def sync_session(wallet_id):
    # current_app.logger.warning(f"Session Sync: {client_id}")
    
    session['credentials'] = await askar.fetch('credentials', wallet_id)
    session['connections'] = await askar.fetch('connections', wallet_id)
    session['notifications'] = await askar.fetch('notifications', wallet_id)

async def sync_wallet(wallet_id):
    current_app.logger.warning(f"Synchronising Wallet: {wallet_id}")
    
    # Refresh token
    await agent.set_agent_auth(wallet_id)
    
    # Update Connections
    connections = []
    connections.extend(agent.get_connections().get('results'))
    await askar.update('connections', wallet_id, connections)
    
    # Update Credentials
    credentials = []
    credentials.extend(
        template_anoncreds(credential) for credential in agent.get_credentials().get('results')
        if credential not in credentials
    )
    credentials.extend(
        credential.get('cred_value') for credential in agent.get_w3c_credentials().get('results')
        if credential not in credentials
    )
    await askar.update('credentials', wallet_id, credentials)

async def template_anoncreds(cred_input):
    credential = await askar.fetch('template', cred_input.get('cred_def_id'))
    for attribute in cred_input['attrs']:
        credential['credentialSubject'][attribute] = cred_input['attrs'][attribute]
        
    return credential