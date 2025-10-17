from flask import current_app, session
from app.plugins import AgentController, AskarStorage, AskarStorageKeys
from app.models.profile import Profile
import secrets

agent = AgentController()
askar = AskarStorage()


async def provision_wallet(client_id):
    wallet_key = str(secrets.token_hex(16))
    wallet = agent.create_subwallet(client_id, wallet_key) | {"wallet_key": wallet_key}
    agent.set_token(wallet["token"])

    wallet["holder_id"] = agent.create_did().get("result").get("did")
    # multikey = agent.create_key().get("multikey")

    wallet_id = wallet["wallet_id"]
    profile = Profile(
        client_id=client_id,
        wallet_id=wallet_id,
        multikey=wallet["holder_id"].split(":")[-1],
    ).model_dump()

    await askar.store(AskarStorageKeys.PROFILES, client_id, profile, {})
    await askar.store(AskarStorageKeys.WALLETS, wallet_id, wallet, {"did": [wallet["holder_id"]]})
    await askar.store(AskarStorageKeys.MESSAGES, wallet_id, [], {})
    await askar.store(AskarStorageKeys.CONNECTIONS, wallet_id, [], {})
    await askar.store(AskarStorageKeys.CREDENTIALS, wallet_id, [], {})
    await askar.store(AskarStorageKeys.NOTIFICATIONS, wallet_id, [], {})

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")
    current_app.logger.warning(f"Bearer {wallet['token']}")

    return wallet


async def sync_wallet(client_id):
    # Refresh token
    profile = await askar.fetch(AskarStorageKeys.PROFILES, client_id)
    wallet = await askar.fetch(AskarStorageKeys.WALLETS, profile.get("wallet_id"))
    wallet["token"] = agent.request_token(
        wallet.get("wallet_id"), wallet.get("wallet_key")
    )
    agent.set_token(wallet["token"])

    # Update Credentials
    credentials = []
    credentials.extend(
        credential.get("cred_value")
        for credential in agent.fetch_credentials().get("results")
        if credential not in credentials
    )
    await askar.update(AskarStorageKeys.CREDENTIALS, wallet.get("wallet_id"), credentials)


async def sync_session(client_id):
    profile = await askar.fetch(AskarStorageKeys.PROFILES, client_id)
    wallet_id = profile.get("wallet_id")
    session["credentials"] = await askar.fetch(AskarStorageKeys.CREDENTIALS, wallet_id)
    session["connections"] = await askar.fetch(AskarStorageKeys.CONNECTIONS, wallet_id)
    session["notifications"] = await askar.fetch(AskarStorageKeys.NOTIFICATIONS, wallet_id)
