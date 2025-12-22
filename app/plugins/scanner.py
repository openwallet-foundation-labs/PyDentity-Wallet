import requests
from flask import current_app
from app.plugins.vcapi import VcApiExchanger
from app.plugins.acapy import AgentController
from app.plugins.askar import AskarStorage, AskarStorageKeys
import json
import base64

from urllib.parse import urlparse

agent = AgentController()

class QRScanner:
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id
        self.askar = AskarStorage.for_wallet(wallet_id)

    async def handle_payload(self, payload):
        current_app.logger.info("Parsing payload")
        uri = urlparse(payload)
        current_app.logger.info(uri)
        
        if uri.scheme == "https":
            if uri.query.startswith("iuv=1"):
                current_app.logger.info("Interaction URL Version 1")
                # Handle Interaction URL Version 1
                result = await self.iuv_handler(payload)
                return {"type": "iuv", "result": result}
                
            elif uri.query.startswith("oob"):
                current_app.logger.info("Out of band invitation")
                invitation = payload.split('?oob=')[-1]
                decoded_invitation = json.loads(base64.urlsafe_b64decode(invitation+'===').decode())
                # BUG #21: connectionless present-proof request inside OOB (redirect form)
                pres_request = self._get_connectionless_presentation_request(decoded_invitation)
                await self.didcomm_handler(decoded_invitation)
                if pres_request:
                    exchange_id = self._find_presentation_exchange_id(pres_request.get("@id"))
                    return {
                        "type": "oob_presentation_request",
                        "action": "presentation_request",
                        "exchange_id": exchange_id,
                    }
                return {"type": "oob_invitation", "label": decoded_invitation.get("label", "Unknown")}
                
            elif payload.split('?')[-1].startswith('_oobid='):
                try:
                    r = requests.get(payload)
                    invitation = r.json()
                    # BUG #21: connectionless present-proof request inside OOB (redirect form)
                    pres_request = self._get_connectionless_presentation_request(invitation)
                    await self.didcomm_handler(invitation)
                    if pres_request:
                        exchange_id = self._find_presentation_exchange_id(pres_request.get("@id"))
                        return {
                            "type": "oob_presentation_request",
                            "action": "presentation_request",
                            "exchange_id": exchange_id,
                        }
                except Exception:
                    try:
                        current_app.logger.info(r.text)
                    except Exception:
                        current_app.logger.info("Failed to fetch/parse _oobid invitation")
        
        current_app.logger.info("No matching URL scheme found")
        return {"type": "unknown", "message": "No matching URL scheme found"}
    
    async def didcomm_handler(self, invitation):
        # BUG: marshmallow.exceptions.ValidationError: {'_schema': ['Model cannot have goal_code without goal']}
        if invitation.get('goal_code') and not invitation.get('goal'):
            invitation.pop('goal_code')
            
        current_app.logger.info(invitation)
        if invitation.get('@type') and invitation.get('@type').startswith('https://didcomm.org/out-of-band/1.'):
            if (wallet := await self.askar.fetch(AskarStorageKeys.WALLETS)):
                agent.set_token(wallet['token'])
                agent.receive_invitation(invitation)

    async def iuv_handler(self, payload):
        current_app.logger.info("Interactions URL")
        r = requests.get(payload, headers={"Accept": "application/json"})
        protocols = r.json().get("protocols")
        if protocols.get("vcapi", None):
            current_app.logger.info("VC API Exchange")
            
            vcapi = VcApiExchanger(self.wallet_id, protocols.get("vcapi"))
            
            exchange = vcapi.initiate_exchange()
            
            if exchange.get("verifiablePresentation", None):
                current_app.logger.info("Verifiable Presentation")
                await vcapi.store_credential(exchange.get("verifiablePresentation"))

            elif exchange.get("verifiablePresentationRequest", None):
                current_app.logger.info("Verifiable Presentation Request")
                await vcapi.present_credential(
                    exchange.get("verifiablePresentationRequest")
                )

            elif exchange.get("redirectUrl", None):
                redirect_url = exchange.get("redirectUrl")
                redirect_url


    # BUG #21: connectionless present-proof request inside OOB (redirect form)
    def _get_connectionless_presentation_request(self, invitation):
        """
        Identify connectionless present-proof OOB invites:
        - handshake_protocols is [] or missing
        - requests~attach contains a present-proof/2.0 message
        """
        handshake_protocols = invitation.get("handshake_protocols")
        if handshake_protocols not in (None, []):
            return None

        for attachment in invitation.get("requests~attach", []):
            message = attachment.get("data", {}).get("json", {})
            msg_type = message.get("@type", "")
            if msg_type.startswith("https://didcomm.org/present-proof/2.0/"):
                return message

        return None

    # BUG #21: connectionless present-proof request inside OOB (redirect form)
    def _find_presentation_exchange_id(self, thread_id):
        """
        Best-effort: after ACA-Py receives the invitation, poll present-proof records
        to find pres_ex_id by thread_id.
        """
        if not thread_id:
            return None

        for _ in range(3):
            try:
                response = requests.get(
                    f"{agent.admin_endpoint}/present-proof-2.0/records",
                    params={"thread_id": thread_id},
                    headers=agent.tenant_headers,
                )
                data = response.json() if response is not None else {}
                records = data.get("results") or data.get("pres_ex_records") or []
                if records:
                    return records[0].get("pres_ex_id")
            except Exception:
                pass

            time.sleep(0.2)

        return None