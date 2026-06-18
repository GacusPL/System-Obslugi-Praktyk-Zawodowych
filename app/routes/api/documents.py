from flask import Blueprint, send_file, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Dokument, Praktyka, Student, ZakladPracy, Uzytkownik, Sprawozdanie, KartaPraktyki
from app.decorators import role_required
from app.routes.api.helpers import api_success, api_error
from app.pdf import generate_pdf
import os

documents_api_bp = Blueprint('documents_api', __name__)

def compile_pdf_data(praktyka, typ):
    student = praktyka.student
    student_user = student.uzytkownik
    uopz_user = praktyka.uopz
    zaklad = praktyka.zaklad_pracy

    data = {
        'praktyka_id': praktyka.id,
        'student_name': f"{student_user.imie} {student_user.nazwisko}",
        'nr_albumu': student.nr_albumu,
        'kierunek': student.kierunek,
        'specjalnosc': student.specjalnosc,
        'semestr': student.semestr,
        'forma_studiow': student.forma_studiow,
        'zaklad_nazwa': zaklad.nazwa,
        'uopz_name': f"{uopz_user.imie} {uopz_user.nazwisko}" if uopz_user else "-",
        'termin_od': praktyka.termin_od.strftime('%Y-%m-%d') if praktyka.termin_od else "",
        'termin_do': praktyka.termin_do.strftime('%Y-%m-%d') if praktyka.termin_do else "",
        'rok_akademicki': praktyka.rok_akademicki,
    }

    if typ == 'zal_nr2a':
        harmonogram = praktyka.harmonogram
        data['dzialy'] = [{
            'nazwa_dzialu': d.nazwa_dzialu,
            'planowane_dni': d.planowane_dni
        } for d in harmonogram.dzialy] if harmonogram else []
        data['program'] = [{
            'efekt_nr': p.efekt.nr,
            'efekt_opis': p.efekt.opis,
            'opis_realizacji': p.opis_realizacji
        } for p in sorted(harmonogram.program_pozycje, key=lambda x: x.efekt.nr)] if harmonogram else []
        data['podpis_student'] = harmonogram.podpis_student if harmonogram else False
        data['podpis_zopz'] = harmonogram.podpis_zopz if harmonogram else False
        data['podpis_uopz'] = harmonogram.podpis_uopz if harmonogram else False

    elif typ == 'zal_nr3':
        karta = praktyka.karta_praktyki
        data.update({
            'porozumienie_nr': praktyka.id,
            'ocena_param_zopz': karta.ocena_param_zopz if karta else None,
            'ocena_opisowa_zopz': karta.ocena_opisowa_zopz if karta else "",
            'ocena_param_uopz': karta.ocena_param_uopz if karta else None,
            'ocena_opisowa_uopz': karta.ocena_opisowa_uopz if karta else "",
            'ocena_sprawozdania': karta.ocena_sprawozdania if karta else None,
            'ocena_koncowa': praktyka.ocena_koncowa,
        })

    elif typ == 'zal_nr4':
        potwierdzenie = praktyka.potwierdzenie_efektow
        data['godziny_zrealizowane'] = potwierdzenie.godziny_zrealizowane if potwierdzenie else 960
        data['opinia_uopz'] = potwierdzenie.opinia_uopz if potwierdzenie else ""
        
        from app.models import EfektUczenia
        efekty_list = EfektUczenia.query.order_by(EfektUczenia.nr).all()
        ratings = []
        for e in efekty_list:
            uzyskano = False
            if potwierdzenie:
                for o in potwierdzenie.oceny:
                    if o.efekt_id == e.id:
                        uzyskano = bool(o.uzyskano)
                        break
            ratings.append({
                'nr': e.nr,
                'opis': e.opis,
                'uzyskano': uzyskano
            })
        data['efekty'] = ratings

    elif typ == 'zal_nr4b':
        wniosek = student.wnioski_alternatywne[-1] if student.wnioski_alternatywne else None
        if wniosek:
            data.update({
                'typ': wniosek.typ,
                'uzasadnienie': wniosek.uzasadnienie,
                'decyzja': wniosek.decyzja,
                'opinia_komisji': wniosek.opinia_komisji,
                'zalaczniki': [z.nazwa_pliku for z in wniosek.skany]
            })

    elif typ == 'zal_nr5':
        from app.models import Ankieta
        ankieta = Ankieta.query.filter_by(
            kierunek=student.kierunek,
            forma_studiow=student.forma_studiow,
            rok_akademicki=praktyka.rok_akademicki
        ).order_by(Ankieta.created_at.desc()).first()
        
        if ankieta:
            data.update({
                'godziny': ankieta.godziny,
                'uwagi': ankieta.uwagi,
                'odpowiedzi': [{
                    'pytanie_nr': o.pytanie_nr,
                    'odpowiedz': o.odpowiedz
                } for o in ankieta.odpowiedzi]
            })
        else:
            data.update({
                'godziny': '960',
                'uwagi': '',
                'odpowiedzi': []
            })

    elif typ == 'zal_nr6':
        wpisy = praktyka.wpisy_dziennika
        data['wpisy'] = [{
            'dzien_nr': w.dzien_nr,
            'data_wpisu': w.data_wpisu.strftime('%Y-%m-%d'),
            'opis_prac': w.opis_prac,
            'status': w.status,
            'efekty': [e.nr for e in w.efekty]
        } for w in wpisy]

    elif typ == 'zal_nr7':
        sprawozdanie = praktyka.sprawozdania[-1] if praktyka.sprawozdania else None
        if sprawozdanie:
            data.update({
                'sekcja_I': sprawozdanie.sekcja_I,
                'sekcja_II': sprawozdanie.sekcja_II,
                'sekcja_III': sprawozdanie.sekcja_III
            })

    elif typ == 'zal_nr8':
        egzamin = praktyka.egzaminy[-1] if praktyka.egzaminy else None
        if egzamin:
            data.update({
                'data_egzaminu': egzamin.termin.strftime('%Y-%m-%d'),
                'ocena_ustna': egzamin.ocena_ustna,
                'ocena_koncowa': egzamin.ocena_koncowa,
                'komisja': [{
                    'imie': c.uzytkownik.imie,
                    'nazwisko': c.uzytkownik.nazwisko,
                    'rola_w_komisji': c.rola_w_komisji
                } for c in egzamin.komisja]
            })

    return data

def generate_and_store(praktyka, typ):
    """Generate a PDF attachment and upsert its Dokument record.
    Returns the Dokument or None on failure (errors are swallowed and logged)."""
    try:
        pdf_data = compile_pdf_data(praktyka, typ)
        filepath = generate_pdf(typ, pdf_data)
        doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ=typ).first()
        if not doc:
            doc = Dokument(praktyka_id=praktyka.id, typ=typ, sciezka_pliku=filepath, status='Closed')
            db.session.add(doc)
        else:
            doc.sciezka_pliku = filepath
        return doc
    except Exception as e:
        print(f"Error generating PDF {typ} for praktyka {praktyka.id}: {e}")
        return None

@documents_api_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@login_required
def download_document(doc_id):
    doc = Dokument.query.get_or_404(doc_id)
    praktyka = doc.praktyka

    # Ownership checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or (praktyka and praktyka.student_id != student.id):
            abort(403)
    elif current_user.rola == 'uopz':
        if praktyka and praktyka.uopz_id != current_user.id:
            abort(403)
    elif current_user.rola == 'zopz':
        if praktyka and not praktyka.zaklad_pracy.is_opiekun(current_user):
            abort(403)

    # Resolve path: generated PDFs are stored absolute, uploaded scans relative to app/static
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    paths_to_try = [
        doc.sciezka_pliku,
        os.path.join(base_dir, 'app', 'static', doc.sciezka_pliku),
        os.path.join(base_dir, 'app', doc.sciezka_pliku),
        os.path.join(base_dir, doc.sciezka_pliku),
    ]
    abs_path = next((p for p in paths_to_try if os.path.exists(p)), None)
    if not abs_path:
        abort(404)

    return send_file(abs_path, as_attachment=True)

@documents_api_bp.route('/documents/generate', methods=['POST'])
@login_required
@role_required('student', 'uopz', 'zopz', 'administrator')
def generate_document_api():
    data_json = request.get_json() or {}
    praktyka_id = data_json.get('praktyka_id')
    typ = data_json.get('typ')

    if not praktyka_id or not typ:
        return api_error("MISSING_PARAMS", "Praktyka_id oraz typ są wymagane", status=400)

    praktyka = Praktyka.query.get_or_404(praktyka_id)

    # Ownership checks
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

    # Compile data and generate PDF
    pdf_data = compile_pdf_data(praktyka, typ)
    filepath = generate_pdf(typ, pdf_data)

    # Insert or update in database
    doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ=typ).first()
    if not doc:
        doc = Dokument(praktyka_id=praktyka.id, typ=typ, sciezka_pliku=filepath, status='Closed')
        db.session.add(doc)
    else:
        doc.sciezka_pliku = filepath
    
    db.session.commit()

    return api_success({
        "id": doc.id,
        "typ": doc.typ,
        "sciezka_pliku": doc.sciezka_pliku,
        "download_url": doc.get_download_url()
    }, status=201)
