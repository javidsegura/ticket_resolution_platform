from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IntentBase(BaseModel):
    name: str | None = None
    category_level_1_id: int | None = None
    category_level_2_id: int | None = None
    category_level_3_id: int | None = None
    area: str | None = None
    is_processed: bool = False


class IntentCreate(IntentBase):
    pass


class IntentUpdate(BaseModel):
    name: str | None = None
    category_level_1_id: int | None = None
    category_level_2_id: int | None = None
    category_level_3_id: int | None = None
    area: str | None = None
    is_processed: bool | None = None


class IntentRead(IntentBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
