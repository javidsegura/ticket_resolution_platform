from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional, List

from ai_ticket_platform.database.generated_models import CompanyFile


def create_company_file(db: Session, blob_path: str, original_filename: str, area: Optional[str] = None) -> CompanyFile:
	"""
	Create a new company file record in the database.
	"""
	db_file = CompanyFile(
		blob_path=blob_path,
		original_filename=original_filename,
		area=area,
	)
	db.add(db_file)
	db.commit()
	db.refresh(db_file)
	return db_file


def get_company_file_by_id(db: Session, file_id: int) -> Optional[CompanyFile]:
	"""
	Retrieve a company file by its ID.
	"""
	result = db.execute(select(CompanyFile).where(CompanyFile.id == file_id))
	return result.scalar_one_or_none()


def get_all_company_files(db: Session) -> List[CompanyFile]:
	"""
	Retrieve all company files.
	"""
	result = db.execute(select(CompanyFile))
	return list(result.scalars().all())


def delete_company_file(db: Session, file_id: int) -> bool:
	"""
	Delete a company file record by ID.
	"""
	file = get_company_file_by_id(db, file_id)
	if file:
		db.delete(file)
		db.commit()
		return True
	return False
