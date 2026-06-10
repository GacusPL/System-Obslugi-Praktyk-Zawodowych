from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
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
    
    if request.is_json:
        data = request.get_json() or {}
        new_role = data.get('rola')
    else:
        new_role = request.form.get('rola')
    
    valid_roles = ['student', 'zopz', 'uopz', 'administrator', 'dyrektor']
    if new_role not in valid_roles:
        if request.headers.get('HX-Request') or request.is_json:
            return {"error": "INVALID_ROLE", "message": "Nieprawidłowa rola"}, 400
        flash("Nieprawidłowa rola.", "danger")
        return redirect(url_for('admin.users_list')), 400
        
    user.rola = new_role
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        return ""
        
    flash(f"Przypisano rolę {new_role} użytkownikowi {user.email}.", "success")
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/praktyki', methods=['GET'])
@login_required
@admin_required
def praktyki_list():
    from app.models import Praktyka
    praktyki = Praktyka.query.all()
    return render_template('admin/praktyki.html', praktyki=praktyki)

@admin_bp.route('/egzamin/<int:egzamin_id>/protokol', methods=['GET'])
@login_required
def view_egzamin_protokol(egzamin_id):
    from app.models import Egzamin
    egzamin = Egzamin.query.get_or_404(egzamin_id)
    praktyka = egzamin.praktyka
    
    # Access checks
    if current_user.rola == 'student':
        from app.models import Student
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)
    elif current_user.rola == 'zopz':
        abort(403)

    return render_template('egzamin/protokol.html', egzamin=egzamin, praktyka=praktyka)

@admin_bp.route('/egzamin/create/<int:praktyka_id>', methods=['GET'])
@login_required
@admin_required
def schedule_egzamin_form(praktyka_id):
    from app.models import Praktyka, Uzytkownik
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    
    # Allowed commission members: uopz, dyrektor, administrator
    commission_candidates = Uzytkownik.query.filter(Uzytkownik.rola.in_(['uopz', 'dyrektor', 'administrator'])).all()
    
    return render_template('egzamin/create.html', praktyka=praktyka, commission_candidates=commission_candidates)

@admin_bp.route('/zaklady', methods=['GET'])
@login_required
@admin_required
def zaklady_manage():
    from app.models import ZakladPracy
    zaklady = ZakladPracy.query.all()
    return render_template('admin/zaklady.html', zaklady=zaklady)

@admin_bp.route('/raporty', methods=['GET'])
@login_required
@admin_required
def raporty_view():
    from app.models import Praktyka
    from sqlalchemy import func
    
    stats = db.session.query(Praktyka.status, func.count(Praktyka.id)).group_by(Praktyka.status).all()
    stats_dict = {status: count for status, count in stats}
    
    years = db.session.query(Praktyka.rok_akademicki).distinct().all()
    years = [y[0] for y in years if y[0]]
    
    return render_template('admin/raporty.html', stats=stats_dict, years=years)

@admin_bp.route('/przypisania', methods=['GET'])
@login_required
@admin_required
def przypisania_uopz_view():
    from app.models import Praktyka, Uzytkownik
    uopz_list = Uzytkownik.query.filter_by(rola='uopz').all()
    praktyki = Praktyka.query.all()
    return render_template('admin/przypisania.html', uopz_list=uopz_list, praktyki=praktyki)

@admin_bp.route('/przedluzenie/<int:praktyka_id>', methods=['GET'])
@login_required
def przedluzenie_view(praktyka_id):
    from app.models import Praktyka
    from datetime import timedelta
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)
    elif current_user.rola not in ['uopz', 'administrator']:
        abort(403)
    max_data_do = praktyka.termin_do + timedelta(days=31)
    return render_template('admin/przedluzenie.html', praktyka=praktyka, max_data_do=max_data_do)

@admin_bp.route('/egzaminy', methods=['GET'])
@login_required
@admin_required
def egzaminy_list():
    from app.models import Egzamin
    egzaminy = Egzamin.query.all()
    return render_template('admin/egzaminy.html', egzaminy=egzaminy)

@admin_bp.route('/eksport', methods=['GET'])
@login_required
@admin_required
def eksport_view():
    from app.models import Praktyka
    from app import db
    years = db.session.query(Praktyka.rok_akademicki).distinct().all()
    years = [y[0] for y in years if y[0]]
    return render_template('admin/eksport.html', years=years)

