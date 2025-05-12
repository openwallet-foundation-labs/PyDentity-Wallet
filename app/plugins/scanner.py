from flask import current_app
import requests
import json
import base64
from app.plugins import AgentController, AskarStorage
from app.utils import decode_jwt_vc
from urllib.parse import urlparse, unquote

askar = AskarStorage()
agent = AgentController()


def decode_invitation(data):
    return json.loads(base64.urlsafe_b64decode(data + "===").decode())


class QRScanner:
    def __init__(self, client_id=None, wallet_id=None):
        self.client_id = client_id
        self.wallet_id = wallet_id

    async def handle_payload(self, payload):
        current_app.logger.warning("Parsing payload")
        uri = urlparse(payload)

        if uri.scheme == "https":
            query_string = payload.split("?")[-1]
            if (
                query_string.startswith("c_i=") 
                or query_string.startswith("oob=") 
                or query_string.startswith("_oob=")
                ):
                await self.didcomm_handler(decode_invitation(payload.split("=")[-1]))

            elif query_string.startswith("_oobid="):
                r = requests.get(payload)
                if r.status_code == 200:
                    await self.didcomm_handler(r.json())
                else:
                    pass

            # VC Playground interaction URI
            elif uri.netloc == 'vcplayground.org':
                current_app.logger.warning("VC Playground")
                await self.vc_api_handler(unquote(uri.path.split('/')[-1]))
                
            else:
                # Simple pickup
                
                r = requests.get(payload, headers={'Accept': 'application/vc'})
                credential = json.loads(r.text)
                wallet = await askar.fetch('wallet', self.wallet_id)
                agent.set_token(wallet['token'])
                agent.store_credential(credential)
                # await askar.append('credentials', self.wallet_id, credential)
                
                # r = requests.get(payload, headers={'Accept': 'application/vc+jwt'})
                # jwt_vc = r.text
                # credential = decode_jwt_vc(jwt_vc)
                # envelope = {
                #     "@context": "https://www.w3.org/ns/credentials/v2",
                #     "type": "EnvelopedVerifiableCredential",
                #     "id": f"data:application/vc+jwt,{jwt_vc}",
                #     'name': credential.get('name'),
                #     'issuer': credential.get('issuer'),
                #     'validFrom': credential.get('validFrom'),
                #     'validUntil': credential.get('validUntil'),
                # }
                # await askar.append('credentials', self.wallet_id, envelope)
                
                
                # await agent.set_agent_auth(self.wallet_id)
                # vc = agent.store_credential(credential).get('verifiableCredential')
                # current_app.logger.warning(vc)
                # if vc:
                #     await askar.append('credentials', self.wallet_id, vc)

        elif uri.scheme == "didcomm":
            query_string = payload.split("?")[-1]

            if query_string.startswith("oob=") or query_string.startswith("_oob="):
                await self.didcomm_handler(decode_invitation(payload.split("=")[-1]))

    async def didcomm_handler(self, invitation):
        current_app.logger.warning("DIDComm Invitation")

        # Model cannot have goal_code without goal
        if not invitation.get("goal"):
            invitation.pop("goal_code", None)

        # TODO, support other than out-of-band
        if isinstance(invitation.get("@type"), str) and invitation.get(
            "@type"
        ).startswith("https://didcomm.org/out-of-band/1.1"):
            await agent.set_agent_auth(self.wallet_id)
            agent.receive_invitation(invitation)
    
    async def vc_api_handler(self, exchange_url):
        current_app.logger.warning("VC-API Exchange")
        wallet = await askar.fetch('wallet', self.wallet_id)
        exchange = requests.post(exchange_url, json={}).json()
        if exchange.get('verifiablePresentation'):
            vp = exchange.get('verifiablePresentation')
            for vc in vp['verifiableCredential']:
                current_app.logger.warning(vc)
                agent.set_token(wallet['token'])
                agent.store_credential(vc)
                
