from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ArticleBase(BaseModel):
    intent_id: int = Field(..., gt=0, description="Must be a positive integer referencing an intent")
    type: Literal["micro", "article"]
    blob_path: str = Field(..., min_length=1, max_length=1000, description="Server-generated Azure storage path")
    status: Literal["accepted", "iteration", "denied"] = "iteration"
    version: int = Field(default=1, ge=1, description="Version must be 1 or higher")
    feedback: str | None = Field(None, max_length=2000, description="Feedback on the article")

    @field_validator('blob_path')
    @classmethod
    def validate_blob_path(cls, v: str) -> str:
        if '..' in v:
            raise ValueError('Blob path contains invalid ".." sequence')
        return v


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    status: Literal["accepted", "iteration", "denied"] | None = None
    version: int | None = Field(None, ge=1)
    blob_path: str | None = Field(None, min_length=1, max_length=1000)
    feedback: str | None = Field(None, max_length=2000)

    @field_validator('blob_path')
    @classmethod
    def validate_blob_path(cls, v: str | None) -> str | None:
        if v and '..' in v:
            raise ValueError('Blob path contains invalid ".." sequence')
        return v


class ArticleRead(ArticleBase): 
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)