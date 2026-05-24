"""
Pytest fixtures - Base SQLAlchemy indépendante pour tests
"""
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import uuid

# Créer une instance SQLAlchemy INDÉPENDANTE
test_db = SQLAlchemy()


@pytest.fixture(scope='session')
def app():
    """Flask app minimale avec BDD test isolée"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialiser NOTRE instance de BDD de test
    test_db.init_app(app)
    
    # Initialiser Flask-Login
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from core.models.user import User
        import uuid
        # Convertir string → UUID object si nécessaire
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        return test_db.session.query(User).filter_by(id=user_id).first()
    
    with app.app_context():
        # Importer les modèles et REMAPPER vers notre Base
        from core.models.base import Base
        from core.models.user import User
        from core.models.job import Job
        from core.models.finding import Finding
        from core.models.artifact import Artifact
        from core.models.audit_log import AuditLog
        
        # RECRÉER les tables avec NOTRE engine
        Base.metadata.create_all(bind=test_db.engine)
        
        yield app
        
        # Cleanup
        Base.metadata.drop_all(bind=test_db.engine)


@pytest.fixture(scope='function')
def db(app):
    """Session BDD pour chaque test"""
    with app.app_context():
        yield test_db
        test_db.session.rollback()
        test_db.session.remove()


@pytest.fixture(scope='function')
def client(app):
    """Test client - charge blueprints uniquement si besoin"""
    if not hasattr(app, '_blueprints_registered'):
        with app.app_context():
            from core.api.routes import auth_bp, api_bp
            from ui.routes import ui_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            app.register_blueprint(api_bp, url_prefix='/api')
            app.register_blueprint(ui_bp)
            app._blueprints_registered = True
    
    return app.test_client()


@pytest.fixture(scope='function')
def auth_client(client, db):
    """Client authentifié"""
    from core.models.user import User
    from werkzeug.security import generate_password_hash
    
    # Vérifier si l'utilisateur existe déjà
    user = db.session.query(User).filter_by(username='testuser').first()
    
    if not user:
        user = User(
            id=uuid.uuid4(),
            username='testuser',
            password_hash=generate_password_hash('testpass'),
            email='test@test.com'
        )
        db.session.add(user)
        db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    
    return client

    
    return client


@pytest.fixture(scope='function')
def sample_job(db):
    """Job de test"""
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
    """Finding de test"""
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
