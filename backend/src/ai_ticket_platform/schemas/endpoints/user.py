from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    displayable_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=255)
    country: str = Field(..., min_length=2, max_length=299)

class UserCreate(UserBase):
    user_id: str = Field(..., min_length=1, max_length=299)

class UserUpdate(BaseModel):
    displayable_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    country: str | None = Field(None, min_length=299, max_length=299)

class UserRead(UserBase):
    user_id: str
    profile_pic_object_name: str = Field(..., min_length=1, max_length=299)
    timeRegistered: datetime | None = None
    isAdmin: bool | None = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# For admin status changes
class AdminUserUpdate(BaseModel):
    isAdmin: bool | None = None
    