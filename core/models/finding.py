"""Finding model."""
from sqlalchemy import Column, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, UUIDMixin, TimestampMixin


class Finding(Base, UUIDMixin, TimestampMixin):
    """Finding model."""
    __tablename__ = 'findings'

    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    description = Column(Text, nullable=True)
    cvss_score = Column(Numeric(3, 1), nullable=True)
    cve_id = Column(String(20), nullable=True)
    remediation = Column(Text, nullable=True)

    # Relationships
    job = relationship('Job', back_populates='findings')
