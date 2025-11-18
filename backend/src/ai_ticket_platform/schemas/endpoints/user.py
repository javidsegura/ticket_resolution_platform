from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., max_length=255)
    role: str = Field(..., min_length=1, max_length=100)
    area: str | None = Field(None, min_length=1, max_length=255)
    slack_user_id: str = Field(..., min_length=1, max_length=255)  

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = Field(None, max_length=255)
    role: str | None = Field(None, min_length=1, max_length=100)
    area: str | None = Field(None, min_length=1, max_length=255)
    slack_user_id: str | None = Field(None, min_length=1, max_length=255) 

class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
    