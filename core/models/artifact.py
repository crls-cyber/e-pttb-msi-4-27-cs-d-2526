"""Artifact model."""
from sqlalchemy import Column, String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, UUIDMixin, TimestampMixin


class Artifact(Base, UUIDMixin, TimestampMixin):
    """Artifact model."""
    __tablename__ = 'artifacts'

    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    minio_bucket = Column(String(100), nullable=False)
    minio_key = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=True)

    # Relationships
    job = relationship('Job', back_populates='artifacts')
