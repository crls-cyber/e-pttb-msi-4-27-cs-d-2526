"""User, Role, and Permission models."""
from sqlalchemy import Column, String, Table, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from .base import Base, UUIDMixin, TimestampMixin

# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""
    __tablename__ = 'users'

    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    must_change_password = Column(Boolean, nullable=False, default=False)
    theme = Column(String(10), nullable=False, default='dark')
    density = Column(String(15), nullable=False, default='comfortable')
    session_timeout_minutes = Column(Integer, nullable=False, default=30)

    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    jobs = relationship('Job', back_populates='user')
    targets = relationship('Target', back_populates='user')
    audit_logs = relationship('AuditLog', back_populates='user')

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password is correct."""
        return check_password_hash(self.password_hash, password)

    # Flask-Login required properties (AJOUTER CES 4 MÉTHODES)
    @property
    def is_authenticated(self):
        """User is authenticated."""
        return True

    @property
    def is_active(self):
        """User is active."""
        return True

    @property
    def is_anonymous(self):
        """User is not anonymous."""
        return False

    def get_id(self):
        """Get user ID for Flask-Login."""
        return str(self.id)

class Role(Base, UUIDMixin, TimestampMixin):
    """Role model."""
    __tablename__ = 'roles'

    name = Column(String(50), unique=True, nullable=False)

    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')


class Permission(Base, UUIDMixin, TimestampMixin):
    """Permission model."""
    __tablename__ = 'permissions'

    name = Column(String(100), unique=True, nullable=False)

    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
