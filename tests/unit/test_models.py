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
        id=str(uuid.uuid4()),
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
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        plugin_name='nmap',
        config={'target': '192.168.1.1'},
        status='pending'
    )
    db.session.add(job)
    db.session.commit()
    
    assert job.id is not None
    assert job.status == 'pending'
    assert job.plugin_name == 'nmap'


def test_finding_creation(db, sample_job):
    """Test: Création d'un finding"""
    finding = Finding(
        id=str(uuid.uuid4()),
        job_id=sample_job.id,
        title='SQL Injection',
        severity='critical',
        description='SQL injection vulnerability detected'
    )
    db.session.add(finding)
    db.session.commit()
    
    assert finding.id is not None
    assert finding.severity == 'critical'
    assert finding.job_id == sample_job.id
