from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ai_ticket_platform.database.generated_models import Category


class IntentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_level_1_id: int | None = Field(None, ge=1)
    category_level_2_id: int | None = Field(None, ge=1)
    category_level_3_id: int | None = Field(None, ge=1)
    area: str | None = Field(None, min_length=1, max_length=255)
    is_processed: bool = False

class IntentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_level_1_id: int | None = Field(None, ge=1)
    category_level_2_id: int | None = Field(None, ge=1)
    category_level_3_id: int | None = Field(None, ge=1)
    area: str | None = Field(None, min_length=1, max_length=255)
    is_processed: bool = False

    @field_validator('category_level_1_id', 'category_level_2_id', 'category_level_3_id', mode='after')
    @classmethod
    def validate_category_levels(cls, v, info):
        if v is None:
            return v
        
        # Extract expected level from field name 
        field_name = info.field_name
        level_map = {
            'category_level_1_id': 1,
            'category_level_2_id': 2,
            'category_level_3_id': 3,
        }
        expected_level = level_map.get(field_name)
        
        # Try to get db from context
        db = info.context.get('db') if info.context else None
        if not db:
            # Skip validation if no DB session available
            return v 

        category = db.query(Category).filter_by(id=v).first()
        if not category:
            raise ValueError(f'Category with id {v} does not exist')
        
        # Check if level matches
        if category.level != expected_level:
            raise ValueError(f'Category {v} is level {category.level}, but category_level_{expected_level}_id expects a level {expected_level} category')
        
        return v


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
