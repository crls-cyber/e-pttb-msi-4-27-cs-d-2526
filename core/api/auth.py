"""Authentication utilities."""
from flask_login import login_user, logout_user, current_user
from core.models import User
from .app import db


def authenticate_user(username, password):
    """Authenticate user and create session."""
    user = db.session.query(User).filter_by(username=username).first()
    
    if user and user.check_password(password):
        login_user(user)
        return user
    
    return None


def logout_current_user():
    """Logout current user."""
    logout_user()


def get_current_user():
    """Get currently authenticated user."""
    return current_user if current_user.is_authenticated else None
