from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
import re

def validate_domain(v: str | None) -> str | None:
        if v is None:
            return v
        # Convert to lowercase for consistency and strip whitespace
        v = v.strip().lower()
        # Basic domain pattern validation
        if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$', v):
            raise ValueError('Invalid domain format')
        return v
    
class CompanyProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str | None = Field(None, min_length=1, max_length=255, description="Company domain")
    industry: str | None = Field(None, min_length=1, max_length=100)
    support_email: EmailStr | None = Field(None, max_length=255)

    @field_validator('domain')
    @classmethod
    def validate_domain_field(cls, v):
        return validate_domain(v)


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, min_length=1, max_length=255, description="Company domain")
    industry: str | None = Field(None, min_length=1, max_length=100)
    support_email: EmailStr | None = Field(None, max_length=255)

    @field_validator('domain')
    @classmethod
    def validate_domain_field(cls, v):
        return validate_domain(v)


class CompanyProfileRead(CompanyProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
