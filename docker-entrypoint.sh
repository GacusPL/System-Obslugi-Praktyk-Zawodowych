#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for database to start..."
python -c "
import socket
import time
import os
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
if db_url:
    url = urlparse(db_url)
    host = url.hostname
    port = url.port or 3306
    print(f'Connecting to {host}:{port}...')
    while True:
        try:
            s = socket.create_connection((host, port), timeout=1)
            s.close()
            print('Database is up!')
            break
        except Exception:
            print('Database is down, waiting...')
            time.sleep(2)
"

echo "Running database migrations..."
flask db upgrade

echo "Seeding initial data..."
flask seed

echo "Starting Gunicorn application..."
exec gunicorn -c gunicorn.conf.py run:app
