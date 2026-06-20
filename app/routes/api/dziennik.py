from datetime import datetime
from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import WpisDziennika, Praktyka, Student, EfektUczenia, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error, paginate_query, validate_payload
from app.validators import validate_wpis_date

dziennik_api_bp = Blueprint('dziennik_api', __name__)

def serialize_wpis(w):
    return {
        "id": w.id,
        "praktyka_id": w.praktyka_id,
        "dzien_nr": w.dzien_nr,
        "data_wpisu": w.data_wpisu.strftime('%Y-%m-%d') if w.data_wpisu else None,
        "opis_prac": w.opis_prac,
        "status": w.status,
        "komentarz_zopz": w.komentarz_zopz,
        "podpis_zopz": w.podpis_zopz,
        "efekty": [e.nr for e in w.efekty],
        "created_at": w.created_at.strftime('%Y-%m-%d %H:%M:%S') if w.created_at else None,
        "updated_at": w.updated_at.strftime('%Y-%m-%d %H:%M:%S') if w.updated_at else None
    }

@dziennik_api_bp.route('/dziennik/wpisy', methods=['POST'])
@login_required
@role_required('student')
def create_wpis():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta", status=400)

    data = request.get_json() or {}
    
    schema = {
        'praktyka_id': {'required': True, 'type': int},
        'dzien_nr': {'required': True, 'type': int},
        'data_wpisu': {'required': True, 'type': str},
        'opis_prac': {'required': True, 'type': str},
    }
    
    sanitized, errors = validate_payload(data, schema)
    if errors:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola lub nieprawidłowe typy", details=errors, status=400)

    praktyka_id = sanitized['praktyka_id']
    dzien_nr = sanitized['dzien_nr']
    data_wpisu_str = sanitized['data_wpisu']
    opis_prac = sanitized['opis_prac']
    efekty_nrs = data.get('efekty', [])
    entry_status = data.get('status', 'Submitted')

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka or praktyka.student_id != student.id:
        abort(403)

    if praktyka.status != 'Approved':
        return api_error("INVALID_PRACTICE_STATUS", "Nie można dodawać wpisów do praktyki, która nie została zaakceptowana (status musi być Approved)", status=400)

    if not (1 <= dzien_nr <= 120):
        return api_error("INVALID_DAY_NUMBER", "Numer dnia musi być z zakresu 1-120", status=400)

    # Check if entry already exists
    existing = WpisDziennika.query.filter_by(praktyka_id=praktyka_id, dzien_nr=dzien_nr).first()
    if existing:
        return api_error("ENTRY_ALREADY_EXISTS", f"Wpis dla dnia {dzien_nr} już istnieje", status=400)

    try:
        data_wpisu = datetime.strptime(data_wpisu_str, '%Y-%m-%d').date()
    except ValueError:
        return api_error("INVALID_DATE_FORMAT", "Nieprawidłowy format daty (wymagany YYYY-MM-DD)", status=400)

    ok, msg = validate_wpis_date(data_wpisu, praktyka.termin_od, praktyka.termin_do)
    if not ok:
        return api_error("INVALID_DATE_RANGE", msg, status=400)

    # Każdy wpis musi mieć unikalną datę w obrębie praktyki
    if WpisDziennika.query.filter_by(praktyka_id=praktyka_id, data_wpisu=data_wpisu).first():
        return api_error("DUPLICATE_DATE", f"Wpis z datą {data_wpisu_str} już istnieje w tym dzienniku", status=400)

    # Validate effects
    efekty = []
    for nr in efekty_nrs:
        efekt = EfektUczenia.query.filter_by(nr=nr).first()
        if not efekt:
            return api_error("EFEKT_NOT_FOUND", f"Efekt uczenia o numerze {nr} nie istnieje", status=400)
        efekty.append(efekt)

    wpis = WpisDziennika(
        praktyka_id=praktyka_id,
        dzien_nr=dzien_nr,
        data_wpisu=data_wpisu,
        opis_prac=opis_prac,
        status=entry_status
    )
    wpis.efekty = efekty

    db.session.add(wpis)
    db.session.commit()

    return api_success(serialize_wpis(wpis), status=201)

@dziennik_api_bp.route('/dziennik/<int:praktyka_id>', methods=['GET'])
@login_required
def list_wpisy(praktyka_id):
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

    query = WpisDziennika.query.filter_by(praktyka_id=praktyka_id)
    
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(WpisDziennika.dzien_nr.asc())

    items, meta = paginate_query(query, serialize_fn=serialize_wpis)
    return api_success(items, meta=meta)

@dziennik_api_bp.route('/dziennik/wpisy/<int:wpis_id>', methods=['PUT'])
@login_required
@role_required('student')
def update_wpis(wpis_id):
    wpis = WpisDziennika.query.get_or_404(wpis_id)
    praktyka = wpis.praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()

    if not student or praktyka.student_id != student.id:
        abort(403)

    if wpis.status not in ['Draft', 'Rejected']:
        return api_error("INVALID_STATUS_FOR_EDIT", "Można edytować tylko wpisy o statusie Draft lub Rejected", status=400)

    data = request.get_json() or {}
    opis_prac = data.get('opis_prac')
    data_wpisu_str = data.get('data_wpisu')
    efekty_nrs = data.get('efekty')
    entry_status = data.get('status', 'Submitted')

    if opis_prac is not None:
        wpis.opis_prac = opis_prac

    if data_wpisu_str is not None:
        try:
            nowa_data = datetime.strptime(data_wpisu_str, '%Y-%m-%d').date()
        except ValueError:
            return api_error("INVALID_DATE_FORMAT", "Nieprawidłowy format daty", status=400)
        ok, msg = validate_wpis_date(nowa_data, praktyka.termin_od, praktyka.termin_do)
        if not ok:
            return api_error("INVALID_DATE_RANGE", msg, status=400)
        dup = WpisDziennika.query.filter(
            WpisDziennika.praktyka_id == praktyka.id,
            WpisDziennika.data_wpisu == nowa_data,
            WpisDziennika.id != wpis.id
        ).first()
        if dup:
            return api_error("DUPLICATE_DATE", f"Wpis z datą {data_wpisu_str} już istnieje w tym dzienniku", status=400)
        wpis.data_wpisu = nowa_data

    if efekty_nrs is not None:
        efekty = []
        for nr in efekty_nrs:
            efekt = EfektUczenia.query.filter_by(nr=nr).first()
            if not efekt:
                return api_error("EFEKT_NOT_FOUND", f"Efekt uczenia o numerze {nr} nie istnieje", status=400)
            efekty.append(efekt)
        wpis.efekty = efekty

    wpis.status = entry_status
    db.session.commit()

    return api_success(serialize_wpis(wpis))

@dziennik_api_bp.route('/dziennik/wpisy/<int:wpis_id>', methods=['PATCH'])
@login_required
@role_required('student', 'uopz', 'zopz', 'administrator')
def patch_wpis(wpis_id):
    wpis = WpisDziennika.query.get_or_404(wpis_id)
    praktyka = wpis.praktyka
    data = request.get_json() or {}

    if 'status' in data and data['status'] not in ('Draft', 'Submitted', 'Approved', 'Rejected'):
        return api_error("INVALID_STATUS", "Nieprawidłowy status wpisu", status=400)

    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
        # Student can only submit a draft
        if 'status' in data and data['status'] == 'Submitted' and wpis.status == 'Draft':
            wpis.status = 'Submitted'
        else:
            abort(403)

    elif current_user.rola == 'zopz':
        if not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)

        new_status = data.get('status')
        if new_status not in ['Approved', 'Rejected']:
            return api_error("INVALID_STATUS", "ZOPZ może tylko zaakceptować (Approved) lub odrzucić (Rejected) wpis", status=400)

        wpis.status = new_status
        if 'komentarz_zopz' in data:
            wpis.komentarz_zopz = data['komentarz_zopz']

        if new_status == 'Approved':
            wpis.podpis_zopz = 1
        else:
            wpis.podpis_zopz = 0

        # Auto transition check: if 120 Approved days, set dziennik_status to Under_Review
        db.session.flush() # ensure status change is in session
        approved_count = WpisDziennika.query.filter_by(praktyka_id=praktyka.id, status='Approved').count()
        if approved_count == 120:
            praktyka.dziennik_status = 'Under_Review'

    elif current_user.rola in ['uopz', 'administrator']:
        if 'status' in data:
            wpis.status = data['status']
        if 'komentarz_zopz' in data:
            wpis.komentarz_zopz = data['komentarz_zopz']
        if 'podpis_zopz' in data:
            wpis.podpis_zopz = int(data['podpis_zopz'])

    db.session.commit()
    return api_success(serialize_wpis(wpis))

@dziennik_api_bp.route('/dziennik/<int:praktyka_id>/pelny', methods=['GET'])
@login_required
@role_required('uopz', 'administrator')
def get_pelny_dziennik(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    wpisy = WpisDziennika.query.filter_by(praktyka_id=praktyka_id).order_by(WpisDziennika.dzien_nr.asc()).all()
    return api_success([serialize_wpis(w) for w in wpisy])

@dziennik_api_bp.route('/dziennik/<int:praktyka_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_dziennik_status(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    new_status = data.get('dziennik_status')

    if new_status not in ['Draft', 'Under_Review', 'Closed', 'Rejected']:
        return api_error("INVALID_STATUS", "Nieprawidłowy status dziennika", status=400)

    praktyka.dziennik_status = new_status
    db.session.commit()

    return api_success({
        "praktyka_id": praktyka.id,
        "dziennik_status": praktyka.dziennik_status
    })
