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
        except Exception as e:
            current_app.logger.warning(e)
            current_app.logger.warning(response.status_code)
            current_app.logger.warning(response.text)
            return None

    def create_subwallet(self, client_id, wallet_key):
        current_app.logger.info(f"Creating new subwallet for client: {client_id}")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/multitenancy/wallet",
                json={
                    "label": f"{Config.APP_NAME} - {client_id}",
                    # "image_url": f'{Config.AVATAR_URL}?seed={client_id}',
                    "wallet_key": wallet_key,
                    "wallet_name": client_id,
                    "wallet_type": "askar-anoncreds",
                    # "key_management_mode": "managed",
                    "wallet_webhook_urls": [f'{Config.APP_URL}/webhooks#{Config.AGENT_ADMIN_API_KEY}'],
                },
                headers=self.admin_headers,
            )
        )

    def request_token(self, wallet_id, wallet_key):
        current_app.logger.info("Requesting Access Token")
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
        current_app.logger.info("Creating keypair")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/wallet/keys",
                json={"alg": "ed25519"},
                headers=self.tenant_headers,
            )
        )

    def create_did(self):
        current_app.logger.info("Creating DID")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/wallet/did/create",
                json={"method": "key", "options": {"key_type": "ed25519"}},
                headers=self.tenant_headers,
            )
        )

    def store_credential(self, credential):
        current_app.logger.info("Storing Credential")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/vc/credentials/store",
                json={"verifiableCredential": credential},
                headers=self.tenant_headers,
            )
        )

    def fetch_credentials(self):
        current_app.logger.info("Fetching Credential")
        return self._try_return(
            requests.get(
                f"{self.admin_endpoint}/vc/credentials",
                headers=self.tenant_headers,
            )
        )

    def sign_presentation(self, presentation, options):
        current_app.logger.info("Signing Presentation")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/vc/presentations/prove",
                json={"presentation": presentation, "options": options},
                headers=self.tenant_headers,
            )
        )

    def receive_invitation(self, invitation):
        current_app.logger.info("Receiving Invitation")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/out-of-band/receive-invitation?auto_accept=true",
                json=invitation,
                headers=self.tenant_headers,
            )
        )

    def get_credential_exchange_info(self, exchange_id):
        current_app.logger.info("Getting Credential Exchange Info")
        return self._try_return(
            requests.get(
                f"{self.admin_endpoint}/issue-credential-2.0/records/{exchange_id}",
                headers=self.tenant_headers,
            )
        )

    def send_credential_request(self, exchange_id):
        current_app.logger.info("Sending Credential Request")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/issue-credential-2.0/records/{exchange_id}/send-request",
                headers=self.tenant_headers,
            )
        )

    def send_credential_decline(self, exchange_id):
        current_app.logger.info("Declining Credential Offer")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/issue-credential-2.0/records/{exchange_id}/problem-report",
                json={"description": "User declined the credential offer"},
                headers=self.tenant_headers,
            )
        )

    def send_presentation_response(self, exchange_id, presentation_request):
        current_app.logger.info("Sending Presentation Response")
        return self._try_return(
            requests.post(
                f"{self.admin_endpoint}/present-proof-2.0/records/{exchange_id}/send-presentation",
                json=presentation_request,
                headers=self.tenant_headers,
            )
        )

    def get_connection_info(self, connection_id):
        current_app.logger.info("Getting Connection Info")
        return self._try_return(
            requests.get(
                f"{self.admin_endpoint}/connections/{connection_id}",
                headers=self.tenant_headers,
            )
        )

    def get_schema_info(self, schema_id):
        current_app.logger.info("Getting Schema Info")
        return self._try_return(
            requests.get(
                f"{self.admin_endpoint}/schemas/{schema_id}",
                headers=self.tenant_headers,
            )
        )
