from pydantic import BaseModel
from typing import Dict, Any


class CustomBaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)
