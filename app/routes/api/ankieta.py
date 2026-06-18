from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Ankieta, AnkietaOdpowiedz, Praktyka, Student
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error

ankieta_api_bp = Blueprint('ankieta_api', __name__)

# 14 pytań ankiety zgodnych z oryginalnym Zał. 5 (kwestionariusz ANS Elbląg).
# Skala odpowiedzi 1-5: 5 = zdecydowanie tak ... 1 = zdecydowanie nie.
QUESTIONS = [
    {"nr": 1, "pytanie": "Poznałam/poznałem zasady funkcjonowania instytucji, w której odbywałam/odbywałem praktyki zawodowe."},
    {"nr": 2, "pytanie": "Poznałam/poznałem strukturę oraz regulamin organizacyjny instytucji, w której odbywałam/odbywałem praktyki zawodowe."},
    {"nr": 3, "pytanie": "Praktyki zawodowe umożliwiły mi pełną realizację ramowego programu praktyk zawodowych przewidzianego w ramach mojego kierunku studiów."},
    {"nr": 4, "pytanie": "Podczas praktyk zawodowych zwracano uwagę na przestrzeganie zasad etyki i tajemnicy zawodowej."},
    {"nr": 5, "pytanie": "Podczas praktyk miałam/miałem możliwość praktycznego zastosowania wiedzy teoretycznej zdobytej na zajęciach."},
    {"nr": 6, "pytanie": "Praktyki zawodowe przyczyniły się do pogłębienia mojej wiedzy i umiejętności zdobytych w trakcie studiów."},
    {"nr": 7, "pytanie": "Mogłem liczyć na wsparcie merytoryczne Opiekuna zakładowego praktyk."},
    {"nr": 8, "pytanie": "Mogłem liczyć na wsparcie merytoryczne Opiekuna uczelnianego praktyk."},
    {"nr": 9, "pytanie": "Opiekun zakładowy odpowiedzialny za praktyki zawodowe w miejscu ich odbywania potrafił prawidłowo zorganizować ich przebieg."},
    {"nr": 10, "pytanie": "Podczas praktyk zawodowych miałam/miałem możliwość pozyskiwania materiałów niezbędnych do przygotowania mojej pracy dyplomowej."},
    {"nr": 11, "pytanie": "Praktyki zawodowe rozwinęły moje umiejętności skutecznego komunikowania się w sytuacjach zawodowych i pracy w zespole."},
    {"nr": 12, "pytanie": "Praktyki zawodowe nauczyły mnie samodzielności i odpowiedzialności podczas wykonywania pracy."},
    {"nr": 13, "pytanie": "Liczba godzin realizowana w ramach praktyk zawodowych jest wystarczająca."},
    {"nr": 14, "pytanie": "Czy po zakończeniu praktyki zawodowej chciałaby/chciałby Pani/Pan współpracować z instytucją, w której Pani/Pan zrealizowała/zrealizował praktykę?"}
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

    if praktyka.status not in ('Approved', 'Closed'):
        return api_error("ANKIETA_TOO_EARLY", "Ankietę można wypełnić dopiero po zakończeniu praktyki", status=400)

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

    # Wygeneruj zal. 5 (ankieta) - dane czerpane z anonimowych metadanych
    from app.routes.api.documents import generate_and_store
    generate_and_store(praktyka, 'zal_nr5')

    db.session.commit()

    return api_success({"message": "Ankieta została zapisana pomyślnie. Dziękujemy!"}, status=201)
