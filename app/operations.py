from flask import current_app
from app.plugins import AgentController, AskarStorage
from app.models.profile import Profile
import secrets

agent = AgentController()
askar = AskarStorage()

async def provision_wallet(client_id):
    wallet_key = str(secrets.token_hex(16))
    wallet = agent.create_subwallet(client_id, wallet_key) | {
        'wallet_key': wallet_key
    }
    agent.set_token(wallet["token"])

    multikey = agent.create_key().get("multikey")

    wallet_id = wallet["wallet_id"]
    profile = Profile(
        client_id=client_id, wallet_id=wallet_id, multikey=multikey
    ).model_dump()

    await askar.store("profile", client_id, profile, {})
    await askar.store("wallet", wallet_id, wallet, {"did": [f'did:key:{multikey}']})
    await askar.store("messages", wallet_id, [], {})
    await askar.store("connections", wallet_id, [], {})
    await askar.store("credentials", wallet_id, [], {})
    await askar.store("notifications", wallet_id, [], {})

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")

    return wallet