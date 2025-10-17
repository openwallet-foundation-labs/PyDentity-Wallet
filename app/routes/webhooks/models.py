from pydantic import Field
from typing import Dict, Union
from datetime import datetime, timezone

from app.models.base import CustomBaseModel

class Connection(CustomBaseModel):
    created: str = Field()
    updated: str = Field()
    connection_id: str = Field()
    label: str = Field()
    did: str = Field()

class Notification(CustomBaseModel):
    new: bool = Field(True)
    type: str = Field()
    title: str = Field()
    details: dict = Field()

class Message(CustomBaseModel):
    content: str = Field()
    inbound: bool = Field()
    timestamp: str = Field()


class CredentialOffer(CustomBaseModel):
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    preview: Dict[str, str] = Field()


class PresentationRequest(CustomBaseModel):
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    attributes: dict = Field()
    predicates: dict = Field()