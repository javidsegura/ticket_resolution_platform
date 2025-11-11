
from typing import Optional
import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, text
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
