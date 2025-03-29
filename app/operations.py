from flask import current_app
from app.plugins import AgentController, AskarStorage
import secrets

agent = AgentController()
askar = AskarStorage()

async def provision_wallet(client_id):
    wallet = agent.create_subwallet(client_id, str(secrets.token_hex(16)))
    multikey = agent.create_key().get('multikey')
    
    await askar.store('wallet', client_id, wallet, {'did': [f'did:key:{multikey}']})
    await askar.store('connections', client_id, [])
    await askar.store('credentials', client_id, [])
    await askar.store('notifications', client_id, [])
    
    current_app.logger.warning(f"Configured Wallet: {client_id}")
    
    return wallet