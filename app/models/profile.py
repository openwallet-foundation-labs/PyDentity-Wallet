from pydantic import Field

from .base import CustomBaseModel


class Profile(CustomBaseModel):
    client_id: str = Field()
    wallet_id: str = Field()
    multikey: str = Field()
    email: str = Field(None)
    username: str = Field(None)
