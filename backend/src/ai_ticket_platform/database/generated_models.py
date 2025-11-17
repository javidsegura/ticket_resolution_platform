
from typing import Optional
import datetime
from uuid import uuid4
import enum

from sqlalchemy import DateTime, Enum, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, text, JSON, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


# Status enums for workflow
class TicketStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    DRAFT_READY = "DRAFT_READY"


class DraftStatus(str, enum.Enum):
    PENDING = "PENDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    NEEDS_EDIT = "NEEDS_EDIT"
    PUBLISHED = "PUBLISHED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    NEEDS_EDIT = "NEEDS_EDIT"


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


# Ticket/Issue model
class Ticket(Base):
    __tablename__ = 'tickets'

    ticket_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    status: Mapped[str] = mapped_column(Enum(TicketStatus), default=TicketStatus.UPLOADED, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    drafts: Mapped[list['Draft']] = relationship('Draft', back_populates='ticket', cascade="all, delete-orphan")


# Draft/Article model
class Draft(Base):
    __tablename__ = 'drafts'
    __table_args__ = (
        ForeignKeyConstraint(['ticket_id'], ['tickets.ticket_id'], name='draft_ibfk_1'),
        Index('ticket_id', 'ticket_id')
    )

    draft_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content: Mapped[str] = mapped_column(String(10000), nullable=False)
    status: Mapped[str] = mapped_column(Enum(DraftStatus), default=DraftStatus.PENDING, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    ticket: Mapped['Ticket'] = relationship('Ticket', back_populates='drafts')
    approvals: Mapped[list['Approval']] = relationship('Approval', back_populates='draft', cascade="all, delete-orphan")
    published_articles: Mapped[list['PublishedArticle']] = relationship('PublishedArticle', back_populates='draft', cascade="all, delete-orphan")


# Approval/Review model
class Approval(Base):
    __tablename__ = 'approvals'
    __table_args__ = (
        ForeignKeyConstraint(['draft_id'], ['drafts.draft_id'], name='approval_ibfk_1'),
        ForeignKeyConstraint(['reviewer_id'], ['user.user_id'], name='approval_ibfk_2'),
        Index('draft_id', 'draft_id'),
        Index('reviewer_id', 'reviewer_id')
    )

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    draft_id: Mapped[str] = mapped_column(String(36), nullable=False)
    slack_message_ts: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(299), nullable=True)
    response_payload: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    draft: Mapped['Draft'] = relationship('Draft', back_populates='approvals')
    reviewer: Mapped[Optional['User']] = relationship('User', foreign_keys=[reviewer_id])


# Published Article model
class PublishedArticle(Base):
    __tablename__ = 'published_articles'
    __table_args__ = (
        ForeignKeyConstraint(['draft_id'], ['drafts.draft_id'], name='article_ibfk_1'),
        Index('draft_id', 'draft_id')
    )

    article_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    draft_id: Mapped[str] = mapped_column(String(36), nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    microsite_url: Mapped[str] = mapped_column(String(500), nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    draft: Mapped['Draft'] = relationship('Draft', back_populates='published_articles')
