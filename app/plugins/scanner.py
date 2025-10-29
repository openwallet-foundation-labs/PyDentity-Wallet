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
                await self.didcomm_handler(decoded_invitation)
                return {"type": "oob_invitation", "label": decoded_invitation.get("label", "Unknown")}
                
            # elif payload.split('?')[-1].startswith('_oobid='):
            #     try:
            #         invitation = r.json()
            #         await self.didcomm_handler(invitation)
            #     except:
            #         current_app.logger.info(r.text)
        
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
