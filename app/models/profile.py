from pydantic import BaseModel, Field, Dict, Any

class BaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)

class Profile(BaseModel):
    email: str = Field(None)
    username: str = Field(None)
    client_id: str = Field()
    wallet_id: str = Field()
