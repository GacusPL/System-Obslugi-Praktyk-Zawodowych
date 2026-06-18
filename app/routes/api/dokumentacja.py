from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Praktyka, Student, Harmonogram, KartaPraktyki, PotwierdzenieEfektow, WpisDziennika, Sprawozdanie, Uzytkownik
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

dokumentacja_api_bp = Blueprint('dokumentacja_api', __name__)

def check_checklist(praktyka):
    harmonogram = Harmonogram.query.filter_by(praktyka_id=praktyka.id).first()
    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka.id).first()
    efekty = PotwierdzenieEfektow.query.filter_by(praktyka_id=praktyka.id).first()
    sprawozdanie = Sprawozdanie.query.filter_by(praktyka_id=praktyka.id).order_by(Sprawozdanie.wersja.desc()).first()

    approved_days_count = WpisDziennika.query.filter_by(praktyka_id=praktyka.id, status='Approved').count()

    checklist = {
        "harmonogram_approved": harmonogram is not None and harmonogram.status == 'Approved',
        "karta_approved": karta is not None and karta.status == 'Approved',
        "efekty_approved": efekty is not None and efekty.status == 'Approved',
        "ankieta_complete": praktyka.ankieta_wypelniona == 1,
        "dziennik_complete": praktyka.dziennik_status == 'Closed' and approved_days_count == 120,
        "sprawozdanie_approved": sprawozdanie is not None and sprawozdanie.status == 'Approved'
    }
    return checklist

@dokumentacja_api_bp.route('/dokumentacja/checklist/<int:praktyka_id>', methods=['GET'])
@login_required
def get_checklist(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id != current_user.id:
            abort(403)

    checklist = check_checklist(praktyka)
    return api_success(checklist)

@dokumentacja_api_bp.route('/dokumentacja/zloz', methods=['POST'])
@login_required
@role_required('student')
def zloz_dokumentacje():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta", status=400)

    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')

    if not praktyka_id:
        return api_error("MISSING_PRAKTYKA_ID", "Brakujące ID praktyki", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka or praktyka.student_id != student.id:
        abort(403)

    # Komplet dokumentacji można złożyć tylko z praktyki w toku (zaakceptowane zgłoszenie)
    if praktyka.status != 'Approved':
        return api_error(
            "INVALID_PRACTICE_STATUS",
            "Dokumentację można złożyć tylko dla praktyki w toku (status Approved).",
            status=400
        )

    # Verify checklist
    checklist = check_checklist(praktyka)
    missing = [k for k, v in checklist.items() if not v]

    if missing:
        return api_error(
            "INCOMPLETE_DOCUMENTATION",
            "Nie można złożyć dokumentacji, ponieważ nie wszystkie elementy są zatwierdzone.",
            details={"missing_items": missing},
            status=422
        )

    # Złożenie kompletu dokumentacji uruchamia finalną weryfikację UOPZ
    praktyka.status = 'Under_Review'
    db.session.commit()

    return api_success({
        "praktyka_id": praktyka.id,
        "status": praktyka.status,
        "message": "Dokumentacja została złożona pomyślnie i oczekuje na weryfikację końcową."
    })

@dokumentacja_api_bp.route('/dokumentacja/<int:praktyka_id>/pelna', methods=['GET'])
@login_required
@role_required('uopz', 'administrator')
def get_pelna_dokumentacja(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    harmonogram = Harmonogram.query.filter_by(praktyka_id=praktyka.id).first()
    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka.id).first()
    efekty = PotwierdzenieEfektow.query.filter_by(praktyka_id=praktyka.id).first()
    sprawozdanie = Sprawozdanie.query.filter_by(praktyka_id=praktyka.id).order_by(Sprawozdanie.wersja.desc()).first()

    # Import helper serializers if needed
    from app.routes.api.harmonogramy import serialize_harmonogram
    from app.routes.api.karta_praktyki import serialize_karta
    from app.routes.api.efekty import serialize_potwierdzenie
    from app.routes.api.sprawozdanie import serialize_sprawozdanie

    return api_success({
        "praktyka_id": praktyka.id,
        "status": praktyka.status,
        "checklist": check_checklist(praktyka),
        "documents": {
            "harmonogram": serialize_harmonogram(harmonogram) if harmonogram else None,
            "karta_praktyki": serialize_karta(karta) if karta else None,
            "potwierdzenie_efektow": serialize_potwierdzenie(efekty) if efekty else None,
            "sprawozdanie": serialize_sprawozdanie(sprawozdanie) if sprawozdanie else None
        }
    })

@dokumentacja_api_bp.route('/dokumentacja/<int:praktyka_id>', methods=['PATCH'])
@login_required
@role_required('uopz', 'administrator')
def patch_dokumentacja(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    new_status = data.get('status') # Closed (zatwierdzenie) lub Approved (zwrot do poprawy)

    if not new_status:
        return api_error("MISSING_STATUS", "Brak statusu w żądaniu", status=400)

    # Finalna weryfikacja dokumentacji: praktyka jest w stanie Under_Review.
    #  - Under_Review -> Closed:   UOPZ zatwierdza całość (generujemy PDF-y)
    #  - Under_Review -> Approved: UOPZ zwraca dokumentację do poprawy
    valid_transitions = {
        'Under_Review': ['Closed', 'Approved'],
    }

    current_status = praktyka.status
    if new_status not in valid_transitions.get(current_status, []):
        return api_error("INVALID_TRANSITION", f"Niedozwolone przejście stanu z {current_status} do {new_status}", status=400)

    # Zwrot do poprawy może zawierać komentarz zwrotny
    if new_status == 'Approved':
        komentarz = (data.get('komentarz_odrzucenia') or '').strip()
        praktyka.komentarz_odrzucenia = komentarz or None

    praktyka.status = new_status

    if new_status == 'Closed':
        praktyka.komentarz_odrzucenia = None
        checklist = check_checklist(praktyka)
        if all(checklist.values()):
            from app.routes.api.documents import generate_and_store

            types_to_generate = ['zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr6', 'zal_nr7']
            if praktyka.egzaminy:
                types_to_generate.append('zal_nr8')
            for t in types_to_generate:
                generate_and_store(praktyka, t)

    db.session.commit()

    return api_success({
        "praktyka_id": praktyka.id,
        "status": praktyka.status,
        "message": f"Status praktyki zaktualizowany do {new_status}"
    })
