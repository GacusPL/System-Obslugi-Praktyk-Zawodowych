from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola is None:
        return redirect(url_for('auth.waiting'))
        
    template_map = {
        'student': 'dashboard/student.html',
        'zopz': 'dashboard/zopz.html',
        'uopz': 'dashboard/uopz.html',
        'administrator': 'dashboard/admin.html',
        'dyrektor': 'dashboard/dyrektor.html'
    }
    
    template_name = template_map.get(current_user.rola)
    if not template_name:
        # Fallback just in case
        return redirect(url_for('auth.waiting'))
        
    return render_template(template_name)
