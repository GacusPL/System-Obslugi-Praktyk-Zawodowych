from datetime import datetime, date
from flask import Blueprint, request, abort, make_response
from flask_login import login_required, current_user
from app import db
from app.models import ZakladPracy, Praktyka, Student, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error, paginate_query
import csv
from io import StringIO

administracja_api_bp = Blueprint('administracja_api', __name__)

def serialize_zaklad(z):
    return {
        "id": z.id,
        "nazwa": z.nazwa,
        "adres": z.adres,
        "nip": z.nip,
        "zopz_imie": z.zopz_imie,
        "zopz_nazwisko": z.zopz_nazwisko,
        "zopz_stanowisko": z.zopz_stanowisko,
        "zopz_wyksztalcenie": z.zopz_wyksztalcenie,
        "status": z.status,
        "created_at": z.created_at.strftime('%Y-%m-%d %H:%M:%S') if z.created_at else None
    }

@administracja_api_bp.route('/zaklady', methods=['POST'])
@login_required
@role_required('administrator', 'uopz')
def create_zaklad():
    data = request.get_json() or {}
    nazwa = data.get('nazwa')
    adres = data.get('adres')
    nip = data.get('nip')
    zopz_imie = data.get('zopz_imie')
    zopz_nazwisko = data.get('zopz_nazwisko')
    zopz_stanowisko = data.get('zopz_stanowisko')
    zopz_wyksztalcenie = data.get('zopz_wyksztalcenie')

    if not all([nazwa, adres, nip, zopz_imie, zopz_nazwisko, zopz_stanowisko, zopz_wyksztalcenie]):
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    # Validate qualification §3 (higher education required)
    wyk = zopz_wyksztalcenie.lower()
    allowed_keywords = ['wyższe', 'wyzsze', 'inż', 'inz', 'mgr', 'dr', 'prof']
    if not any(k in wyk for k in allowed_keywords):
        return api_error("INVALID_ZOPZ_QUALIFICATION", "Opiekun praktyk (ZOPZ) musi posiadać wykształcenie wyższe lub inżynierskie", status=422)

    # Check NIP unique
    existing = ZakladPracy.query.filter_by(nip=nip).first()
    if existing:
        return api_error("ZAKLAD_ALREADY_EXISTS", "Zakład pracy o podanym NIP już istnieje", status=400)

    # Look up ZOPZ user to associate by name/surname
    zopz_user = Uzytkownik.query.filter_by(rola='zopz', imie=zopz_imie, nazwisko=zopz_nazwisko).first()
    zopz_uzytkownik_id = zopz_user.id if zopz_user else None

    zaklad = ZakladPracy(
        nazwa=nazwa,
        adres=adres,
        nip=nip,
        zopz_imie=zopz_imie,
        zopz_nazwisko=zopz_nazwisko,
        zopz_stanowisko=zopz_stanowisko,
        zopz_wyksztalcenie=zopz_wyksztalcenie,
        status='Approved',
        zopz_uzytkownik_id=zopz_uzytkownik_id
    )
    db.session.add(zaklad)
    db.session.commit()

    return api_success(serialize_zaklad(zaklad), status=201)

@administracja_api_bp.route('/zaklady', methods=['GET'])
@login_required
def list_zaklady():
    query = ZakladPracy.query
    items, meta = paginate_query(query, serialize_fn=serialize_zaklad)
    return api_success(items, meta=meta)

@administracja_api_bp.route('/przypisania', methods=['POST'])
@login_required
@role_required('administrator')
def assign_uopz():
    data = request.get_json() or {}
    uopz_id = data.get('uopz_id')
    studenci_ids = data.get('studenci_ids', [])

    if not uopz_id or not studenci_ids:
        return api_error("MISSING_FIELDS", "Brakujące uopz_id lub lista studenci_ids", status=400)

    uopz = Uzytkownik.query.get(uopz_id)
    if not uopz or uopz.rola != 'uopz':
        return api_error("INVALID_UOPZ", "Użytkownik nie istnieje lub nie ma roli UOPZ", status=400)

    # Update uopz_id in all active practices of the specified students.
    # Students without a practice cannot be linked here (UOPZ jest wybierany
    # przy zgloszeniu praktyki) - zwracamy ich jawnie zamiast cicho pomijac.
    practices = Praktyka.query.filter(Praktyka.student_id.in_(studenci_ids)).all()
    for p in practices:
        p.uopz_id = uopz_id

    students_with_practice = {p.student_id for p in practices}
    skipped = [sid for sid in studenci_ids if sid not in students_with_practice]

    db.session.commit()
    return api_success({
        "message": f"Przypisano opiekuna UOPZ do {len(practices)} praktyk",
        "assigned_count": len(practices),
        "skipped_students_without_practice": skipped
    })

@administracja_api_bp.route('/przedluzenie', methods=['POST'])
@login_required
@role_required('uopz', 'administrator')
def przedluz_praktyke():
    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')
    nowa_data_str = data.get('nowa_data_do')

    if not praktyka_id or not nowa_data_str:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka:
        return api_error("PRAKTYKA_NOT_FOUND", "Praktyka nie istnieje", status=404)

    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    try:
        nowa_data = datetime.strptime(nowa_data_str, '%Y-%m-%d').date()
    except ValueError:
        return api_error("INVALID_DATE_FORMAT", "Nieprawidłowy format nowej daty zakończenia", status=400)

    if nowa_data <= praktyka.termin_do:
        return api_error("INVALID_DATE", "Nowa data zakończenia musi być późniejsza niż dotychczasowa", status=400)

    # Validate difference (max 1 month = 31 days)
    delta = nowa_data - praktyka.termin_do
    if delta.days > 31:
        return api_error("EXTENSION_TOO_LONG", "Przedłużenie praktyki nie może przekraczać 1 miesiąca (31 dni)", status=400)

    praktyka.termin_do = nowa_data
    db.session.commit()

    return api_success({
        "praktyka_id": praktyka.id,
        "termin_do": praktyka.termin_do.strftime('%Y-%m-%d'),
        "message": "Praktyka została przedłużona pomyślnie."
    })

@administracja_api_bp.route('/raporty/stan-praktyk', methods=['GET'])
@login_required
@role_required('administrator', 'uopz')
def get_stan_praktyk():
    rok_ak = request.args.get('rok_ak')
    query = Praktyka.query
    if rok_ak:
        query = query.filter_by(rok_akademicki=rok_ak)

    practices = query.all()
    stats = {}
    for p in practices:
        stats[p.status] = stats.get(p.status, 0) + 1

    return api_success({
        "rok_akademicki": rok_ak,
        "statystyki": stats,
        "lacznie": len(practices)
    })

@administracja_api_bp.route('/raporty/eksport', methods=['GET'])
@login_required
@role_required('administrator', 'uopz')
def export_raport():
    rok_ak = request.args.get('rok_ak')
    query = Praktyka.query
    if rok_ak:
        query = query.filter_by(rok_akademicki=rok_ak)

    practices = query.all()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID Praktyki', 'Student', 'Zaklad Pracy', 'UOPZ', 'Status', 'Ocena Koncowa'])

    for p in practices:
        writer.writerow([
            p.id,
            f"{p.student.uzytkownik.imie} {p.student.uzytkownik.nazwisko} ({p.student.nr_albumu})",
            p.zaklad_pracy.nazwa,
            f"{p.uopz.imie} {p.uopz.nazwisko}" if p.uopz else "Brak",
            p.status,
            p.ocena_koncowa or "Brak"
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=raport_praktyk.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

@administracja_api_bp.route('/control/students', methods=['POST'])
@login_required
@role_required('student')
def create_student_profile():
    data = request.get_json() or {}
    uzytkownik_id = data.get('uzytkownik_id')
    nr_albumu = data.get('nr_albumu')
    kierunek = data.get('kierunek')
    specjalnosc = data.get('specjalnosc')
    semestr = data.get('semestr')
    forma_studiow = data.get('forma_studiow')
    rok_akademicki = data.get('rok_akademicki')

    # Ensure all required fields are present
    if not all([uzytkownik_id, nr_albumu, kierunek, semestr, forma_studiow, rok_akademicki]):
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    # Security check: User can only create profile for themselves
    if current_user.id != uzytkownik_id:
        abort(403)

    # Check if student profile already exists for this user
    existing_user_student = Student.query.filter_by(uzytkownik_id=uzytkownik_id).first()
    if existing_user_student:
        return api_error("STUDENT_ALREADY_EXISTS", "Profil studenta dla tego użytkownika już istnieje", status=400)

    # Check if student with this nr_albumu already exists
    existing_album_student = Student.query.filter_by(nr_albumu=nr_albumu).first()
    if existing_album_student:
        return api_error("ALBUM_NOT_UNIQUE", "Student o podanym numerze albumu już istnieje", status=400)

    # Validate semestr and forma_studiow
    if semestr not in [6, 7]:
        return api_error("INVALID_SEMESTER", "Semestr musi mieć wartość 6 lub 7", status=422)

    if forma_studiow not in ['stacjonarne', 'niestacjonarne']:
        return api_error("INVALID_FORMA_STUDIOW", "Forma studiów musi być 'stacjonarne' lub 'niestacjonarne'", status=422)

    student = Student(
        uzytkownik_id=uzytkownik_id,
        nr_albumu=nr_albumu,
        kierunek=kierunek,
        specjalnosc=specjalnosc,
        semestr=semestr,
        forma_studiow=forma_studiow,
        rok_akademicki=rok_akademicki
    )
    db.session.add(student)
    db.session.commit()

    return api_success({
        "id": student.id,
        "uzytkownik_id": student.uzytkownik_id,
        "nr_albumu": student.nr_albumu,
        "kierunek": student.kierunek,
        "specjalnosc": student.specjalnosc,
        "semestr": student.semestr,
        "forma_studiow": student.forma_studiow,
        "rok_akademicki": student.rok_akademicki
    }, status=201)

