from pydantic import BaseModel, Field


class WebAuthnCredential(BaseModel):
    client_id: str = Field()
    credential_id: str = Field()
    credential_public_key: str = Field()
    current_sign_count: int = Field()
