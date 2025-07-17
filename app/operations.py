from flask import current_app, session
from app.plugins import AgentController, AskarStorage
from app.models.profile import Profile
import secrets

agent = AgentController()
askar = AskarStorage()


async def provision_wallet(client_id):
    wallet_key = str(secrets.token_hex(16))
    wallet = agent.create_subwallet(client_id, wallet_key) | {"wallet_key": wallet_key}
    agent.set_token(wallet["token"])

    did = agent.create_did().get("result").get('did')
    multikey = did.split(':')[-1]
    # multikey = agent.create_key().get("multikey")

    wallet_id = wallet["wallet_id"]
    profile = Profile(
        client_id=client_id, wallet_id=wallet_id, multikey=multikey
    ).model_dump()

    await askar.store("profile", client_id, profile, {})
    await askar.store("wallet", wallet_id, wallet, {"did": [f"did:key:{multikey}"]})
    await askar.store("messages", wallet_id, [], {})
    await askar.store("connections", wallet_id, [], {})
    await askar.store("credentials", wallet_id, [], {})
    await askar.store("notifications", wallet_id, [], {})

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")

    return wallet


async def sync_wallet(client_id):
    # Refresh token
    profile = await askar.fetch('profile', client_id)
    wallet = await askar.fetch('wallet', profile.get('wallet_id'))
    wallet['token'] = agent.request_token(
        wallet.get('wallet_id'), 
        wallet.get('wallet_key')
    )
    agent.set_token(wallet['token'])

    # Update Credentials
    credentials = []
    credentials.extend(
        credential.get("cred_value")
        for credential in agent.fetch_credentials().get("results")
        if credential not in credentials
    )
    await askar.update("credentials", wallet.get('wallet_id'), credentials)


async def sync_session(client_id):
    profile = await askar.fetch('profile', client_id)
    wallet_id = profile.get('wallet_id')
    session["credentials"] = await askar.fetch("credentials", wallet_id)
    session["connections"] = await askar.fetch("connections", wallet_id)
    session["notifications"] = await askar.fetch("notifications", wallet_id)
