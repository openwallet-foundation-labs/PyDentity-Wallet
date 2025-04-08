from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union
from datetime import datetime, timezone
from config import Config


class BaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)

class Notification(BaseModel):
    type: str = Field()
    title: str = Field()
    details: dict = Field()

class Message(BaseModel):
    content: str = Field()
    inbound: bool = Field()
    timestamp: str = Field()


class CredentialOffer(BaseModel):
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    preview: Dict[str, str] = Field()


class PresentationRequest(BaseModel):
    timestamp: str = Field()
    exchange_id: str = Field()
    connection_id: str = Field()
    comment: Union[str, None] = Field(None)
    attributes: dict = Field()
    predicates: dict = Field()