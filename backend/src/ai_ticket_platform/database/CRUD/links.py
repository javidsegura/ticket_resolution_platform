from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..generated_models import Link
from ai_ticket_platform.schemas.db_CRUD import URLShorteningDBStore

async def create_link(db: AsyncSession, url_info: URLShorteningDBStore) -> Link:
	db_link = Link(
		creator_id=url_info.creator_id,
		old_link=url_info.old_link,
		new_link=url_info.new_link,
		expires_at=url_info.expires_at,
		click_count=url_info.click_count,
	)
	db.add(db_link)
	await db.commit()
	await db.refresh(db_link)
	return db_link


async def increment_link_count(db: AsyncSession, url: str) -> None:
	link = (
		update(Link)
		.where(Link.new_link == url)
		.values(click_count=Link.click_count + 1)
	)
	await db.execute(link)
	await db.commit()


async def get_list_of_links(db: AsyncSession, user_id: str) -> List[Link]:
	db_links = select(Link).where(Link.creator_id == user_id)
	result = await db.execute(db_links)
	return result.scalars().all()
