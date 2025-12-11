from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
	intent_id: int = Field(
		..., gt=0, description="Must be a positive integer referencing an intent"
	)
	type: Literal["micro", "article"]
	status: Literal["accepted", "iteration", "denied"] = "iteration"
	version: int = Field(default=1, ge=1, description="Version must be 1 or higher")
	feedback: str | None = Field(
		None, max_length=2000, description="Feedback on the article"
	)


class ArticleCreate(ArticleBase):
	pass


class ArticleUpdate(BaseModel):
	status: Literal["accepted", "iteration", "denied"] | None = None
	version: int | None = Field(None, ge=1)
	feedback: str | None = Field(None, max_length=2000)


class ArticleRead(ArticleBase):
	id: int
	created_at: datetime
	updated_at: datetime | None = None
	blob_path: str = Field(
		...,
		min_length=1,
		max_length=1000,
		description="Server-generated Azure storage path",
	)

	model_config = ConfigDict(from_attributes=True)


class LatestArticlesResponse(BaseModel):
	intent_id: int
	version: int | None = Field(None, description="Latest version number")
	status: str | None = Field(
		None, description="Article status (accepted, iteration, denied)"
	)
	presigned_url_micro: str | None = Field(
		None, description="Presigned URL to download the micro article content from S3"
	)
	presigned_url_full: str | None = Field(
		None, description="Presigned URL to download the full article content from S3"
	)
