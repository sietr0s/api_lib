from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import declared_attr, declarative_base, relationship

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID, primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.now)


class VersionedModel(Base):
    __abstract__ = True

    @declared_attr
    def previous_version_id(cls):
        return Column(UUID, ForeignKey(f'{cls.__tablename__}.id'), nullable=True)

    @declared_attr
    def previous_version(cls):
        return relationship(lambda: cls, remote_side=cls.id)

    @declared_attr
    def active(cls):
        return Column(Boolean, default=True)