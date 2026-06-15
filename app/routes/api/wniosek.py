from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import WniosekAlternatywny, ZalacznikSkan, Student, Praktyka, PotwierdzenieEfektow, PotwierdzenieEfektOcena, EfektUczenia, Uzytkownik, ZakladPracy
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error
from app.utils.upload import save_uploaded_file

wniosek_api_bp = Blueprint('wniosek_api', __name__)

def serialize_wniosek(w):
    skany_records = ZalacznikSkan.query.filter_by(wniosek_id=w.id).all()
    return {
        "id": w.id,
        "student_id": w.student_id,
        "typ": w.typ,
        "uzasadnienie": w.uzasadnienie,
        "opinia_komisji": w.opinia_komisji,
        "decyzja": w.decyzja,
        "status": w.status,
        "skany": [
            {
                "id": s.id,
                "nazwa_pliku": s.nazwa_pliku,
                "sciezka_pliku": s.sciezka_pliku,
                "typ_dokumentu": s.typ_dokumentu
            } for s in skany_records
        ],
        "created_at": w.created_at.strftime('%Y-%m-%d %H:%M:%S') if w.created_at else None,
        "updated_at": w.updated_at.strftime('%Y-%m-%d %H:%M:%S') if w.updated_at else None
    }

@wniosek_api_bp.route('/wniosek-zaliczenia', methods=['POST'])
@login_required
@role_required('student')
def create_wniosek():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta", status=400)

    # Read from multipart form
    typ = request.form.get('typ')
    uzasadnienie = request.form.get('uzasadnienie')

    if not typ or not uzasadnienie:
        return api_error("MISSING_FIELDS", "Brakujące pola typ lub uzasadnienie", status=400)

    if typ not in ['praca_zawodowa', 'staz', 'dzialalnosc_gospodarcza']:
        return api_error("INVALID_TYPE", "Nieprawidłowy typ wniosku", status=400)

    wniosek = WniosekAlternatywny(
        student_id=student.id,
        typ=typ,
        uzasadnienie=uzasadnienie,
        status='Submitted'
    )
    db.session.add(wniosek)
    db.session.flush()

    # Handle file uploads
    uploaded_files = request.files.getlist('skany') or request.files.getlist('files')
    # Per-file document types (aligned by index); fall back to single field then 'inny'
    typy_list = request.form.getlist('typ_dokumentu')
    allowed_td = ['umowa_o_prace', 'zakres_obowiazkow', 'ceidg', 'krs', 'inny']
    for idx, file in enumerate(uploaded_files):
        if file and file.filename != '':
            path, err = save_uploaded_file(file, 'wnioski')
            if err:
                db.session.rollback()
                return api_error("UPLOAD_ERROR", err, status=400)

            # Determine typ_dokumentu for this specific file
            td = typy_list[idx] if idx < len(typy_list) else (typy_list[0] if typy_list else 'inny')
            if td not in allowed_td:
                td = 'inny'

            skan = ZalacznikSkan(
                wniosek_id=wniosek.id,
                nazwa_pliku=file.filename,
                sciezka_pliku=path,
                typ_dokumentu=td
            )
            db.session.add(skan)

    db.session.commit()
    return api_success(serialize_wniosek(wniosek), status=201)

@wniosek_api_bp.route('/wniosek/<int:wniosek_id>', methods=['GET'])
@login_required
def get_wniosek(wniosek_id):
    w = WniosekAlternatywny.query.get_or_404(wniosek_id)

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or w.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        # UOPZ can see all alternative requests, or we could limit by uopz_id if needed.
        # But UOPZ supervises their own students. Let's make sure they can see it.
        pass

    return api_success(serialize_wniosek(w))

@wniosek_api_bp.route('/wniosek/<int:wniosek_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_wniosek(wniosek_id):
    w = WniosekAlternatywny.query.get_or_404(wniosek_id)
    data = request.get_json() or {}
    status = data.get('status')

    if status:
        if status not in ['Submitted', 'Under_Review', 'Approved', 'Rejected']:
            return api_error("INVALID_STATUS", "Nieprawidłowy status", status=400)
        w.status = status

    db.session.commit()
    return api_success(serialize_wniosek(w))

@wniosek_api_bp.route('/komisja/ocena', methods=['POST'])
@login_required
@role_required('dyrektor', 'administrator')
def evaluate_komisja():
    data = request.get_json() or {}
    wniosek_id = data.get('wniosek_id')
    opinia = data.get('opinia_komisji')
    decyzja = data.get('decyzja')
    oceny_data = data.get('oceny', [])

    if not wniosek_id or not opinia or not decyzja:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    if decyzja not in ['zgoda_pelna', 'zgoda_czesciowa', 'odmowa']:
        return api_error("INVALID_DECISION", "Nieprawidłowa decyzja", status=400)

    w = WniosekAlternatywny.query.get(wniosek_id)
    if not w:
        return api_error("WNIOSEK_NOT_FOUND", "Wniosek o podanym ID nie istnieje", status=404)

    w.opinia_komisji = opinia
    w.decyzja = decyzja
    w.status = 'Approved' if decyzja in ['zgoda_pelna', 'zgoda_czesciowa'] else 'Rejected'

    # If commission grades the 13 learning outcomes:
    if oceny_data:
        if len(oceny_data) != 13:
            return api_error("INVALID_EFFECTS_COUNT", "Należy ocenić dokładnie 13 efektów uczenia się", status=400)

        # Get or create practice for the student
        praktyka = Praktyka.query.filter_by(student_id=w.student_id).first()
        if not praktyka:
            # Create a practice to hold these outcome confirmations.
            # Do not assume fixed ids exist - resolve real records or fail clearly.
            student = Student.query.get(w.student_id)
            uopz_user = Uzytkownik.query.filter_by(rola='uopz').first()
            zaklad = ZakladPracy.query.filter_by(status='Approved').first() or ZakladPracy.query.first()
            if not uopz_user or not zaklad:
                db.session.rollback()
                return api_error(
                    "CANNOT_CREATE_PRAKTYKA",
                    "Brak dostępnego opiekuna uczelnianego (UOPZ) lub zakładu pracy do utworzenia praktyki zaliczeniowej",
                    status=400
                )
            from datetime import date
            today = date.today()
            praktyka = Praktyka(
                student_id=w.student_id,
                zaklad_id=zaklad.id,
                uopz_id=uopz_user.id,
                termin_od=today,
                termin_do=today,
                rok_akademicki=student.rok_akademicki,
                status='Approved'
            )
            db.session.add(praktyka)
            db.session.flush()

        pe = PotwierdzenieEfektow.query.filter_by(praktyka_id=praktyka.id).first()
        if not pe:
            pe = PotwierdzenieEfektow(
                praktyka_id=praktyka.id,
                godziny_zrealizowane=360,
                status='Approved'
            )
            db.session.add(pe)
            db.session.flush()
        else:
            pe.status = 'Approved'

        # Clear existing evaluations
        PotwierdzenieEfektOcena.query.filter_by(potwierdzenie_id=pe.id).delete()

        for o in oceny_data:
            nr = o.get('efekt_nr')
            uzyskano = o.get('uzyskano')
            efekt = EfektUczenia.query.filter_by(nr=nr).first()
            if efekt:
                ocena = PotwierdzenieEfektOcena(
                    potwierdzenie_id=pe.id,
                    efekt_id=efekt.id,
                    uzyskano=uzyskano
                )
                db.session.add(ocena)

    # Wygeneruj wniosek alternatywny (zal. 4b) po decyzji - wymaga praktyki jako kontekstu
    praktyka_dok = Praktyka.query.filter_by(student_id=w.student_id).first()
    if praktyka_dok:
        from app.routes.api.documents import generate_and_store
        generate_and_store(praktyka_dok, 'zal_nr4b')

    db.session.commit()
    return api_success(serialize_wniosek(w))
