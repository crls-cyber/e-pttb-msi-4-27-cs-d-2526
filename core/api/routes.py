"""API routes."""
from core.security import audit_log, require_role
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .auth import authenticate_user, logout_current_user
from core.orchestrator import run_plugin
from core.models import Job
from .app import db
import uuid


# Auth blueprint
auth_bp = Blueprint('auth', __name__)

# API blueprint
api_bp = Blueprint('api', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    
    if user:
        audit_log('user.login', 'user', user.id)  #  AJOUT AUDIT
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': str(user.id),
                'username': user.username
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint."""
    logout_current_user()
    return jsonify({'message': 'Logout successful'}), 200


@api_bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user_info():
    """Get current user info."""
    return jsonify({
        'id': str(current_user.id),
        'username': current_user.username,
        'email': current_user.email
    }), 200


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@api_bp.route('/jobs', methods=['POST'])
@login_required
def create_job():
    """Create a new job."""
    data = request.get_json()
    plugin_name = data.get('plugin')
    config = data.get('config', {})
    
    if not plugin_name:
        return jsonify({'error': 'Plugin name required'}), 400
    
    # Create job in database
    job = Job(
        id=uuid.uuid4(),
        user_id=current_user.id,
        plugin_name=plugin_name,
        config=config,
        status='pending'
    )
    
    db.session.add(job)
    db.session.commit()
    
    # Send task to Celery
    task = run_plugin.delay(str(job.id), plugin_name, config)
    
    audit_log('job.create', 'job', job.id)
    
    return jsonify({
        'job_id': str(job.id),
        'task_id': task.id,
        'status': 'pending'
    }), 201


@api_bp.route('/jobs', methods=['GET'])
@login_required
def list_jobs():
    """List user's jobs."""
    jobs = db.session.query(Job).filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'jobs': [{
            'id': str(job.id),
            'plugin': job.plugin_name,
            'status': job.status,
            'created_at': job.created_at.isoformat()
        } for job in jobs]
    }), 200


@api_bp.route('/jobs/<job_id>', methods=['GET'])
@login_required
def get_job(job_id):
    """Get job details."""
    job = db.session.query(Job).filter_by(id=job_id, user_id=current_user.id).first()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'id': str(job.id),
        'plugin': job.plugin_name,
        'config': job.config,
        'status': job.status,
        'error': job.error,
        'created_at': job.created_at.isoformat(),
        'updated_at': job.updated_at.isoformat()
    }), 200
