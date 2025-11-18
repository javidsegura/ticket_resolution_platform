from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyFileBase(BaseModel):
    area: str | None = Field(None, max_length=255, description="File area/category")
    original_filename: str = Field(..., min_length=1, max_length=255, description="Original uploaded filename")
    
    @field_validator('original_filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if '..' in v or '/' in v or '\\' in v or any(ord(c) < 32 for c in v):
            raise ValueError('Filename contains invalid characters')
        return v

class CompanyFileCreate(CompanyFileBase):
    pass


class CompanyFileRead(CompanyFileBase):
    id: int
    blob_path: str = Field(..., min_length=1, max_length=1000, description="Server-generated Azure storage path")
    created_at: datetime
    updated_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
