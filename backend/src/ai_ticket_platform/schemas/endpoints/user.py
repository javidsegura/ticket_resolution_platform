from datetime import datetime  
from pydantic import BaseModel, ConfigDict
from typing import Optional, Type


class CreateUserRequest(BaseModel): # This seems redudant
	user_id: str
	displayable_name: str
	email: str
	profile_pic_object_name: str
	country: str

class ModifyUserNameRequest(BaseModel):
	new_name: str


class UploadProfilePicRequest(BaseModel):
	file_name: str
	content_type: str

class GetUserDataResponse(BaseModel):
	user_id: str
	displayable_name : str
	email : str
	timeRegistered : datetime
	profile_pic_object_name : str
	country : str
	isAdmin : int
	presigned_url_profile_pic: str
	
