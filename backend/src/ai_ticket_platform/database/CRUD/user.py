from sqlalchemy import select, update

from ai_ticket_platform.database import User
from ai_ticket_platform.schemas.endpoints import CreateUserRequest
from sqlalchemy.ext.asyncio import AsyncSession



async def create_user(db: AsyncSession, user_data: CreateUserRequest) -> User:
	db_user = User(
		user_id=user_data.user_id,
		displayable_name=user_data.displayable_name,
		email=user_data.email,
		profile_pic_object_name=user_data.profile_pic_object_name,
		country=user_data.country,
	)

	db.add(db_user)

	await db.commit()
	await db.refresh(db_user)

	return db_user


async def read_user(db: AsyncSession, user_id: str) -> User:
	result = await db.execute(select(User).where(User.user_id == user_id))
	return result.scalar_one_or_none()

async def delete_user(db: AsyncSession, user_id: str) -> bool:
	user = await read_user(db, user_id)
	if user is None:
		return False
	await db.delete(user)
	await db.commit()
	return True

async def edit_user_name(db: AsyncSession, user_id: str, new_name: str) -> User | None:
	new_name_statment = update(User)\
						  .where(User.user_id == user_id)\
						  .values(displayable_name=new_name)
	await db.execute(new_name_statment)
	await db.commit()
	select_stmt = select(User).where(User.user_id == user_id)
	result = await db.execute(select_stmt)
	user = result.scalar_one_or_none()
	
	return user
