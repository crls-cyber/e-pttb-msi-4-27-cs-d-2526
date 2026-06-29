"""Flask application factory."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    """Create and configure Flask application."""
    import os
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '../../ui/static'), static_url_path='/static')
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'ui.login'
    
    # User loader for Flask-Login
    from core.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)
    
    # Register blueprints (routes)
    from .routes import auth_bp, api_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register UI blueprint
    from ui.routes import ui_bp
    app.register_blueprint(ui_bp)

    return app


def create_test_app():
    """Create Flask app for testing with SQLite in-memory database"""
    app = Flask(__name__)
    
    # Test-specific config
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    from core.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)
    
    # Register blueprints
    from core.api.routes import auth_bp, api_bp
    from ui.routes import ui_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ui_bp)
    
    return app
