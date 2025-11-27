from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import User


async def create_user(
    db: AsyncSession,
    name: str,
    email: str,
    role: str,
    slack_user_id: str,
    area: Optional[str] = None
) -> User:
    """
    Create a new user.
    """
    db_user = User(
        name=name,
        email=email,
        role=role,
        slack_user_id=slack_user_id,
        area=area,
    )
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        await db.rollback()
        raise RuntimeError(f"Failed to create user: {e}") from e
    return db_user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieve all users.
    """
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def update_user(
    db: AsyncSession,
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    slack_user_id: Optional[str] = None,
    area: Optional[str] = None
) -> Optional[User]:
    """
    Update a user. All fields are updatable.
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        return None

    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    if role is not None:
        user.role = role
    if slack_user_id is not None:
        user.slack_user_id = slack_user_id
    if area is not None:
        user.area = area

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise RuntimeError(f"Failed to update user: {e}") from e

    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user by ID.
    """
    user = await get_user_by_id(db, user_id)
    if user:
        try:
            await db.delete(user)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise RuntimeError(f"Failed to delete user: {e}") from e
        return True
    return False
