from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    displayable_name: str
    email: EmailStr
    profile_pic_object_name: str
    country: str

class UserCreate(UserBase):
    user_id: str

class UserUpdate(BaseModel):
    displayable_name: str | None = None
    email: EmailStr | None = None
    profile_pic_object_name: str | None = None
    country: str | None = None

class UserRead(UserBase):
    user_id: str
    timeRegistered: datetime | None = None
    isAdmin: bool | None = None
    model_config = ConfigDict(from_attributes=True)

# For admin status changes
class AdminUserUpdate(BaseModel):
    isAdmin: bool | None = None