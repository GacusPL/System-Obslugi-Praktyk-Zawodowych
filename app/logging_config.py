import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    # Ensure logs folder exists in the project root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Base logging format
    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s'
    )

    # Level configuration
    is_prod = os.environ.get('FLASK_ENV') == 'production' or not app.debug
    log_level = logging.WARNING if is_prod else logging.DEBUG

    # Application Log Handler
    app_log_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_log_handler.setFormatter(log_format)
    app_log_handler.setLevel(log_level)

    # Error Log Handler
    error_log_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_log_handler.setFormatter(log_format)
    error_log_handler.setLevel(logging.ERROR)

    # Register handlers
    app.logger.addHandler(app_log_handler)
    app.logger.addHandler(error_log_handler)
    app.logger.setLevel(log_level)

    app.logger.info("Logging configured successfully")
