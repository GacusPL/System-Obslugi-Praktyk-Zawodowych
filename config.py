import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key-for-development')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MSAL Settings
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID')
    MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI')
    MICROSOFT_AUTHORITY = os.environ.get('MICROSOFT_AUTHORITY')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/app.db')

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Use SQLite in-memory or a temporary file for tests
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite://')
    # WTF_CSRF_ENABLED = False is usually helpful in tests
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    # production must use MariaDB/MySQL or configured DB
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Security cookies settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
