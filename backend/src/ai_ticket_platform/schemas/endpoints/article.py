from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    intent_id: int
    type: str
    blob_path: str
    status: str = "iteration"
    version: int = 1
    feedback: str | None = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    status: str | None = None
    version: int | None = None
    blob_path: str | None = None
    feedback: str | None = None


class ArticleRead(ArticleBase): 
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
