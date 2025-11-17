from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfileBase(BaseModel):
    name: str = Field(..., min_length=1)
    domain: str | None = None
    industry: str | None = None
    support_email: str | None = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    support_email: str | None = None


class CompanyProfileRead(CompanyProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
