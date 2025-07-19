
import requests
from flask import current_app
from app.plugins.vcapi import VcApiExchanger

from urllib.parse import urlparse


class QRScanner:
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id

    async def handle_payload(self, payload):
        current_app.logger.warning("Parsing payload")
        uri = urlparse(payload)
        if uri.scheme == "https":
            if uri.query.startswith("iuv=1"):
                # Handle Interaction URL Version 1
                await self.iuv_handler(payload)
        return

    async def iuv_handler(self, payload):
        current_app.logger.warning("Interactions URL")
        r = requests.get(payload, headers={'Accept': 'application/json'})
        protocols = r.json().get('protocols')
        if protocols.get('vcapi', None):
            current_app.logger.warning("VC API Exchange")
            vcapi = VcApiExchanger(self.wallet_id, protocols.get('vcapi'))
            exchange = vcapi.initiate_exchange()
            if exchange.get('verifiablePresentation', None):
                current_app.logger.warning("Verifiable Presentation")
                await vcapi.store_credential(exchange.get('verifiablePresentation'))
                
            elif exchange.get('verifiablePresentationRequest', None):
                current_app.logger.warning("Verifiable Presentation Request")
                await vcapi.present_credential(exchange.get('verifiablePresentationRequest'))
                
            elif exchange.get('redirectUrl', None):
                redirect_url = exchange.get('redirectUrl')
                redirect_url
           
