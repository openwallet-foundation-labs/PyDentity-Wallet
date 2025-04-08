from flask import current_app
import requests
import json
import base64
from app.services import AgentController, AskarStorage
from urllib.parse import urlparse

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

            if query_string.startswith("oob=") or query_string.startswith("_oob="):
                await self.didcomm_handler(decode_invitation(payload.split("=")[-1]))

            elif query_string.startswith("_oobid="):
                r = requests.get(payload)
                if r.status_code == 200:
                    await self.didcomm_handler(r.json())
                else:
                    pass

        elif uri.scheme == "didcomm":
            query_string = payload.split("?")[-1]

            if query_string.startswith("oob=") or query_string.startswith("_oob="):
                await self.didcomm_handler(decode_invitation(payload.split("=")[-1]))

    async def didcomm_handler(self, invitation):
        current_app.logger.warning("DIDComm Invitation")

        # Model cannot have goal_code without goal
        if not invitation.get("goal"):
            invitation.pop("goal_code", None)

        if isinstance(invitation.get("@type"), str) and invitation.get(
            "@type"
        ).startswith("https://didcomm.org/out-of-band/1.1"):
            wallet = await askar.fetch("wallet", self.wallet_id)

            agent.set_token(wallet["token"])
            agent.receive_invitation(invitation)
