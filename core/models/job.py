"""Job model."""
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, UUIDMixin, TimestampMixin


class Job(Base, UUIDMixin, TimestampMixin):
    """Job model."""
    __tablename__ = 'jobs'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    plugin_name = Column(String(50), nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed
    error = Column(Text, nullable=True)

    # Relationships
    user = relationship('User', back_populates='jobs')
    findings = relationship('Finding', back_populates='job', cascade='all, delete-orphan')
    artifacts = relationship('Artifact', back_populates='job', cascade='all, delete-orphan')
