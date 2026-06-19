from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Uzytkownik, Student
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

VALID_ROLES = ['student', 'zopz', 'uopz', 'administrator', 'dyrektor']

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def users_list():
    # List users without roles, and also list all users for admin convenience
    pending_users = Uzytkownik.query.filter(Uzytkownik.rola.is_(None)).all()
    all_users = Uzytkownik.query.all()
    return render_template('admin/users.html', pending_users=pending_users, all_users=all_users)

def _user_form_data(form):
    return {
        'imie': (form.get('imie') or '').strip(),
        'nazwisko': (form.get('nazwisko') or '').strip(),
        'email': (form.get('email') or '').strip(),
        'rola': (form.get('rola') or '').strip(),
        'nr_albumu': (form.get('nr_albumu') or '').strip(),
        'kierunek': (form.get('kierunek') or '').strip(),
        'specjalnosc': (form.get('specjalnosc') or '').strip(),
        'semestr': (form.get('semestr') or '').strip(),
        'forma_studiow': (form.get('forma_studiow') or '').strip(),
        'rok_akademicki': (form.get('rok_akademicki') or '').strip(),
    }

def _has_student_profile_data(data):
    """Czy admin wprowadził jakiekolwiek dane profilu studenta."""
    return any(data[k] for k in ('nr_albumu', 'kierunek', 'specjalnosc', 'semestr', 'forma_studiow', 'rok_akademicki'))

def _validate_student_profile(data, errors, exclude_student_id=None):
    if not (data['nr_albumu'] and data['kierunek'] and data['semestr'] and data['forma_studiow'] and data['rok_akademicki']):
        errors.append("Dla studenta wymagane są: nr albumu, kierunek, semestr, forma studiów, rok akademicki.")
    if data['semestr'] and data['semestr'] not in ('6', '7'):
        errors.append("Semestr musi wynosić 6 lub 7.")
    if data['forma_studiow'] and data['forma_studiow'] not in ('stacjonarne', 'niestacjonarne'):
        errors.append("Forma studiów musi być 'stacjonarne' lub 'niestacjonarne'.")
    if data['nr_albumu']:
        q = Student.query.filter_by(nr_albumu=data['nr_albumu'])
        if exclude_student_id:
            q = q.filter(Student.id != exclude_student_id)
        if q.first():
            errors.append("Student z tym numerem albumu już istnieje.")

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'GET':
        return render_template('admin/user_form.html', mode='create',
                               action_url=url_for('admin.create_user'), data={}, roles=VALID_ROLES)

    data = _user_form_data(request.form)
    haslo = request.form.get('haslo') or ''
    errors = []

    if not (data['imie'] and data['nazwisko'] and data['email']):
        errors.append("Imię, nazwisko i email są wymagane.")
    if data['rola'] and data['rola'] not in VALID_ROLES:
        errors.append("Nieprawidłowa rola.")
    if not haslo:
        errors.append("Hasło jest wymagane przy tworzeniu konta.")
    if data['email'] and Uzytkownik.query.filter_by(email=data['email']).first():
        errors.append("Użytkownik z tym adresem email już istnieje.")
    # Profil studenta jest opcjonalny - student może go uzupełnić sam po zalogowaniu
    has_profile = _has_student_profile_data(data)
    if data['rola'] == 'student' and has_profile:
        _validate_student_profile(data, errors)

    if errors:
        for e in errors:
            flash(e, "danger")
        return render_template('admin/user_form.html', mode='create',
                               action_url=url_for('admin.create_user'), data=data, roles=VALID_ROLES)

    user = Uzytkownik(imie=data['imie'], nazwisko=data['nazwisko'], email=data['email'],
                      rola=data['rola'] or None)
    user.set_password(haslo)
    db.session.add(user)
    db.session.flush()

    if data['rola'] == 'student' and has_profile:
        db.session.add(Student(
            uzytkownik_id=user.id, nr_albumu=data['nr_albumu'], kierunek=data['kierunek'],
            specjalnosc=data['specjalnosc'] or None, semestr=int(data['semestr']),
            forma_studiow=data['forma_studiow'], rok_akademicki=data['rok_akademicki']
        ))

    db.session.commit()
    flash(f"Utworzono użytkownika {user.email}.", "success")
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = Uzytkownik.query.get_or_404(user_id)
    student = Student.query.filter_by(uzytkownik_id=user.id).first()

    if request.method == 'GET':
        data = {
            'imie': user.imie, 'nazwisko': user.nazwisko, 'email': user.email,
            'rola': user.rola or '',
            'nr_albumu': student.nr_albumu if student else '',
            'kierunek': student.kierunek if student else '',
            'specjalnosc': student.specjalnosc if student else '',
            'semestr': str(student.semestr) if student else '',
            'forma_studiow': student.forma_studiow if student else '',
            'rok_akademicki': student.rok_akademicki if student else '',
        }
        return render_template('admin/user_form.html', mode='edit',
                               action_url=url_for('admin.edit_user', user_id=user.id), data=data, roles=VALID_ROLES)

    data = _user_form_data(request.form)
    haslo = request.form.get('haslo') or ''
    errors = []

    if not (data['imie'] and data['nazwisko'] and data['email']):
        errors.append("Imię, nazwisko i email są wymagane.")
    if data['rola'] and data['rola'] not in VALID_ROLES:
        errors.append("Nieprawidłowa rola.")
    if data['email'] and Uzytkownik.query.filter(Uzytkownik.email == data['email'], Uzytkownik.id != user.id).first():
        errors.append("Inny użytkownik z tym adresem email już istnieje.")
    # Profil studenta jest opcjonalny - walidujemy tylko gdy podano dane
    has_profile = _has_student_profile_data(data)
    if data['rola'] == 'student' and has_profile:
        _validate_student_profile(data, errors, exclude_student_id=student.id if student else None)

    if errors:
        for e in errors:
            flash(e, "danger")
        return render_template('admin/user_form.html', mode='edit',
                               action_url=url_for('admin.edit_user', user_id=user.id), data=data, roles=VALID_ROLES)

    user.imie = data['imie']
    user.nazwisko = data['nazwisko']
    user.email = data['email']
    user.rola = data['rola'] or None
    if haslo:
        user.set_password(haslo)

    if data['rola'] == 'student' and has_profile:
        if student:
            student.nr_albumu = data['nr_albumu']
            student.kierunek = data['kierunek']
            student.specjalnosc = data['specjalnosc'] or None
            student.semestr = int(data['semestr'])
            student.forma_studiow = data['forma_studiow']
            student.rok_akademicki = data['rok_akademicki']
        else:
            db.session.add(Student(
                uzytkownik_id=user.id, nr_albumu=data['nr_albumu'], kierunek=data['kierunek'],
                specjalnosc=data['specjalnosc'] or None, semestr=int(data['semestr']),
                forma_studiow=data['forma_studiow'], rok_akademicki=data['rok_akademicki']
            ))

    db.session.commit()
    flash(f"Zaktualizowano użytkownika {user.email}.", "success")
    return redirect(url_for('admin.users_list'))

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
        return redirect(request.referrer or url_for('admin.users_list')), 400

    user.rola = new_role
    db.session.commit()

    if request.headers.get('HX-Request'):
        return ""

    flash(f"Przypisano rolę {new_role} użytkownikowi {user.email}.", "success")
    return redirect(request.referrer or url_for('admin.users_list'))

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

@admin_bp.route('/praktyki/<int:praktyka_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_praktyka(praktyka_id):
    from app.models import Praktyka
    p = Praktyka.query.get_or_404(praktyka_id)
    p.archived = True
    db.session.commit()
    flash("Praktyka została zarchiwizowana (dane zachowane).", "success")
    return redirect(url_for('admin.praktyki_list'))

@admin_bp.route('/praktyki/<int:praktyka_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_praktyka(praktyka_id):
    from app.models import Praktyka
    p = Praktyka.query.get_or_404(praktyka_id)
    p.archived = False
    db.session.commit()
    flash("Praktyka została przywrócona z archiwum.", "success")
    return redirect(url_for('admin.praktyki_list'))

@admin_bp.route('/zaklady/<int:zaklad_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_zaklad(zaklad_id):
    from app.models import ZakladPracy
    z = ZakladPracy.query.get_or_404(zaklad_id)
    z.archived = True
    db.session.commit()
    flash("Zakład pracy został zarchiwizowany.", "success")
    return redirect(url_for('admin.zaklady_manage'))

@admin_bp.route('/zaklady/<int:zaklad_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_zaklad(zaklad_id):
    from app.models import ZakladPracy
    z = ZakladPracy.query.get_or_404(zaklad_id)
    z.archived = False
    db.session.commit()
    flash("Zakład pracy został przywrócony z archiwum.", "success")
    return redirect(url_for('admin.zaklady_manage'))

@admin_bp.route('/users/<int:user_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_user(user_id):
    user = Uzytkownik.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Nie możesz zarchiwizować własnego konta.", "danger")
        return redirect(url_for('admin.users_list'))
    user.archived = True
    db.session.commit()
    flash(f"Konto {user.email} zostało zarchiwizowane.", "success")
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/<int:user_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_user(user_id):
    user = Uzytkownik.query.get_or_404(user_id)
    user.archived = False
    db.session.commit()
    flash(f"Konto {user.email} zostało przywrócone z archiwum.", "success")
    return redirect(url_for('admin.users_list'))

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

