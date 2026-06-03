from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import PotwierdzenieEfektow, PotwierdzenieEfektOcena, Praktyka, Student, EfektUczenia, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

efekty_api_bp = Blueprint('efekty_api', __name__)

def serialize_potwierdzenie(pe):
    return {
        "id": pe.id,
        "praktyka_id": pe.praktyka_id,
        "godziny_zrealizowane": pe.godziny_zrealizowane,
        "opinia_uopz": pe.opinia_uopz,
        "status": pe.status,
        "oceny": [
            {
                "efekt_nr": o.efekt.nr,
                "uzyskano": o.uzyskano
            } for o in pe.oceny
        ],
        "created_at": pe.created_at.strftime('%Y-%m-%d %H:%M:%S') if pe.created_at else None,
        "updated_at": pe.updated_at.strftime('%Y-%m-%d %H:%M:%S') if pe.updated_at else None
    }

@efekty_api_bp.route('/efekty/szablon/<int:praktyka_id>', methods=['GET'])
@login_required
def get_efekty_szablon(praktyka_id):
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
        if praktyka.zaklad_pracy.zopz_imie != current_user.imie or praktyka.zaklad_pracy.zopz_nazwisko != current_user.nazwisko:
            abort(403)

    efekty = EfektUczenia.query.order_by(EfektUczenia.nr.asc()).all()
    return api_success([
        {
            "id": e.id,
            "nr": e.nr,
            "opis": e.opis
        } for e in efekty
    ])

@efekty_api_bp.route('/efekty/potwierdzenie', methods=['POST'])
@login_required
@role_required('zopz', 'administrator')
def create_potwierdzenie():
    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')
    godziny = data.get('godziny_zrealizowane')
    oceny_data = data.get('oceny', [])

    if not praktyka_id or godziny is None or not oceny_data:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka:
        return api_error("PRAKTYKA_NOT_FOUND", "Praktyka o podanym ID nie istnieje", status=404)

    # Access check for ZOPZ
    if current_user.rola == 'zopz':
        if praktyka.zaklad_pracy.zopz_imie != current_user.imie or praktyka.zaklad_pracy.zopz_nazwisko != current_user.nazwisko:
            abort(403)

    # Check if already exists
    existing = PotwierdzenieEfektow.query.filter_by(praktyka_id=praktyka_id).first()
    if existing:
        return api_error("CONFIRMATION_ALREADY_EXISTS", "Potwierdzenie efektów dla tej praktyki już istnieje", status=400)

    # Validate 13 effects
    if len(oceny_data) != 13:
        return api_error("INVALID_EFFECTS_COUNT", f"Należy ocenić dokładnie 13 efektów (przesłano {len(oceny_data)})", status=400)

    # Validate each effect unique nr 1..13
    nrs = [o.get('efekt_nr') for o in oceny_data]
    if len(set(nrs)) != 13 or any(nr is None or not (1 <= nr <= 13) for nr in nrs):
        return api_error("INVALID_EFFECTS_LIST", "Lista efektów musi zawierać unikalne numery od 1 do 13", status=400)

    pe = PotwierdzenieEfektow(
        praktyka_id=praktyka_id,
        godziny_zrealizowane=godziny,
        status='Submitted'
    )
    db.session.add(pe)
    db.session.flush()

    for o in oceny_data:
        nr = o.get('efekt_nr')
        uzyskano = o.get('uzyskano')
        if uzyskano not in [0, 1]:
            db.session.rollback()
            return api_error("INVALID_OCENA_VALUE", "Wartość uzyskano musi wynosić 0 lub 1", status=400)

        efekt = EfektUczenia.query.filter_by(nr=nr).first()
        ocena = PotwierdzenieEfektOcena(
            potwierdzenie_id=pe.id,
            efekt_id=efekt.id,
            uzyskano=uzyskano
        )
        db.session.add(ocena)

    db.session.commit()
    return api_success(serialize_potwierdzenie(pe), status=201)

@efekty_api_bp.route('/efekty/potwierdzenie/<int:praktyka_id>', methods=['GET'])
@login_required
def get_potwierdzenie(praktyka_id):
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
        if praktyka.zaklad_pracy.zopz_imie != current_user.imie or praktyka.zaklad_pracy.zopz_nazwisko != current_user.nazwisko:
            abort(403)

    pe = PotwierdzenieEfektow.query.filter_by(praktyka_id=praktyka_id).first()
    if not pe:
        return api_error("CONFIRMATION_NOT_FOUND", "Potwierdzenie efektów nie zostało jeszcze utworzone", status=404)

    return api_success(serialize_potwierdzenie(pe))

@efekty_api_bp.route('/efekty/potwierdzenie/<int:potwierdzenie_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_potwierdzenie(potwierdzenie_id):
    pe = PotwierdzenieEfektow.query.get_or_404(potwierdzenie_id)
    praktyka = pe.praktyka

    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    status = data.get('status')
    opinia_uopz = data.get('opinia_uopz')

    if status:
        if status not in ['Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected']:
            return api_error("INVALID_STATUS", "Nieprawidłowy status", status=400)
        pe.status = status

    if opinia_uopz is not None:
        pe.opinia_uopz = opinia_uopz

    db.session.commit()
    return api_success(serialize_potwierdzenie(pe))
