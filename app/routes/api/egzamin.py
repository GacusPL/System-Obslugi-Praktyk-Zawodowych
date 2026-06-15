import csv
from io import BytesIO, StringIO
from datetime import datetime
from flask import Blueprint, request, abort, make_response, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Egzamin, KomisjaCzlonek, Praktyka, Student, Uzytkownik, KartaPraktyki
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error, validate_payload
import openpyxl

egzamin_api_bp = Blueprint('egzamin_api', __name__)

def serialize_egzamin(e):
    return {
        "id": e.id,
        "praktyka_id": e.praktyka_id,
        "termin": e.termin.strftime('%Y-%m-%d %H:%M:%S') if e.termin else None,
        "ocena_ustna": e.ocena_ustna,
        "ocena_koncowa": e.ocena_koncowa,
        "status": e.status,
        "komisja": [
            {
                "uzytkownik_id": c.uzytkownik_id,
                "imie": c.uzytkownik.imie,
                "nazwisko": c.uzytkownik.nazwisko,
                "rola_w_komisji": c.rola_w_komisji
            } for c in e.komisja
        ]
    }

@egzamin_api_bp.route('/egzamin', methods=['POST'])
@login_required
@role_required('administrator', 'uopz')
def create_egzamin():
    data = request.get_json() or {}
    schema = {
        'praktyka_id': {'required': True, 'type': int},
        'termin': {'required': True, 'type': str},
    }
    sanitized, errors = validate_payload(data, schema)
    if errors or 'komisja_sklad' not in data or not data['komisja_sklad']:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", details=errors, status=400)

    praktyka_id = sanitized['praktyka_id']
    termin_str = sanitized['termin']
    komisja_sklad = data['komisja_sklad']

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka:
        return api_error("PRAKTYKA_NOT_FOUND", "Praktyka o podanym ID nie istnieje", status=404)

    try:
        termin = datetime.strptime(termin_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            termin = datetime.strptime(termin_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                termin = datetime.strptime(termin_str, '%Y-%m-%d %H:%M')
            except ValueError:
                return api_error("INVALID_DATE_FORMAT", "Nieprawidłowy format daty (wymagany YYYY-MM-DD HH:MM:SS)", status=400)

    # Check if there's already an active/draft exam for this practice
    existing = Egzamin.query.filter_by(praktyka_id=praktyka_id, status='Draft').first()
    if existing:
        return api_error("EXAM_ALREADY_EXISTS", "Dla tej praktyki istnieje już zaplanowany egzamin (Draft)", status=400)

    egzamin = Egzamin(
        praktyka_id=praktyka_id,
        termin=termin,
        status='Draft'
    )
    db.session.add(egzamin)
    db.session.flush()

    for member in komisja_sklad:
        u_id = member.get('uzytkownik_id')
        rola = member.get('rola_w_komisji')
        
        if not u_id or rola not in ['przewodniczacy', 'czlonek']:
            db.session.rollback()
            return api_error("INVALID_MEMBER_DATA", "Nieprawidłowe dane członka komisji", status=400)

        user = Uzytkownik.query.get(u_id)
        if not user or user.rola not in ['uopz', 'dyrektor', 'administrator']:
            db.session.rollback()
            return api_error("USER_NOT_ELIGIBLE", f"Użytkownik o ID {u_id} nie może być członkiem komisji", status=400)

        czlonek = KomisjaCzlonek(
            egzamin_id=egzamin.id,
            uzytkownik_id=u_id,
            rola_w_komisji=rola
        )
        db.session.add(czlonek)

    db.session.commit()
    return api_success(serialize_egzamin(egzamin), status=201)

@egzamin_api_bp.route('/egzamin/<int:egzamin_id>', methods=['GET'])
@login_required
def get_egzamin(egzamin_id):
    e = Egzamin.query.get_or_404(egzamin_id)
    praktyka = e.praktyka

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    return api_success(serialize_egzamin(e))

@egzamin_api_bp.route('/egzamin/<int:egzamin_id>/protokol', methods=['GET'])
@login_required
def get_protokol(egzamin_id):
    e = Egzamin.query.get_or_404(egzamin_id)
    praktyka = e.praktyka

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka.id).first()
    
    return api_success({
        "egzamin_id": e.id,
        "student": {
            "imie": praktyka.student.uzytkownik.imie,
            "nazwisko": praktyka.student.uzytkownik.nazwisko,
            "nr_albumu": praktyka.student.nr_albumu
        },
        "oceny_czastkowe": {
            "ocena_zopz": karta.ocena_param_zopz if karta else None,
            "ocena_uopz": karta.ocena_param_uopz if karta else None,
            "ocena_sprawozdania": karta.ocena_sprawozdania if karta else None
        },
        "ocena_ustna": e.ocena_ustna,
        "ocena_koncowa": e.ocena_koncowa,
        "status": e.status
    })

@egzamin_api_bp.route('/egzamin/<int:egzamin_id>/wynik', methods=['POST'])
@login_required
@role_required('administrator', 'uopz')
def submit_egzamin_wynik(egzamin_id):
    e = Egzamin.query.get_or_404(egzamin_id)
    praktyka = e.praktyka

    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    schema = {
        'ocena_ustna': {'required': True, 'type': float},
        'ocena_koncowa': {'required': True, 'type': float},
    }
    sanitized, errors = validate_payload(data, schema)
    if errors:
        return api_error("MISSING_GRADES", "Brak oceny ustnej lub oceny końcowej", details=errors, status=400)
    ou = sanitized['ocena_ustna']
    ok = sanitized['ocena_koncowa']

    for g in [ou, ok]:
        if not (2.0 <= g <= 5.0):
            return api_error("INVALID_GRADE_RANGE", "Oceny muszą być z przedziału 2.0 - 5.0", status=400)

    e.ocena_ustna = ou
    e.ocena_koncowa = ok

    if ok == 2.0:
        e.status = 'Rejected'
        # Practice remains in Under_Review or Rejected so they can schedule a retake
        praktyka.status = 'Rejected'
    else:
        e.status = 'Approved'
        praktyka.status = 'Closed'
        praktyka.ocena_koncowa = ok

    # Wygeneruj protokol egzaminu (zal. 8) niezaleznie od wyniku
    from app.routes.api.documents import generate_and_store
    generate_and_store(praktyka, 'zal_nr8')

    db.session.commit()
    return api_success(serialize_egzamin(e))

@egzamin_api_bp.route('/eksport/oceny', methods=['GET'])
@login_required
@role_required('administrator', 'uopz')
def export_oceny():
    rok_ak = request.args.get('rok_ak')
    fmt = request.args.get('format', 'xlsx').lower()

    query = Praktyka.query.filter_by(status='Closed')
    if rok_ak:
        query = query.filter_by(rok_akademicki=rok_ak)

    practices = query.all()

    if fmt == 'csv':
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Nr albumu', 'Nazwisko', 'Imie', 'Kierunek', 'Rok akademicki', 'Ocena koncowa'])
        for p in practices:
            writer.writerow([
                p.student.nr_albumu,
                p.student.uzytkownik.nazwisko,
                p.student.uzytkownik.imie,
                p.student.kierunek,
                p.rok_akademicki,
                p.ocena_koncowa
            ])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=oceny_usos.csv"
        output.headers["Content-type"] = "text/csv; charset=utf-8"
        return output

    else:
        # XLSX export using openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Oceny USOS"

        # Headers
        ws.append(['Nr albumu', 'Nazwisko', 'Imie', 'Kierunek', 'Rok akademicki', 'Ocena koncowa'])

        for p in practices:
            ws.append([
                p.student.nr_albumu,
                p.student.uzytkownik.nazwisko,
                p.student.uzytkownik.imie,
                p.student.kierunek,
                p.rok_akademicki,
                p.ocena_koncowa
            ])

        out = BytesIO()
        wb.save(out)
        out.seek(0)

        return send_file(
            out,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="oceny_usos.xlsx"
        )
