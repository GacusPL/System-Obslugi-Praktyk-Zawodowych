import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="memory://"
)

def create_app(config_name=None):
    app = Flask(__name__)
    
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    from config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    if config_name == 'production' and app.config.get('SECRET_KEY') == 'default-key-for-development':
        raise ValueError("SECRET_KEY must be set in production config")
    
    # Setup logging
    from app.logging_config import setup_logging
    setup_logging(app)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Exempt API from CSRF protection
    csrf.exempt(api_bp)
    
    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)
    
    # Import models so they are registered with SQLAlchemy metadata
    from app import models
    from app.models import Uzytkownik
    
    # Setup user loader
    @login_manager.user_loader
    def load_user(user_id):
        return Uzytkownik.query.get(int(user_id))
        
    @app.context_processor
    def inject_active_praktyka():
        if current_user.is_authenticated and current_user.rola == 'student':
            from app.models import Student, Praktyka
            student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
            if student:
                praktyka = Praktyka.query.filter_by(student_id=student.id).first()
                return {'active_praktyka': praktyka}
        return {'active_praktyka': None}
        
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            from app.routes.api.helpers import api_error
            return api_error("UNAUTHORIZED", "Wymagane zalogowanie", status=401)
        return redirect(url_for('auth.login'))
        
    # Global redirect check for users without role
    @app.before_request
    def check_user_role():
        # Do not redirect API requests to waiting page (API has its own auth/role checks)
        if request.path.startswith('/api/'):
            return
            
        if current_user.is_authenticated:
            # Bypass waiting check for logout, waiting page, and static assets
            allowed_endpoints = ['auth.waiting', 'auth.logout', 'static']
            if current_user.rola is None and request.endpoint not in allowed_endpoints:
                return redirect(url_for('auth.waiting'))
                
    @app.template_filter('translate_status')
    def translate_status(status):
        translations = {
            'Draft': 'Szkic',
            'Submitted': 'Przesłany',
            'Under_Review': 'W weryfikacji',
            'Approved': 'Zatwierdzony',
            'Rejected': 'Odrzucony',
            'Closed': 'Zakończony'
        }
        return translations.get(status, status)

    @app.template_filter('status_icon')
    def status_icon(status):
        icons = {
            'Draft': 'bi-pencil-square',
            'Submitted': 'bi-send-fill',
            'Under_Review': 'bi-hourglass-split',
            'Approved': 'bi-check-circle-fill',
            'Rejected': 'bi-exclamation-triangle-fill',
            'Closed': 'bi-folder-check'
        }
        return icons.get(status, 'bi-question-circle')
                
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; img-src 'self' data:;"
        return response
                
    return app
