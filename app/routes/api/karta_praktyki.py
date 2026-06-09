from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import KartaPraktyki, Praktyka, Student, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

karta_praktyki_api_bp = Blueprint('karta_praktyki_api', __name__)

def serialize_karta(k):
    return {
        "id": k.id,
        "praktyka_id": k.praktyka_id,
        "ocena_param_zopz": k.ocena_param_zopz,
        "ocena_opisowa_zopz": k.ocena_opisowa_zopz,
        "ocena_param_uopz": k.ocena_param_uopz,
        "ocena_opisowa_uopz": k.ocena_opisowa_uopz,
        "ocena_sprawozdania": k.ocena_sprawozdania,
        "status": k.status,
        "created_at": k.created_at.strftime('%Y-%m-%d %H:%M:%S') if k.created_at else None,
        "updated_at": k.updated_at.strftime('%Y-%m-%d %H:%M:%S') if k.updated_at else None
    }

@karta_praktyki_api_bp.route('/karta-praktyki/ocena', methods=['POST'])
@login_required
@role_required('zopz', 'administrator')
def evaluate_zopz():
    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')
    ocena_param = data.get('ocena_param_zopz') or data.get('ocena_param')
    ocena_opisowa = data.get('ocena_opisowa_zopz') or data.get('ocena_opisowa')

    if not praktyka_id or ocena_param is None or ocena_opisowa is None:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka:
        return api_error("PRAKTYKA_NOT_FOUND", "Praktyka o podanym ID nie istnieje", status=404)

    # Access checks
    if current_user.rola == 'zopz':
        if not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)

    try:
        val = float(ocena_param)
    except ValueError:
        return api_error("INVALID_OCENA_FORMAT", "Ocena musi być liczbą", status=400)

    if not (2.0 <= val <= 5.0):
        return api_error("INVALID_OCENA_RANGE", "Ocena musi być z zakresu 2.0 do 5.0", status=400)

    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka_id).first()
    if not karta:
        karta = KartaPraktyki(
            praktyka_id=praktyka_id,
            ocena_param_zopz=val,
            ocena_opisowa_zopz=ocena_opisowa,
            status='Under_Review'
        )
        db.session.add(karta)
    else:
        karta.ocena_param_zopz = val
        karta.ocena_opisowa_zopz = ocena_opisowa
        karta.status = 'Under_Review'

    db.session.commit()
    return api_success(serialize_karta(karta), status=201 if not karta.id else 200)

@karta_praktyki_api_bp.route('/karta-praktyki/<int:praktyka_id>', methods=['GET'])
@login_required
def get_karta(praktyka_id):
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

    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka_id).first()
    if not karta:
        return api_error("KARTA_NOT_FOUND", "Karta praktyki nie została jeszcze utworzona", status=404)

    return api_success(serialize_karta(karta))

@karta_praktyki_api_bp.route('/karta-praktyki/<int:karta_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_karta(karta_id):
    karta = KartaPraktyki.query.get_or_404(karta_id)
    praktyka = karta.praktyka

    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    ocena_param_uopz = data.get('ocena_param_uopz')
    ocena_opisowa_uopz = data.get('ocena_opisowa_uopz')
    ocena_sprawozdania = data.get('ocena_sprawozdania')
    status = data.get('status')

    if ocena_param_uopz is not None:
        try:
            val = float(ocena_param_uopz)
        except ValueError:
            return api_error("INVALID_OCENA", "Ocena UOPZ musi być liczbą", status=400)
        if not (2.0 <= val <= 5.0):
            return api_error("INVALID_OCENA_RANGE", "Ocena UOPZ musi być z zakresu 2.0 do 5.0", status=400)
        karta.ocena_param_uopz = val

    if ocena_sprawozdania is not None:
        try:
            val = float(ocena_sprawozdania)
        except ValueError:
            return api_error("INVALID_OCENA", "Ocena sprawozdania musi być liczbą", status=400)
        if not (2.0 <= val <= 5.0):
            return api_error("INVALID_OCENA_RANGE", "Ocena sprawozdania musi być z zakresu 2.0 do 5.0", status=400)
        karta.ocena_sprawozdania = val

    if ocena_opisowa_uopz is not None:
        karta.ocena_opisowa_uopz = ocena_opisowa_uopz

    if status:
        if status not in ['Draft', 'Under_Review', 'Approved', 'Closed']:
            return api_error("INVALID_STATUS", "Nieprawidłowy status karty praktyki", status=400)
        karta.status = status

    db.session.commit()
    return api_success(serialize_karta(karta))
