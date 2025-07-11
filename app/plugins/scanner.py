from flask import current_app


class QRScanner:
    def __init__(self, client_id, wallet_id):
        self.client_id = client_id
        self.wallet_id = wallet_id

    async def handle_payload(self, payload):
        current_app.logger.warning("Parsing payload")
        current_app.logger.warning(payload)
        return
