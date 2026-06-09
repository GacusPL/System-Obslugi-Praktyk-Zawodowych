from functools import wraps
from flask import abort, redirect, url_for, request
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.rola is None:
                if request.path.startswith('/api/'):
                    abort(403)
                return redirect(url_for('auth.waiting'))
            if current_user.rola not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('administrator')(f)
