from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CategoryBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=255)
	level: int = Field(..., ge=1, le=3, description="Category level (1-3)")
	parent_id: int | None = Field(None, ge=1, description="Parent category ID")

	@model_validator(mode="after")
	def validate_parent_relationship(self) -> "CategoryBase":
		# Level 1 must not have a parent
		if self.level == 1 and self.parent_id is not None:
			raise ValueError("Level 1 categories cannot have a parent")

		# Level 2+ must have a parent
		if self.level > 1 and self.parent_id is None:
			raise ValueError(f"Level {self.level} categories must have a parent")

		return self


class CategoryCreate(CategoryBase):
	pass


class CategoryUpdate(BaseModel):
	name: str | None = Field(None, min_length=1, max_length=255)


class CategoryRead(CategoryBase):
	id: int
	created_at: datetime
	updated_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
