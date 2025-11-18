from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

def validate_profile_pic_object_name(v: str | None) -> str | None:
    if v is not None and ('..' in v or any(ord(c) < 32 for c in v)):
        raise ValueError('Invalid profile picture object name')
    return v

class UserBase(BaseModel):
    displayable_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=255)
    profile_pic_object_name: str = Field(..., min_length=1, max_length=299)
    country: str = Field(..., min_length=2, max_length=2) #ISO

    @field_validator('profile_pic_object_name')
    @classmethod
    def validate_pic_name(cls, v: str) -> str:
        return validate_profile_pic_object_name(v)
    
class UserCreate(UserBase):
    user_id: str = Field(..., min_length=1, max_length=299)

class UserUpdate(BaseModel):
    displayable_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    profile_pic_object_name: str | None = Field(None, min_length=1, max_length=299)
    country: str | None = Field(None, min_length=2, max_length=2)

    @field_validator('profile_pic_object_name')
    @classmethod
    def validate_pic_name(cls, v: str | None) -> str | None:
        return validate_profile_pic_object_name(v)
    
class UserRead(UserBase):
    user_id: str
    timeRegistered: datetime | None = None
    isAdmin: bool | None = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# For admin status changes
class AdminUserUpdate(BaseModel):
    isAdmin: bool | None = None