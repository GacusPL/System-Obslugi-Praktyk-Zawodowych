from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Sprawozdanie, Praktyka, Student, Uzytkownik, KartaPraktyki
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error, validate_payload
from app.validators import validate_dziennik_completeness

sprawozdanie_api_bp = Blueprint('sprawozdanie_api', __name__)

def serialize_sprawozdanie(s):
    return {
        "id": s.id,
        "praktyka_id": s.praktyka_id,
        "sekcja_I": s.sekcja_I,
        "sekcja_II": s.sekcja_II,
        "sekcja_III": s.sekcja_III,
        "wersja": s.wersja,
        "ocena": s.ocena,
        "status": s.status,
        "komentarz_odrzucenia": s.komentarz_odrzucenia,
        "created_at": s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
        "updated_at": s.updated_at.strftime('%Y-%m-%d %H:%M:%S') if s.updated_at else None
    }

@sprawozdanie_api_bp.route('/sprawozdanie/szablon/<int:praktyka_id>', methods=['GET'])
@login_required
def get_sprawozdanie_szablon(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    return api_success({
        "praktyka_id": praktyka_id,
        "sekcja_I": "",
        "sekcja_II": "",
        "sekcja_III": ""
    })

@sprawozdanie_api_bp.route('/sprawozdanie', methods=['POST'])
@login_required
@role_required('student')
def create_sprawozdanie():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta", status=400)

    data = request.get_json() or {}
    schema = {
        'praktyka_id': {'required': True, 'type': int},
        'sekcja_I': {'required': False, 'type': str},
        'sekcja_II': {'required': False, 'type': str},
        'sekcja_III': {'required': False, 'type': str},
        'status': {'required': False, 'type': str},
    }
    sanitized, errors = validate_payload(data, schema)
    if errors:
        return api_error("MISSING_PRAKTYKA_ID", "Brakujące ID praktyki", details=errors, status=400)

    praktyka_id = sanitized['praktyka_id']
    sekcja_I = sanitized.get('sekcja_I') or ''
    sekcja_II = sanitized.get('sekcja_II') or ''
    sekcja_III = sanitized.get('sekcja_III') or ''
    status = sanitized.get('status') or 'Submitted'

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka or praktyka.student_id != student.id:
        abort(403)

    # Sprawozdanie można wysłać dopiero po wypełnieniu dziennika (120 zatwierdzonych dni)
    if status == 'Submitted':
        ok, msg = validate_dziennik_completeness(praktyka_id)
        if not ok:
            return api_error("DZIENNIK_INCOMPLETE", f"Sprawozdanie można złożyć dopiero po wypełnieniu dziennika. {msg}", status=400)

    # Check if sprawozdanie already exists
    existing = Sprawozdanie.query.filter_by(praktyka_id=praktyka_id).first()
    if existing:
        return api_error("SPRAWOZDANIE_ALREADY_EXISTS", "Sprawozdanie dla tej praktyki już istnieje. Użyj PUT, aby je edytować.", status=400)

    # Check length (only if submitting, wait, let's enforce it always or if status == Submitted?
    # Usually we can save Draft with shorter text, but let's check: "Walidacja min 100 znaków per sekcja"
    # Let's enforce the check if they try to save/submit)
    if status == 'Submitted' or len(sekcja_I) > 0 or len(sekcja_II) > 0 or len(sekcja_III) > 0:
        if len(sekcja_I) < 100 or len(sekcja_II) < 100 or len(sekcja_III) < 100:
            return api_error("SECTION_TOO_SHORT", "Każda sekcja sprawozdania musi mieć minimum 100 znaków", status=400)

    sprawozdanie = Sprawozdanie(
        praktyka_id=praktyka_id,
        sekcja_I=sekcja_I,
        sekcja_II=sekcja_II,
        sekcja_III=sekcja_III,
        status=status,
        wersja=1
    )
    db.session.add(sprawozdanie)
    db.session.commit()

    return api_success(serialize_sprawozdanie(sprawozdanie), status=201)

@sprawozdanie_api_bp.route('/sprawozdanie/<int:sprawozdanie_id>', methods=['GET'])
@login_required
def get_sprawozdanie(sprawozdanie_id):
    s = Sprawozdanie.query.get_or_404(sprawozdanie_id)
    praktyka = s.praktyka

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    return api_success(serialize_sprawozdanie(s))

@sprawozdanie_api_bp.route('/sprawozdanie/praktyka/<int:praktyka_id>', methods=['GET'])
@login_required
def get_sprawozdanie_by_praktyka(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    s = Sprawozdanie.query.filter_by(praktyka_id=praktyka_id).first()
    if not s:
        return api_error("SPRAWOZDANIE_NOT_FOUND", "Sprawozdanie nie zostało jeszcze utworzone", status=404)

    return api_success(serialize_sprawozdanie(s))

@sprawozdanie_api_bp.route('/sprawozdanie/<int:sprawozdanie_id>', methods=['PUT'])
@login_required
@role_required('student')
def update_sprawozdanie(sprawozdanie_id):
    s = Sprawozdanie.query.get_or_404(sprawozdanie_id)
    praktyka = s.praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()

    if not student or praktyka.student_id != student.id:
        abort(403)

    if s.status not in ['Draft', 'Rejected']:
        return api_error("INVALID_STATUS_FOR_EDIT", "Można edytować tylko sprawozdania o statusie Draft lub Rejected", status=400)

    data = request.get_json() or {}
    schema = {
        'sekcja_I': {'required': False, 'type': str},
        'sekcja_II': {'required': False, 'type': str},
        'sekcja_III': {'required': False, 'type': str},
        'status': {'required': False, 'type': str},
    }
    sanitized, errors = validate_payload(data, schema)
    if errors:
        return api_error("VALIDATION_ERROR", "Błędy walidacji danych", details=errors, status=400)

    sekcja_I = sanitized.get('sekcja_I') or s.sekcja_I
    sekcja_II = sanitized.get('sekcja_II') or s.sekcja_II
    sekcja_III = sanitized.get('sekcja_III') or s.sekcja_III
    status = sanitized.get('status') or 'Submitted'

    if len(sekcja_I) < 100 or len(sekcja_II) < 100 or len(sekcja_III) < 100:
        return api_error("SECTION_TOO_SHORT", "Każda sekcja sprawozdania musi mieć minimum 100 znaków", status=400)

    # Ponowne złożenie dopiero po wypełnieniu dziennika (120 zatwierdzonych dni)
    if status == 'Submitted':
        ok, msg = validate_dziennik_completeness(praktyka.id)
        if not ok:
            return api_error("DZIENNIK_INCOMPLETE", f"Sprawozdanie można złożyć dopiero po wypełnieniu dziennika. {msg}", status=400)

    s.sekcja_I = sekcja_I
    s.sekcja_II = sekcja_II
    s.sekcja_III = sekcja_III
    s.status = status
    s.wersja += 1
    # Ponowne przesłanie czyści poprzedni komentarz odrzucenia
    s.komentarz_odrzucenia = None

    db.session.commit()
    return api_success(serialize_sprawozdanie(s))

@sprawozdanie_api_bp.route('/sprawozdanie/<int:sprawozdanie_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_sprawozdanie(sprawozdanie_id):
    s = Sprawozdanie.query.get_or_404(sprawozdanie_id)
    praktyka = s.praktyka

    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    schema = {
        'status': {'required': False, 'type': str},
        'ocena': {'required': False, 'type': float},
    }
    sanitized, errors = validate_payload(data, schema)
    if errors:
        return api_error("VALIDATION_ERROR", "Błędy walidacji danych", details=errors, status=400)
    status = sanitized.get('status')
    ocena = sanitized.get('ocena')

    if status:
        if status not in ['Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected']:
            return api_error("INVALID_STATUS", "Nieprawidłowy status", status=400)
        if status == 'Rejected':
            komentarz = (data.get('komentarz_odrzucenia') or '').strip()
            if not komentarz:
                return api_error("MISSING_COMMENT", "Odrzucenie sprawozdania wymaga podania komentarza zwrotnego", status=400)
            s.komentarz_odrzucenia = komentarz
        s.status = status

    if ocena is not None:
        try:
            ocena_val = float(ocena)
        except ValueError:
            return api_error("INVALID_OCENA", "Ocena musi być liczbą", status=400)
        if not (2.0 <= ocena_val <= 5.0):
            return api_error("INVALID_OCENA_RANGE", "Ocena musi być w zakresie 2.0 - 5.0", status=400)
        s.ocena = ocena_val

    # Zatwierdzone sprawozdanie z oceną przenosi ocenę do karty praktyki (P6)
    if s.status == 'Approved' and s.ocena is not None:
        karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka.id).first()
        if not karta:
            karta = KartaPraktyki(praktyka_id=praktyka.id, ocena_sprawozdania=s.ocena)
            db.session.add(karta)
        else:
            karta.ocena_sprawozdania = s.ocena

    db.session.commit()
    return api_success(serialize_sprawozdanie(s))
