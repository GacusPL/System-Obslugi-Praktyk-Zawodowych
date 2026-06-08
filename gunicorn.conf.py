import os

# Gunicorn configuration file
bind = "0.0.0.0:8000"
workers = 4
timeout = 120
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "warning"
