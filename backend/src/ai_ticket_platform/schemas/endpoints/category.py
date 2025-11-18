from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_parent_id(v: int | None, level: int | None) -> int | None:
    """Validate parent_id based on category level.
    
    Skip validation if level is not provided (for partial updates).
    Level 1 must not have a parent, Level 2+ must have a parent.
    """
    # Skip validation if level is not provided (for partial updates)
    if level is None:
        return v
    # Level 1 must not have a parent
    if level == 1 and v is not None:
        raise ValueError('Level 1 categories cannot have a parent')
    # Level 2+ must have a parent
    if level and level > 1 and v is None:
        raise ValueError(f'Level {level} categories must have a parent')
    
    return v

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    level: int = Field(..., ge=1, le=3, description='Category level (1-3)')
    parent_id: int | None = Field(None, ge=1, description="Parent category ID")
    
    @field_validator('parent_id', mode='after') #after parent_id ge=1
    @classmethod
    def validate_parent_id_field(cls, v: int | None, info) -> int | None:
        level = info.data.get('level')
        return validate_parent_id(v, level)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    level: int | None = Field(None, ge=1, le=3)
    parent_id: int | None = Field(None, ge=1)

    @field_validator('parent_id', mode='after')
    @classmethod
    def validate_parent_id_field(cls, v: int | None, info) -> int | None:
        level = info.data.get('level')
        return validate_parent_id(v, level)

class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
