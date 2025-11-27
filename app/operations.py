from flask import current_app, session
from app.plugins import AgentController, AskarStorage, AskarStorageKeys
from app.models.profile import Profile
import secrets

agent = AgentController()


async def sign_in_agent(wallet_id):
        askar = AskarStorage.for_wallet(wallet_id)
        
        if not (wallet := await askar.fetch(AskarStorageKeys.WALLETS)):
            return None
        
        agent.set_token(wallet["token"])
        return agent
        
        


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

    # Create profiles first (if they don't exist)
    global_askar = AskarStorage.global_store()
    await global_askar.create_profile()  # Create 'global' profile
    
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    await wallet_askar.create_profile()  # Create wallet-specific profile
    
    # Store global data (client_id -> wallet_id mapping)
    await global_askar.store(AskarStorageKeys.PROFILES, client_id, profile, {})
    
    # Initialize wallet-specific data in wallet's profile
    await wallet_askar.store(AskarStorageKeys.WALLETS, "data", wallet, {"did": [wallet["holder_id"]]})
    await wallet_askar.store(AskarStorageKeys.MESSAGES, "data", [], {})
    await wallet_askar.store(AskarStorageKeys.CONNECTIONS, "data", [], {})
    await wallet_askar.store(AskarStorageKeys.CREDENTIALS, "data", [], {})
    await wallet_askar.store(AskarStorageKeys.CRED_OFFERS, "data", [], {})
    await wallet_askar.store(AskarStorageKeys.PRES_REQUESTS, "data", [], {})
    # Notifications are stored individually - no array initialization needed
    
    current_app.logger.info(f"✅ Created Askar profile for wallet: {wallet_id}")

    current_app.logger.warning(f"Configured Wallet: {wallet_id}")
    current_app.logger.warning(f"Bearer {wallet['token']}")

    return wallet


async def sync_wallet(client_id):
    # Refresh token
    global_askar = AskarStorage.global_store()
    profile = await global_askar.fetch(AskarStorageKeys.PROFILES, client_id)
    
    wallet_id = profile.get("wallet_id")
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    wallet = await wallet_askar.fetch(AskarStorageKeys.WALLETS)
    
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
    await wallet_askar.update(AskarStorageKeys.CREDENTIALS, "data", credentials)


async def sync_session(client_id):
    from app.utils import get_notifications
    
    global_askar = AskarStorage.global_store()
    profile = await global_askar.fetch(AskarStorageKeys.PROFILES, client_id)
    if not profile:
        current_app.logger.error(f"No profile found for client_id: {client_id}")
        raise ValueError(f"Profile not found for client_id: {client_id}")
    
    wallet_id = profile.get("wallet_id")
    
    current_app.logger.info(f"=== SYNCING SESSION for wallet: {wallet_id} ===")
    
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    credentials = await wallet_askar.fetch(AskarStorageKeys.CREDENTIALS) or []
    connections = await wallet_askar.fetch(AskarStorageKeys.CONNECTIONS) or []
    notifications = await get_notifications(wallet_id) or []  # Use new notification system
    
    current_app.logger.info(f"Fetched from storage: {len(credentials)} credentials, {len(connections)} connections, {len(notifications)} notifications")
    
    if notifications:
        for i, n in enumerate(notifications):
            current_app.logger.info(f"  Notification {i}: type={n.get('type')}, id={n.get('id')}")
    
    session["credentials"] = credentials
    session["connections"] = connections
    session["notifications"] = notifications
    
    current_app.logger.info(f"✅ Session synced")
