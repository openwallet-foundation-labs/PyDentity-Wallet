from flask import current_app
import requests
from config import Config


class AgentController:
    def __init__(self):
        self.admin_endpoint = Config.AGENT_ADMIN_ENDPOINT
        self.admin_headers = {"X-API-KEY": Config.AGENT_ADMIN_API_KEY}
        self.tenant_headers = {}

    def _try_return(self, response):
        try:
            return response.json()
        except:
            current_app.logger.warning(response.status_code)
            current_app.logger.warning(response.text)
            return None

    def create_subwallet(self, client_id, wallet_key):
        current_app.logger.info(f"Creating new Subwallet: {client_id}")
        return self._try_return(
            requests.post(
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
        )

    def request_token(self, wallet_id, wallet_key):
        current_app.logger.warning("Requesting Access Token")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/multitenancy/wallet/{wallet_id}/token",
                json={"wallet_key": wallet_key},
                headers=self.admin_headers,
            )
        )

    def set_token(self, token):
        self.tenant_headers["Authorization"] = f"Bearer {token}"

    def create_key(self):
        current_app.logger.warning("Creating keypair")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/wallet/keys",
                json={"alg": "ed25519"},
                headers=self.tenant_headers,
            )
        )

    def create_did(self):
        current_app.logger.warning("Creating DID")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/wallet/did/create",
                json={
                    "method": "key",
                    'options': {
                        'key_type': 'ed25519'
                    }
                },
                headers=self.tenant_headers,
            )
        )

    def store_credential(self, credential):
        current_app.logger.warning("Storing Credential")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/vc/credentials/store",
                json={
                    "verifiableCredential": credential
                },
                headers=self.tenant_headers,
            )
        )

    def fetch_credentials(self):
        current_app.logger.warning("Fetching Credential")
        return self._try_return(
            requests.get(
                f"{self.admin_endpoint}/vc/credentials",
                headers=self.tenant_headers,
            )
        )

    def sign_presentation(self, presentation, options):
        current_app.logger.warning("Signing Presentation")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/vc/presentations/prove",
                json={
                    "presentation": presentation,
                    "options": options
                },
                headers=self.tenant_headers,
            )
        )
