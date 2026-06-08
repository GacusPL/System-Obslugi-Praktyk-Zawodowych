import os
import importlib

def test_development_config():
    import config
    importlib.reload(config)
    assert config.DevelopmentConfig.DEBUG is True
    assert "sqlite" in config.DevelopmentConfig.SQLALCHEMY_DATABASE_URI or "mysql" in config.DevelopmentConfig.SQLALCHEMY_DATABASE_URI

def test_production_config(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://user:pass@db:3306/sopz")
    monkeypatch.setenv("SECRET_KEY", "super-secret-prod-key")
    
    import config
    importlib.reload(config)
    
    assert config.ProductionConfig.DEBUG is False
    assert "mysql" in config.ProductionConfig.SQLALCHEMY_DATABASE_URI
    assert config.ProductionConfig.SESSION_COOKIE_SECURE is True
    assert config.ProductionConfig.SESSION_COOKIE_HTTPONLY is True

def test_testing_config():
    import config
    importlib.reload(config)
    assert config.TestingConfig.TESTING is True
    assert config.TestingConfig.WTF_CSRF_ENABLED is False
    assert config.TestingConfig.RATELIMIT_ENABLED is False
