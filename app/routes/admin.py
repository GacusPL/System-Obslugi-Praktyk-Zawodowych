from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app import db
from app.models import Uzytkownik
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def users_list():
    # List users without roles, and also list all users for admin convenience
    pending_users = Uzytkownik.query.filter(Uzytkownik.rola.is_(None)).all()
    all_users = Uzytkownik.query.all()
    return render_template('admin/users.html', pending_users=pending_users, all_users=all_users)

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = Uzytkownik.query.get_or_404(user_id)
    new_role = request.form.get('rola')
    
    valid_roles = ['student', 'zopz', 'uopz', 'administrator', 'dyrektor']
    if new_role not in valid_roles:
        flash("Nieprawidłowa rola.", "danger")
        return redirect(url_for('admin.users_list')), 400
        
    user.rola = new_role
    db.session.commit()
    flash(f"Przypisano rolę {new_role} użytkownikowi {user.email}.", "success")
    return redirect(url_for('admin.users_list'))
