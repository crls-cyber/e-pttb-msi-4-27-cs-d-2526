"""
Pytest fixtures communes pour tous les tests
"""
import pytest
from core.api.app import create_test_app, db as _db
from core.models.user import User
from werkzeug.security import generate_password_hash
import uuid


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_test_app()
    
    with app.app_context():
        # Import ALL models BEFORE create_all()
        from core.models.user import User
        from core.models.job import Job
        from core.models.finding import Finding
        from core.models.artifact import Artifact
        from core.models.audit_log import AuditLog
        
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create database for testing"""
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def auth_client(client, db):
    """Create authenticated test client"""
    # Create test user
    user = User(
        id=uuid.uuid4(),
        username='testuser',
        password_hash=generate_password_hash('testpass'),
        email='test@test.com'
    )
    db.session.add(user)
    db.session.commit()
    
    # Login
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    
    return client


@pytest.fixture(scope='function')
def sample_job(db):
    """Create sample job for testing"""
    from core.models.job import Job
    
    job = Job(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        plugin_name='nmap',
        config={'target': '192.168.1.1'},
        status='completed'
    )
    db.session.add(job)
    db.session.commit()
    
    return job


@pytest.fixture(scope='function')
def sample_finding(db, sample_job):
    """Create sample finding for testing"""
    from core.models.finding import Finding
    
    finding = Finding(
        id=uuid.uuid4(),
        job_id=sample_job.id,
        title='Test vulnerability',
        severity='high',
        description='Test description'
    )
    db.session.add(finding)
    db.session.commit()
    
    return finding
