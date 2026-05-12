"""
Tests unitaires des modèles de données
"""
import pytest
from core.models.user import User
from core.models.job import Job
from core.models.finding import Finding
import uuid


def test_user_creation(db):
    """Test: Création d'un utilisateur"""
    user = User(
        id=uuid.uuid4(),  # UUID object, pas string !
        username='testuser',
        password_hash='hashed_password',
        email='test@example.com'
    )
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.username == 'testuser'


def test_job_creation(db):
    """Test: Création d'un job"""
    job = Job(
        id=uuid.uuid4(),  # UUID object
        user_id=uuid.uuid4(),  # UUID object
        plugin_name='nmap',
        config={'target': '192.168.1.1'},
        status='pending'
    )
    db.session.add(job)
    db.session.commit()
    
    assert job.id is not None
    assert job.plugin_name == 'nmap'


def test_finding_creation(db, sample_job):
    """Test: Création d'un finding"""
    finding = Finding(
        id=uuid.uuid4(),  # UUID object
        job_id=sample_job.id,
        title='Test vulnerability',
        severity='high'
    )
    db.session.add(finding)
    db.session.commit()
    
    assert finding.id is not None
    assert finding.severity == 'high'
