from datetime import datetime, date
from app.models import WpisDziennika, HarmonogramDzial, PotwierdzenieEfektOcena, AnkietaOdpowiedz

def validate_dziennik_completeness(praktyka_id):
    count = WpisDziennika.query.filter_by(praktyka_id=praktyka_id, status='Approved').count()
    if count == 120:
        return True, "Dziennik kompletny (120 dni zatwierdzonych)"
    return False, f"Dziennik niekompletny: zatwierdzono {count}/120 dni"

def validate_harmonogram_sum(harmonogram_id):
    dzialy = HarmonogramDzial.query.filter_by(harmonogram_id=harmonogram_id).all()
    total_days = sum(dzial.planowane_dni for dzial in dzialy)
    if total_days == 120:
        return True, "Suma dni w harmonogramie wynosi 120"
    return False, f"Suma dni w harmonogramie wynosi {total_days} (wymagane 120)"

def validate_all_effects_rated(potwierdzenie_id):
    count = PotwierdzenieEfektOcena.query.filter_by(potwierdzenie_id=potwierdzenie_id).count()
    if count == 13:
        return True, "Wszystkie 13 efektów uczenia się zostało ocenionych"
    return False, f"Oceniono {count}/13 efektów"

def validate_dates_range(termin_od, termin_do):
    if not termin_od or not termin_do:
        return False, "Brakujące daty"
        
    try:
        if isinstance(termin_od, str):
            termin_od = datetime.strptime(termin_od, '%Y-%m-%d').date()
        elif isinstance(termin_od, datetime):
            termin_od = termin_od.date()
            
        if isinstance(termin_do, str):
            termin_do = datetime.strptime(termin_do, '%Y-%m-%d').date()
        elif isinstance(termin_do, datetime):
            termin_do = termin_do.date()
    except ValueError:
        return False, "Nieprawidłowy format daty"
        
    if termin_od > termin_do:
        return False, "Data zakończenia nie może być wcześniejsza niż data rozpoczęcia"
    return True, "Zakres dat poprawny"

def validate_ankieta_complete(ankieta_id):
    count = AnkietaOdpowiedz.query.filter_by(ankieta_id=ankieta_id).count()
    if count == 14:
        return True, "Ankieta kompletna (14 odpowiedzi)"
    return False, f"Wypełniono {count}/14 pytań"
