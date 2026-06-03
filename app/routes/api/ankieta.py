from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Ankieta, AnkietaOdpowiedz, Praktyka, Student
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

ankieta_api_bp = Blueprint('ankieta_api', __name__)

# List of 14 questions representing evaluation criteria
QUESTIONS = [
    {"nr": 1, "pytanie": "Jak oceniasz zgodność realizowanych zadań z programem praktyk?"},
    {"nr": 2, "pytanie": "Jak oceniasz organizację praktyk ze strony zakładu pracy?"},
    {"nr": 3, "pytanie": "Jak oceniasz opiekę merytoryczną ze strony opiekuna w zakładzie pracy?"},
    {"nr": 4, "pytanie": "Jak oceniasz warunki pracy (miejsce, sprzęt, bezpieczeństwo)?"},
    {"nr": 5, "pytanie": "Jak oceniasz atmosferę panującą w zespole/zakładzie pracy?"},
    {"nr": 6, "pytanie": "W jakim stopniu praktyka pozwoliła Ci na wykorzystanie wiedzy teoretycznej?"},
    {"nr": 7, "pytanie": "W jakim stopniu praktyka pozwoliła Ci rozwinąć umiejętności praktyczne?"},
    {"nr": 8, "pytanie": "W jakim stopniu praktyka ułatwi Ci start na rynku pracy?"},
    {"nr": 9, "pytanie": "Jak oceniasz kontakt i pomoc ze strony koordynatora praktyk uczelni (UOPZ)?"},
    {"nr": 10, "pytanie": "Jak oceniasz sprawność procedur administracyjnych związanych z praktykami?"},
    {"nr": 11, "pytanie": "Jak oceniasz przydatność dziennika praktyk w dokumentowaniu pracy?"},
    {"nr": 12, "pytanie": "Czy polecił(a)byś ten zakład pracy innym studentom na praktyki?"},
    {"nr": 13, "pytanie": "Jak oceniasz ogólny poziom zadowolenia z odbytych praktyk?"},
    {"nr": 14, "pytanie": "Jak oceniasz wsparcie ze strony uczelni przy poszukiwaniu miejsca praktyk?"}
]

@ankieta_api_bp.route('/ankieta/szablon', methods=['GET'])
@login_required
def get_ankieta_szablon():
    return api_success(QUESTIONS)

@ankieta_api_bp.route('/ankieta', methods=['POST'])
@login_required
@role_required('student')
def create_ankieta():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return api_error("STUDENT_PROFILE_NOT_FOUND", "Brak profilu studenta", status=400)

    data = request.get_json() or {}
    praktyka_id = data.get('praktyka_id')
    odpowiedzi_data = data.get('odpowiedzi', [])
    uwagi = data.get('uwagi', '')

    if not praktyka_id or not odpowiedzi_data:
        return api_error("MISSING_FIELDS", "Brakujące wymagane pola", status=400)

    praktyka = Praktyka.query.get(praktyka_id)
    if not praktyka or praktyka.student_id != student.id:
        abort(403)

    if praktyka.ankieta_wypelniona == 1:
        return api_error("ANKIETA_ALREADY_SUBMITTED", "Ankieta dla tej praktyki została już wypełniona", status=400)

    if len(odpowiedzi_data) != 14:
        return api_error("INVALID_ANSWERS_COUNT", f"Należy odpowiedzieć na dokładnie 14 pytań (przesłano {len(odpowiedzi_data)})", status=400)

    # Validate scale 1-5 and unique question numbers
    nrs = [o.get('pytanie_nr') for o in odpowiedzi_data]
    if len(set(nrs)) != 14 or any(nr is None or not (1 <= nr <= 14) for nr in nrs):
        return api_error("INVALID_QUESTIONS_LIST", "Lista odpowiedzi musi zawierać unikalne numery pytań od 1 do 14", status=400)

    # Create anonymous Ankieta record using metadata from student's profile
    # Note: no student_id or praktyka_id is stored in Ankieta table to preserve absolute anonymity!
    ankieta = Ankieta(
        rok_akademicki=student.rok_akademicki,
        kierunek=student.kierunek,
        forma_studiow=student.forma_studiow,
        semestr=student.semestr,
        godziny=360, # Standard length of internship in hours (e.g. 360 hours for 6 months/120 days)
        uwagi=uwagi
    )
    db.session.add(ankieta)
    db.session.flush()

    for o in odpowiedzi_data:
        nr = o.get('pytanie_nr')
        val = o.get('odpowiedz')
        if val is None or not (1 <= val <= 5):
            db.session.rollback()
            return api_error("INVALID_ANSWER_VALUE", f"Odpowiedź na pytanie {nr} musi wynosić od 1 do 5", status=400)

        odp = AnkietaOdpowiedz(
            ankieta_id=ankieta.id,
            pytanie_nr=nr,
            odpowiedz=val
        )
        db.session.add(odp)

    # Mark the student's practice as having the survey completed
    praktyka.ankieta_wypelniona = 1
    db.session.commit()

    return api_success({"message": "Ankieta została zapisana pomyślnie. Dziękujemy!"}, status=201)
