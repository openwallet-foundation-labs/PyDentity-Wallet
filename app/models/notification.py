from pydantic import Field

from .base import CustomBaseModel


class Notification(CustomBaseModel):
    id: str = Field()
    type: str = Field()
    title: str = Field()
    origin: str = Field()
    message: str = Field()
    timestamp: str = Field()
