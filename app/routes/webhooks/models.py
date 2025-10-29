from pydantic import Field
from typing import Dict, Union
from datetime import datetime, timezone

from app.models.base import CustomBaseModel

class Connection(CustomBaseModel):
    active: bool = Field()
    state: str = Field()
    created: str = Field()
    updated: str = Field()
    connection_id: str = Field()
    label: str = Field()
    did: Union[str, None] = Field(None)

class Notification(CustomBaseModel):
    id: str = Field()  # Unique notification ID (usually exchange_id)
    new: bool = Field(True)
    type: str = Field()
    title: str = Field()
    details: dict = Field()
    created_at: str = Field()

class Message(CustomBaseModel):
    content: str = Field()
    inbound: bool = Field()
    timestamp: str = Field()


class CredentialOffer(CustomBaseModel):
    state: str = Field()
    completed: bool = Field(False)
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    preview: Union[Dict[str, str], None] = Field(None)


class PresentationRequest(CustomBaseModel):
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    attributes: dict = Field()
    predicates: dict = Field()