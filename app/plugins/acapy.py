from flask import current_app
import httpx
from config import Config
from app.utils import url_encode


class AgentController:
    def __init__(self):
        self.admin_endpoint = Config.AGENT_ADMIN_ENDPOINT
        self.admin_headers = {"X-API-KEY": Config.AGENT_ADMIN_API_KEY}
        self.tenant_headers = {}

    def create_subwallet(self, client_id, wallet_key):
        current_app.logger.info("Creating new Subwallet: {client_id}")
        r = httpx.post(
            f"{self.admin_endpoint}/multitenancy/wallet",
            json={
                "label": f"{Config.APP_NAME} - {client_id}",
                # "image_url": f'{Config.AVATAR_URL}?seed={client_id}',
                "wallet_key": wallet_key,
                "wallet_name": client_id,
                "wallet_type": "askar-anoncreds",
                "key_management_mode": "managed",
            },
            headers=self.admin_headers,
        )
        self.set_token(r.json().get("token"))
        return r.json() | {"wallet_key": wallet_key}

    def request_token(self, wallet_id, wallet_key):
        current_app.logger.warning("Requesting Access Token")
        r = httpx.post(
            f"{self.admin_endpoint}/multitenancy/wallet/{wallet_id}/token",
            json={"wallet_key": wallet_key},
            headers=self.admin_headers,
        )
        self.set_token(r.json().get("token"))
        return r.json()

    def set_token(self, token):
        self.tenant_headers["Authorization"] = f"Bearer {token}"

    def create_key(self):
        current_app.logger.warning("Creating keypair")
        r = httpx.post(
            f"{self.admin_endpoint}/wallet/keys",
            json={"alg": "ed25519"},
            headers=self.tenant_headers,
        )
        return r.json()
        
    def receive_invitation(self, invitation):
        current_app.logger.warning('Receiving invitation.')
        label = invitation.get('label')
        r = httpx.post(
            f'{self.admin_endpoint}/out-of-band/receive-invitation?alias={label}',
            json=invitation,
            headers=self.tenant_headers
        )
        return r.json()
        
    def get_connections(self):
        r = httpx.get(
            f'{self.admin_endpoint}/connections',
            headers=self.tenant_headers
        )
        return r.json()
        
    def get_connection_info(self, connection_id):
        r = httpx.get(
            f'{self.admin_endpoint}/connections/{connection_id}',
            headers=self.tenant_headers
        )
        return r.json()
        
    def get_schema_info(self, schema_id):
        r = httpx.get(
            f'{self.admin_endpoint}/anoncreds/schema/{url_encode(schema_id)}',
            headers=self.tenant_headers
        )
        return r.json()
        
    def get_credentials(self):
        r = httpx.get(
            f'{self.admin_endpoint}/credentials',
            headers=self.tenant_headers
        )
        return r.json()
