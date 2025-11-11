from datetime import datetime
from pydantic import BaseModel

class URLShorteningDBStore(BaseModel):
	creator_id: str
	old_link: str
	new_link: str
	expires_at: datetime
	click_count: int