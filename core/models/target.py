"""Target model."""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, UUIDMixin, TimestampMixin


class Target(Base, UUIDMixin, TimestampMixin):
    """Authorized target model."""
    __tablename__ = 'targets'

    user_id     = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    ip_or_domain = Column(String(255), nullable=False)
    description  = Column(Text, nullable=True)
    authorized   = Column(Boolean, nullable=False, default=True)
    notes        = Column(Text, nullable=True)

    # Relationships
    user = relationship('User', back_populates='targets')
