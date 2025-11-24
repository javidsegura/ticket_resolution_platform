from typing import List, Optional
import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, TIMESTAMP, text, CheckConstraint
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# THESE MODELS NEED TO BE UPDATED
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slack_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (CheckConstraint("status IN ('iteration', 'accepted', 'denied')",name="check_article_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intent_id: Mapped[int] = mapped_column(ForeignKey("intents.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    blob_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'iteration'"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1")) #TODO: autoincrement versions on update
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    intent = relationship("Intent", back_populates="articles") 

class Category(Base): #TODO: Create a utility function that checks no circular dependencies exist
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint('id != parent_id', name='check_no_self_reference'),
        CheckConstraint('level BETWEEN 1 AND 3', name='check_level_range'),
        CheckConstraint(
            '(level = 1 AND parent_id IS NULL) OR (level > 1 AND parent_id IS NOT NULL)',
            name='check_parent_by_level'
        ),
    ) #no self-reference

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    

    parent: Mapped["Category | None"] = relationship("Category", remote_side=[id], back_populates="children")
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    

class CompanyFile(Base):
    __tablename__ = "company_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    area: Mapped[str | None] = mapped_column(String(255))
    blob_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(100))
    support_email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

class Intent(Base):
    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_level_1_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category_level_2_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category_level_3_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    area: Mapped[str | None] = mapped_column(String(255))
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    category_level_1 = relationship("Category", foreign_keys=[category_level_1_id], lazy="joined")
    category_level_2 = relationship("Category", foreign_keys=[category_level_2_id], lazy="joined")
    category_level_3 = relationship("Category", foreign_keys=[category_level_3_id], lazy="joined")
    
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="intent", cascade="all, delete-orphan")
    source_tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="intent")


class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    # Tickets start with intent_id=None when first created. After clustering is done, the orchestrator updates intent_id to correct value
    intent_id: Mapped[int | None] = mapped_column(ForeignKey("intents.id", ondelete='SET NULL'), nullable=True)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    
    intent: Mapped["Intent | None"] = relationship("Intent", back_populates="source_tickets", passive_deletes=True)