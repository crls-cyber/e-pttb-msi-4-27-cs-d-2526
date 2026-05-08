"""Audit logging utilities."""
from flask import request
from flask_login import current_user
from core.models import AuditLog
from core.api.app import db


def audit_log(action, resource_type=None, resource_id=None):
    """Create an audit log entry."""
    try:
        log_entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
    except Exception as e:
        # Don't fail the request if audit logging fails
        print(f"Audit log error: {e}")
        db.session.rollback()
