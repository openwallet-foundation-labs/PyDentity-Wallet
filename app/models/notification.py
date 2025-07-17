from pydantic import BaseModel, Field
from typing import Dict, Any


class BaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)


class Notification(BaseModel):
    id: str = Field()
    type: str = Field()
    title: str = Field()
    origin: str = Field()
    message: str = Field()
    timestamp: str = Field()