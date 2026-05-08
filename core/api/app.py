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
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # User loader for Flask-Login
    from core.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)
    
    # Register blueprints (routes)
    from .routes import auth_bp, api_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
