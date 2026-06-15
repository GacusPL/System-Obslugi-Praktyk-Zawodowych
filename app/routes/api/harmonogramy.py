from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Harmonogram, HarmonogramDzial, Praktyka, Student, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

harmonogramy_api_bp = Blueprint('harmonogramy_api', __name__)

def serialize_harmonogram(h):
    return {
        "id": h.id,
        "praktyka_id": h.praktyka_id,
        "podpis_student": h.podpis_student,
        "podpis_zopz": h.podpis_zopz,
        "podpis_uopz": h.podpis_uopz,
        "status": h.status,
        "dzialy": [
            {
                "id": d.id,
                "nazwa_dzialu": d.nazwa_dzialu,
                "planowane_dni": d.planowane_dni
            } for d in h.dzialy
        ],
        "created_at": h.created_at.strftime('%Y-%m-%d %H:%M:%S') if h.created_at else None,
        "updated_at": h.updated_at.strftime('%Y-%m-%d %H:%M:%S') if h.updated_at else None
    }

@harmonogramy_api_bp.route('/harmonogramy', methods=['POST'])
@login_required
@role_required('uopz', 'administrator')
def create_harmonogram():
    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')
    dzialy_data = data.get('dzialy', [])

    if not praktyka_id or not dzialy_data:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka:
        return api_error("PRAKTYKA_NOT_FOUND", "Praktyka o podanym ID nie istnieje", status=404)

    # Check if harmonogram already exists for this practice
    existing = Harmonogram.query.filter_by(praktyka_id=praktyka_id).first()
    if existing:
        return api_error("HARMONOGRAM_ALREADY_EXISTS", "Harmonogram dla tej praktyki już istnieje", status=400)

    # Calculate total days
    total_days = sum(d.get('planowane_dni', 0) for d in dzialy_data)
    if total_days != 120:
        return api_error("INVALID_TOTAL_DAYS", f"Suma dni w harmonogramie wynosi {total_days} (wymagane 120)", status=400)

    harmonogram = Harmonogram(praktyka_id=praktyka_id, status='Draft')
    db.session.add(harmonogram)
    db.session.flush()  # to get harmonogram.id

    for d in dzialy_data:
        nazwa = d.get('nazwa_dzialu')
        dni = d.get('planowane_dni')
        if not nazwa or dni is None or dni <= 0:
            db.session.rollback()
            return api_error("INVALID_DIVISION", "Nieprawidłowe dane działu (nazwa i dni > 0 są wymagane)", status=400)
        
        dzial = HarmonogramDzial(
            harmonogram_id=harmonogram.id,
            nazwa_dzialu=nazwa,
            planowane_dni=dni
        )
        db.session.add(dzial)

    db.session.commit()
    return api_success(serialize_harmonogram(harmonogram), status=201)

@harmonogramy_api_bp.route('/harmonogramy/<int:praktyka_id>', methods=['GET'])
@login_required
def get_harmonogram(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)
    elif current_user.rola == 'zopz':
        if not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)

    harmonogram = Harmonogram.query.filter_by(praktyka_id=praktyka_id).first()
    if not harmonogram:
        return api_error("HARMONOGRAM_NOT_FOUND", "Harmonogram dla tej praktyki nie został utworzony", status=404)

    return api_success(serialize_harmonogram(harmonogram))

@harmonogramy_api_bp.route('/harmonogramy/<int:harmonogram_id>', methods=['PATCH'])
@login_required
@role_required('student', 'uopz', 'zopz', 'administrator')
def update_harmonogram(harmonogram_id):
    harmonogram = Harmonogram.query.get_or_404(harmonogram_id)
    praktyka = harmonogram.praktyka
    data = request.get_json() or {}

    # Access checks for signatures
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
        # Student can only update their own signature
        if any(k in data for k in ['podpis_zopz', 'podpis_uopz', 'status']):
            abort(403)
        if 'podpis_student' in data:
            harmonogram.podpis_student = int(data['podpis_student'])

    elif current_user.rola == 'zopz':
        if not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)
        # ZOPZ can only update their own signature
        if any(k in data for k in ['podpis_student', 'podpis_uopz', 'status']):
            abort(403)
        if 'podpis_zopz' in data:
            harmonogram.podpis_zopz = int(data['podpis_zopz'])

    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)
        # UOPZ can sign or update status if needed, but signature check
        if any(k in data for k in ['podpis_student', 'podpis_zopz']):
            abort(403)
        if 'podpis_uopz' in data:
            harmonogram.podpis_uopz = int(data['podpis_uopz'])
        if 'status' in data:
            new_status = data['status']
            if new_status not in ['Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected']:
                return api_error("INVALID_STATUS", "Nieprawidłowy status harmonogramu", status=400)
            harmonogram.status = new_status

    elif current_user.rola == 'administrator':
        # Admin can do anything
        if 'podpis_student' in data:
            harmonogram.podpis_student = int(data['podpis_student'])
        if 'podpis_zopz' in data:
            harmonogram.podpis_zopz = int(data['podpis_zopz'])
        if 'podpis_uopz' in data:
            harmonogram.podpis_uopz = int(data['podpis_uopz'])
        if 'status' in data:
            harmonogram.status = data['status']

    # If 3 signatures present, harmonogram is Approved. The praktyka itself is
    # only nudged from Draft into Under_Review - final praktyka approval stays an
    # explicit UOPZ decision (praktyki.py), so we never auto-Approve here.
    if harmonogram.podpis_student == 1 and harmonogram.podpis_zopz == 1 and harmonogram.podpis_uopz == 1:
        harmonogram.status = 'Approved'
        if praktyka.status == 'Draft':
            praktyka.status = 'Under_Review'

    db.session.commit()
    return api_success(serialize_harmonogram(harmonogram))

@harmonogramy_api_bp.route('/harmonogramy/<int:harmonogram_id>', methods=['PUT'])
@login_required
@role_required('student', 'uopz', 'administrator')
def save_harmonogram_divisions(harmonogram_id):
    harmonogram = Harmonogram.query.get_or_404(harmonogram_id)
    praktyka = harmonogram.praktyka
    
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
        # Student cannot update if already signed or approved
        if harmonogram.status not in ['Draft', 'Rejected'] or harmonogram.podpis_student:
            return api_error("NOT_EDITABLE", "Nie można edytować podpisanego lub zatwierdzonego harmonogramu", status=400)
    elif current_user.rola not in ['uopz', 'administrator']:
        abort(403)

    data = request.get_json() or {}
    dzialy_data = data.get('dzialy', [])
    if not dzialy_data:
        return api_error("MISSING_FIELDS", "Brakujące działy harmonogramu", status=400)

    # Calculate total days
    total_days = sum(int(d.get('planowane_dni', 0)) for d in dzialy_data)
    if total_days != 120:
        return api_error("INVALID_TOTAL_DAYS", f"Suma dni w harmonogramie wynosi {total_days} (wymagane 120)", status=400)

    # Delete existing divisions
    HarmonogramDzial.query.filter_by(harmonogram_id=harmonogram.id).delete()

    # Add new divisions
    for d in dzialy_data:
        nazwa = d.get('nazwa_dzialu')
        dni = int(d.get('planowane_dni', 0))
        if not nazwa or dni <= 0:
            db.session.rollback()
            return api_error("INVALID_DIVISION", "Nieprawidłowe dane działu (nazwa i dni > 0 są wymagane)", status=400)
        
        dzial = HarmonogramDzial(
            harmonogram_id=harmonogram.id,
            nazwa_dzialu=nazwa,
            planowane_dni=dni
        )
        db.session.add(dzial)

    db.session.commit()
    return api_success(serialize_harmonogram(harmonogram))

@harmonogramy_api_bp.route('/harmonogramy/<int:harmonogram_id>/signature', methods=['PATCH'])
@login_required
@role_required('student', 'uopz', 'zopz', 'administrator')
def sign_harmonogram(harmonogram_id):
    harmonogram = Harmonogram.query.get_or_404(harmonogram_id)
    praktyka = harmonogram.praktyka

    # Read role from request (can be in json, form, or args)
    req_role = None
    if request.is_json:
        req_role = request.get_json().get('rola')
    if not req_role:
        req_role = request.form.get('rola') or request.args.get('rola')

    if not req_role:
        return api_error("MISSING_ROLE", "Brak podanej roli do podpisu", status=400)

    # Permission checks and signing
    if req_role == 'student':
        if current_user.rola != 'student':
            abort(403)
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
        
        # Verify that sum of days is 120 before signing
        total_days = sum(d.planowane_dni for d in harmonogram.dzialy)
        if total_days != 120:
            return api_error("INVALID_TOTAL_DAYS", "Nie można podpisać harmonogramu z sumą dni inną niż 120", status=400)

        harmonogram.podpis_student = 1

    elif req_role == 'zopz':
        if current_user.rola != 'zopz':
            abort(403)
        if not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)
        harmonogram.podpis_zopz = 1

    elif req_role == 'uopz':
        if current_user.rola != 'uopz':
            abort(403)
        if praktyka.uopz_id != current_user.id:
            abort(403)
        harmonogram.podpis_uopz = 1

    else:
        return api_error("INVALID_ROLE", "Nieprawidłowa rola do podpisu", status=400)

    # If 3 signatures present, harmonogram is Approved. The praktyka itself is
    # only nudged from Draft into Under_Review - final praktyka approval stays an
    # explicit UOPZ decision (praktyki.py), so we never auto-Approve here.
    if harmonogram.podpis_student == 1 and harmonogram.podpis_zopz == 1 and harmonogram.podpis_uopz == 1:
        harmonogram.status = 'Approved'
        if praktyka.status == 'Draft':
            praktyka.status = 'Under_Review'

    db.session.commit()
    return api_success(serialize_harmonogram(harmonogram))
