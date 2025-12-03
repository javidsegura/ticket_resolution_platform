from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import CompanyProfile


async def create_company_profile(
	db: AsyncSession,
	name: str,
	domain: Optional[str] = None,
	industry: Optional[str] = None,
	support_email: Optional[str] = None,
) -> CompanyProfile:
	"""
	Create a new company profile.
	"""
	db_profile = CompanyProfile(
		name=name,
		domain=domain,
		industry=industry,
		support_email=support_email,
	)
	try:
		db.add(db_profile)
		await db.commit()
		await db.refresh(db_profile)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to create company profile: {e}") from e
	return db_profile


async def get_company_profile_by_id(
	db: AsyncSession, profile_id: int
) -> Optional[CompanyProfile]:
	"""
	Retrieve a company profile by ID.
	"""
	result = await db.execute(
		select(CompanyProfile).where(CompanyProfile.id == profile_id)
	)
	return result.scalar_one_or_none()


async def get_all_company_profiles(
	db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[CompanyProfile]:
	"""
	Retrieve all company profiles.
	"""
	result = await db.execute(
		select(CompanyProfile)
		.offset(skip)
		.limit(limit)
		.order_by(CompanyProfile.created_at.desc())
	)
	return result.scalars().all()


async def update_company_profile(
	db: AsyncSession,
	profile_id: int,
	name: Optional[str] = None,
	domain: Optional[str] = None,
	industry: Optional[str] = None,
	support_email: Optional[str] = None,
) -> Optional[CompanyProfile]:
	"""
	Update a company profile. All fields are updatable.
	"""
	profile = await get_company_profile_by_id(db, profile_id)

	if not profile:
		return None

	if name is not None:
		profile.name = name
	if domain is not None:
		profile.domain = domain
	if industry is not None:
		profile.industry = industry
	if support_email is not None:
		profile.support_email = support_email

	try:
		await db.commit()
		await db.refresh(profile)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to update company profile: {e}") from e

	return profile


async def delete_company_profile(db: AsyncSession, profile_id: int) -> bool:
	"""
	Delete a company profile by ID.
	"""
	profile = await get_company_profile_by_id(db, profile_id)
	if profile:
		try:
			await db.delete(profile)
			await db.commit()
		except SQLAlchemyError as e:
			await db.rollback()
			raise RuntimeError(f"Failed to delete company profile: {e}") from e
		return True
	return False
