from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import CompanyFile


async def create_company_file(
	db: AsyncSession, blob_path: str, original_filename: str, area: Optional[str] = None
) -> CompanyFile:
	"""
	Create a new company file record in the database.
	"""
	db_file = CompanyFile(
		blob_path=blob_path,
		original_filename=original_filename,
		area=area,
	)
	db.add(db_file)
	await db.commit()
	await db.refresh(db_file)
	return db_file


async def get_company_file_by_id(
	db: AsyncSession, file_id: int
) -> Optional[CompanyFile]:
	"""
	Retrieve a company file by its ID.
	"""
	result = await db.execute(select(CompanyFile).where(CompanyFile.id == file_id))
	return result.scalar_one_or_none()


async def get_all_company_files(
	db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[CompanyFile]:
	"""
	Retrieve all company files.
	"""
	result = await db.execute(select(CompanyFile).offset(skip).limit(limit))
	return result.scalars().all()


async def delete_company_file(db: AsyncSession, file_id: int) -> bool:
	"""
	Delete a company file record by ID.
	"""
	file = await get_company_file_by_id(db, file_id)
	if file:
		db.delete(file)
		await db.commit()
		return True
	return False
