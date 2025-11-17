from typing import List, Optional
import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


# THESE MODELS NEED TO BE UPDATED
class User(Base):
    __tablename__ = 'user'

    user_id: Mapped[str] = mapped_column(String(299), primary_key=True)
    displayable_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_pic_object_name: Mapped[str] = mapped_column(String(299), nullable=False)
    country: Mapped[str] = mapped_column(String(299), nullable=False)
    timeRegistered: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    isAdmin: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'0'"))

    link: Mapped[list['Link']] = relationship('Link', back_populates='creator', cascade="all, delete-orphan")


class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        ForeignKeyConstraint(['creator_id'], ['user.user_id'], name='link_ibfk_1'),
        Index('creator_id', 'creator_id')
    )

    link_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creator_id: Mapped[str] = mapped_column(String(299), nullable=False)
    old_link: Mapped[str] = mapped_column(String(299), nullable=False)
    new_link: Mapped[str] = mapped_column(String(299), nullable=False)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    timeRegistered: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    click_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'0'"))

    creator: Mapped['User'] = relationship('User', back_populates='link')


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intent_id: Mapped[int] = mapped_column(ForeignKey("intents.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    blob_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="iteration")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    intent = relationship("Intent", back_populates="articles") 



class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    
    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id", back_populates="children")
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent", cascade="all, delete-orphan")



class CompanyFile(Base):
    __tablename__ = "company_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    area: Mapped[str | None] = mapped_column(String(255))
    blob_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255))
    support_email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class Intent(Base):
    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    category_level_1_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category_level_2_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category_level_3_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    area: Mapped[str | None] = mapped_column(String(255))
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    
    category_level_1 = relationship("Category", foreign_keys=[category_level_1_id], lazy="joined")
    category_level_2 = relationship("Category", foreign_keys=[category_level_2_id], lazy="joined")
    category_level_3 = relationship("Category", foreign_keys=[category_level_3_id], lazy="joined")
    
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="intent", cascade="all, delete-orphan")


