from pydantic import Field

from .base import CustomBaseModel


class Connection(CustomBaseModel):
    active: bool = Field()
    state: str = Field()
    created: str = Field()
    updated: str = Field()
    connection_id: str = Field()
    label: str = Field()
    did: str = Field(None)
