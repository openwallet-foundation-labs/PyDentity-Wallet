from pydantic import Field

from .base import CustomBaseModel


class Connection(CustomBaseModel):
    created: str = Field()
    updated: str = Field()
    connection_id: str = Field()
    label: str = Field()
    did: str = Field()
