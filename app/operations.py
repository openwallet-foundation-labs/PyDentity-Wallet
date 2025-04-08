from flask import current_app, session
from app.plugins import AgentController, AskarStorage
from app.models.profile import Profile
import secrets

agent = AgentController()
askar = AskarStorage()


async def provision_wallet(client_id):
    wallet = agent.create_subwallet(client_id, str(secrets.token_hex(16)))
    wallet_id = wallet['wallet_id']
    
    multikey = agent.create_key().get("multikey")
    
    profile = Profile(
        wallet_id=wallet_id,
        did_key=f'did:key:{multikey}'
    )

    await askar.store("profile", client_id, profile, {})
    await askar.store("wallet", wallet_id, wallet, {"did": [f"did:key:{multikey}"]})
    await askar.store("messages", wallet_id, [], {})
    await askar.store("connections", wallet_id, [], {})
    await askar.store("credentials", wallet_id, [], {})
    await askar.store("notifications", wallet_id, [], {})

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")

    return wallet

async def sync_session(client_id):
    current_app.logger.warning(f"Session Sync: {client_id}")
    
    profile = await askar.fetch('profile', client_id)
    
    session['credentials'] = await askar.fetch('credentials', profile['wallet_id'])
    session['connections'] = await askar.fetch('connections', profile['wallet_id'])
    session['notifications'] = await askar.fetch('notifications', profile['wallet_id'])

async def sync_wallet(wallet_id):
    current_app.logger.warning(f"Synchronising Wallet: {wallet_id}")
    
    # Refresh token
    wallet = await askar.fetch('wallet', wallet_id)
    wallet['token'] = agent.request_token(
        wallet['wallet_id'],
        wallet['wallet_key'],
    ).get('token')
    await askar.update('wallet', wallet_id, wallet)
    
    # Update Connections
    connections = []
    connections.extend(agent.get_connections())
    await askar.update('connections', wallet_id, connections)
    
    # Update Credentials
    credentials = []
    credentials.extend(
        template_anoncreds(credential) for credential in agent.get_credentials()
        if credential not in credentials
    )
    await askar.update('credentials', wallet_id, credentials)

async def template_anoncreds(cred_input):
    cred_template = await askar.fetch('template', cred_input.get('cred_def_id'))
    for attribute in cred_input['attrs']:
        cred_template['credentialSubject'][attribute] = cred_input['attrs'][attribute]
        
    return cred_template