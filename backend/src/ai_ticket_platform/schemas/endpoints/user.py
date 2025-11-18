from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    displayable_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    profile_pic_object_name: str = Field(..., min_length=1, max_length=299)
    country: str = Field(..., min_length=2, max_length=2) #ISO

    @field_validator('profile_pic_object_name')
    @classmethod
    def validate_pic_name(cls, v: str) -> str:
        if '..' in v or any(ord(c) < 32 for c in v):
            raise ValueError('Invalid profile picture object name')
        return v
    
class UserCreate(UserBase):
    user_id: str = Field(..., min_length=1, max_length=299)

class UserUpdate(BaseModel):
    displayable_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    profile_pic_object_name: str | None = Field(None, min_length=1, max_length=299)
    country: str | None = Field(None, min_length=2, max_length=2)

class UserRead(UserBase):
    user_id: str
    time_registered: datetime | None = Field(None, alias="timeRegistered")
    is_admin: bool | None = Field(None, alias="isAdmin")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# For admin status changes
class AdminUserUpdate(BaseModel):
    isAdmin: bool | None = None