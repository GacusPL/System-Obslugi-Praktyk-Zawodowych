from datetime import datetime
from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Praktyka, Student, ZakladPracy, Uzytkownik
from app.decorators import role_required
from app.validators import validate_dates_range
from app.routes.api.helpers import api_success, api_error, paginate_query

praktyki_api_bp = Blueprint('praktyki_api', __name__)

def serialize_praktyka(p):
    return {
        "id": p.id,
        "student_id": p.student_id,
        "zaklad_id": p.zaklad_id,
        "uopz_id": p.uopz_id,
        "termin_od": p.termin_od.strftime('%Y-%m-%d') if p.termin_od else None,
        "termin_do": p.termin_do.strftime('%Y-%m-%d') if p.termin_do else None,
        "rok_akademicki": p.rok_akademicki,
        "status": p.status,
        "ocena_koncowa": p.ocena_koncowa,
        "ankieta_wypelniona": p.ankieta_wypelniona,
        "dziennik_status": p.dziennik_status,
        "created_at": p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None,
        "updated_at": p.updated_at.strftime('%Y-%m-%d %H:%M:%S') if p.updated_at else None
    }

@praktyki_api_bp.route('/praktyki', methods=['POST'])
@login_required
@role_required('student')
def create_praktyka():
    # Find student profile
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta dla zalogowanego użytkownika", status=400)
        
    if student.semestr not in [6, 7]:
        return api_error("INVALID_SEMESTER", "Praktykę można zarejestrować tylko na 6 lub 7 semestrze", status=403)

    data = request.get_json() or {}
    zaklad_id = data.get('zaklad_id')
    uopz_id = data.get('uopz_id')
    termin_od_str = data.get('termin_od')
    termin_do_str = data.get('termin_do')
    rok_akademicki = data.get('rok_akademicki')

    if not all([zaklad_id, uopz_id, termin_od_str, termin_do_str, rok_akademicki]):
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    # Validate dates
    is_valid_dates, msg = validate_dates_range(termin_od_str, termin_do_str)
    if not is_valid_dates:
        return api_error("INVALID_DATES", msg, status=400)

    # Parse dates
    termin_od = datetime.strptime(termin_od_str, '%Y-%m-%d').date()
    termin_do = datetime.strptime(termin_do_str, '%Y-%m-%d').date()

    # Validate zaklad and uopz existence
    if not ZakladPracy.query.get(zaklad_id):
        return api_error("ZAKLAD_NOT_FOUND", "Zakład pracy o podanym ID nie istnieje", status=404)
        
    uopz_user = Uzytkownik.query.get(uopz_id)
    if not uopz_user or uopz_user.rola != 'uopz':
        return api_error("UOPZ_NOT_FOUND", "UOPZ o podanym ID nie istnieje", status=404)

    praktyka = Praktyka(
        student_id=student.id,
        zaklad_id=zaklad_id,
        uopz_id=uopz_id,
        termin_od=termin_od,
        termin_do=termin_do,
        rok_akademicki=rok_akademicki,
        status='Draft'
    )
    db.session.add(praktyka)
    db.session.commit()

    return api_success(serialize_praktyka(praktyka), status=201)

@praktyki_api_bp.route('/praktyki', methods=['GET'])
@login_required
def list_praktyki():
    query = Praktyka.query
    
    # Filter by user role
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student:
            return api_success([], meta={"total": 0})
        query = query.filter_by(student_id=student.id)
    elif current_user.rola == 'uopz':
        query = query.filter_by(uopz_id=current_user.id)
        
    # Query filters
    student_id = request.args.get('student_id', type=int)
    if student_id and current_user.rola != 'student':
        query = query.filter_by(student_id=student_id)
        
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
        
    rok_akademicki = request.args.get('rok_akademicki')
    if rok_akademicki:
        query = query.filter_by(rok_akademicki=rok_akademicki)
        
    # Sort
    sort_by = request.args.get('sort', '-created_at')
    if sort_by.startswith('-'):
        field_name = sort_by[1:]
        if hasattr(Praktyka, field_name):
            query = query.order_by(getattr(Praktyka, field_name).desc())
    else:
        if hasattr(Praktyka, sort_by):
            query = query.order_by(getattr(Praktyka, sort_by).asc())

    items, meta = paginate_query(query, serialize_fn=serialize_praktyka)
    return api_success(items, meta=meta)

@praktyki_api_bp.route('/praktyki/<int:praktyka_id>', methods=['GET'])
@login_required
def get_praktyka(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)
            
    return api_success(serialize_praktyka(praktyka))

@praktyki_api_bp.route('/praktyki/<int:praktyka_id>', methods=['PATCH'])
@praktyki_api_bp.route('/praktyki/<int:praktyka_id>/status', methods=['PATCH'])
@login_required
def update_praktyka_status(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    data = request.get_json() or {}
    new_status = data.get('status')
    
    if not new_status:
        return api_error("MISSING_STATUS", "Brak statusu w żądaniu", status=400)
        
    valid_transitions = {
        'Draft': ['Submitted'],
        'Submitted': ['Under_Review', 'Draft'],
        'Under_Review': ['Approved', 'Rejected'],
        'Approved': ['Closed', 'Under_Review'],
        'Rejected': ['Draft'],
        'Closed': []
    }
    
    current_status = praktyka.status
    if new_status not in valid_transitions.get(current_status, []):
        return api_error("INVALID_TRANSITION", f"Niedozwolone przejście stanu z {current_status} do {new_status}", status=400)

    # Permission check for transitions
    if current_user.rola == 'student':
        # Student can only submit a draft, or put rejected back to draft
        is_submit = (new_status == 'Submitted' and current_status == 'Draft')
        is_recall_or_edit = (new_status == 'Draft' and current_status == 'Rejected')
        if not (is_submit or is_recall_or_edit):
            abort(403)
    else:
        # non-students (uopz, administrator)
        if new_status == 'Submitted':
            abort(403)

    praktyka.status = new_status
    
    # Update other fields if provided and role matches
    if current_status == 'Draft' and current_user.rola == 'student':
        if 'termin_od' in data:
            praktyka.termin_od = datetime.strptime(data['termin_od'], '%Y-%m-%d').date()
        if 'termin_do' in data:
            praktyka.termin_do = datetime.strptime(data['termin_do'], '%Y-%m-%d').date()
        if 'rok_akademicki' in data:
            praktyka.rok_akademicki = data['rok_akademicki']
            
    if new_status == 'Closed' and 'ocena_koncowa' in data:
        if current_user.rola in ['uopz', 'administrator']:
            praktyka.ocena_koncowa = float(data['ocena_koncowa'])

    db.session.commit()
    return api_success(serialize_praktyka(praktyka))

@praktyki_api_bp.route('/praktyki/<int:praktyka_id>', methods=['DELETE'])
@login_required
@role_required('student')
def delete_praktyka(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student or praktyka.student_id != student.id:
        abort(403)
        
    if praktyka.status != 'Draft':
        return api_error("CANNOT_DELETE", "Można usuwać tylko praktyki o statusie Draft", status=400)
        
    db.session.delete(praktyka)
    db.session.commit()
    return api_success({"message": "Praktyka usunięta pomyślnie"})
