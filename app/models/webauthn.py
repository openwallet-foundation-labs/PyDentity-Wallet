from pydantic import Field

from .base import CustomBaseModel


class WebAuthnCredential(CustomBaseModel):
    client_id: str = Field()
    credential_id: str = Field()
    credential_public_key: str = Field()
    current_sign_count: int = Field()
