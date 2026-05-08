"""Role-Based Access Control (RBAC)."""
from functools import wraps
from flask import jsonify
from flask_login import current_user


def require_permission(permission_name):
    """Decorator to require a specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has the required permission
            has_permission = any(
                permission.name == permission_name
                for role in current_user.roles
                for permission in role.permissions
            )
            
            if not has_permission:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(role_name):
    """Decorator to require a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has the required role
            has_role = any(role.name == role_name for role in current_user.roles)
            
            if not has_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
