from flask import current_app
from app.plugins import AskarStorage, AgentController
from app.models.webhooks import CredentialOffer, Notification

askar = AskarStorage()
agent = AgentController()


class AnonCredsProcessor:
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id

    async def process_offer_v1(self, cred_ex):
        await agent.set_agent_auth(self.wallet_id)

        connection = agent.get_connection_info(cred_ex.get("connection_id"))

        preview = {}
        attributes = (
            cred_ex.get("credential_offer_dict")
            .get("credential_preview")
            .get("attributes")
        )

        for attribute in attributes:
            preview[attribute.get("name")] = attribute.get("value")

        cred_offer = CredentialOffer(
            timestamp=cred_ex.get("created_at"),
            exchange_id=cred_ex.get("cred_ex_id")
            or cred_ex.get("credential_exchange_id"),
            connection_id=cred_ex.get("connection_id"),
            preview=preview,
        ).model_dump()

        await askar.append("cred_ex", cred_ex.get("connection_id"), cred_offer)

        schema_id = cred_ex.get("schema_id")
        cred_def_id = cred_ex.get("credential_definition_id")

        cred_name = schema_id.split(":")[2].replace("_", " ").title()
        issuer_id = cred_def_id.split("/")[0]
        issuer_name = connection.get("their_label")

        cred_template = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential"],
            "name": cred_name,
            "issuer": {
                "id": issuer_id,
                "name": issuer_name,
                "image": connection.get("image"),
            },
            "credentialSubject": {},
        }
        current_app.logger.warning(cred_template)
        await askar.store("template", cred_def_id, cred_template)

        notification = Notification(
            type="cred_offer",
            title=f"{issuer_name} is offering {cred_name}",
            details=cred_offer,
        ).model_dump()
        await askar.append("notifications", self.wallet_id, notification)
        return cred_template

    async def process_offer_v2(self, cred_ex):
        await agent.set_agent_auth(self.wallet_id)

        connection = agent.get_connection_info(cred_ex.get("connection_id"))

        preview = {}
        attributes = (
            cred_ex.get("cred_offer").get("credential_preview").get("attributes")
        )

        for attribute in attributes:
            preview[attribute.get("name")] = attribute.get("value")

        cred_offer = CredentialOffer(
            timestamp=cred_ex.get("created_at"),
            exchange_id=cred_ex.get("cred_ex_id")
            or cred_ex.get("credential_exchange_id"),
            connection_id=cred_ex.get("connection_id"),
            comment=cred_ex.get("cred_offer").get("comment"),
            preview=preview,
        ).model_dump()

        await askar.append("cred_ex", cred_ex.get("connection_id"), cred_offer)

        schema_id = (
            cred_ex.get("by_format").get("cred_offer").get("anoncreds").get("schema_id")
        )
        cred_def_id = (
            cred_ex.get("by_format")
            .get("cred_offer")
            .get("anoncreds")
            .get("cred_def_id")
        )

        schema = agent.get_schema_info(schema_id).get("schema")

        cred_name = schema.get("name")
        issuer_id = cred_def_id.split("/")[0]
        issuer_name = connection.get("their_label")

        cred_template = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential"],
            "name": cred_name,
            "issuer": {
                "id": issuer_id,
                "name": issuer_name,
                "image": connection.get("image"),
            },
            "credentialSubject": {},
        }
        await askar.store("template", cred_def_id, cred_template)

        notification = Notification(
            type="cred_offer",
            title=f"{issuer_name} is offering {cred_name}",
            details=cred_offer,
        ).model_dump()
        await askar.append("notifications", self.wallet_id, notification)

    async def get_template(self, cred_ex):
        cred_def_id = (
            cred_ex.get("by_format")
            .get("cred_offer")
            .get("anoncreds")
            .get("cred_def_id")
        )
        credential = await askar.fetch("template", cred_def_id)

        attributes = (
            cred_ex.get("cred_offer").get("credential_preview").get("attributes")
        )
        for attribute in attributes:
            credential["credentialSubject"][attribute["name"]] = attribute["value"]

        await askar.append("credentials", self.wallet_id, credential)
