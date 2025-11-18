from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IntentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_level_1_id: int | None = Field(None, ge=1)
    category_level_2_id: int | None = Field(None, ge=1)
    category_level_3_id: int | None = Field(None, ge=1)
    area: str | None = Field(None, min_length=1, max_length=255)
    is_processed: bool = False


class IntentCreate(IntentBase):
    name: str = Field(..., min_length=1, max_length=255)
    category_level_1_id: int = Field(..., ge=1)


class IntentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    category_level_1_id: int | None = Field(None, ge=1)
    category_level_2_id: int | None = Field(None, ge=1)
    category_level_3_id: int | None = Field(None, ge=1)
    area: str | None = Field(None, min_length=1, max_length=255)
    is_processed: bool | None = None


class IntentRead(IntentBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
