import pytest
from datetime import date, datetime
from app import db
from app.models import WpisDziennika, HarmonogramDzial, PotwierdzenieEfektow, PotwierdzenieEfektOcena, Ankieta, AnkietaOdpowiedz, Harmonogram
from app.validators import (
    validate_dziennik_completeness,
    validate_harmonogram_sum,
    validate_all_effects_rated,
    validate_dates_range,
    validate_ankieta_complete
)

def test_validate_dziennik_completeness(db_session, sample_praktyka):
    # Case: 0 approved entries
    valid, msg = validate_dziennik_completeness(sample_praktyka.id)
    assert not valid
    assert "niekompletny" in msg

    # Insert 120 approved entries
    for i in range(1, 121):
        wpis = WpisDziennika(
            praktyka_id=sample_praktyka.id,
            dzien_nr=i,
            data_wpisu=date(2026, 7, 1),
            opis_prac=f"Praca testowa dzień {i}",
            status='Approved',
            podpis_zopz=1
        )
        db_session.add(wpis)
    db_session.commit()

    valid, msg = validate_dziennik_completeness(sample_praktyka.id)
    assert valid
    assert "kompletny" in msg

    # Delete one to make it 119
    last_wpis = WpisDziennika.query.filter_by(praktyka_id=sample_praktyka.id, dzien_nr=120).first()
    db_session.delete(last_wpis)
    db_session.commit()

    valid, msg = validate_dziennik_completeness(sample_praktyka.id)
    assert not valid
    assert "119/120" in msg

def test_validate_harmonogram_sum(db_session, sample_praktyka):
    harmonogram = Harmonogram(praktyka_id=sample_praktyka.id, status='Draft')
    db_session.add(harmonogram)
    db_session.commit()

    # Case: sum of days != 120 (e.g. 100)
    dzial1 = HarmonogramDzial(harmonogram_id=harmonogram.id, nazwa_dzialu="Dzial 1", planowane_dni=50)
    dzial2 = HarmonogramDzial(harmonogram_id=harmonogram.id, nazwa_dzialu="Dzial 2", planowane_dni=50)
    db_session.add_all([dzial1, dzial2])
    db_session.commit()

    valid, msg = validate_harmonogram_sum(harmonogram.id)
    assert not valid
    assert "100" in msg

    # Case: sum of days == 120
    dzial3 = HarmonogramDzial(harmonogram_id=harmonogram.id, nazwa_dzialu="Dzial 3", planowane_dni=20)
    db_session.add(dzial3)
    db_session.commit()

    valid, msg = validate_harmonogram_sum(harmonogram.id)
    assert valid
    assert "120" in msg

def test_validate_all_effects_rated(db_session, sample_praktyka):
    potwierdzenie = PotwierdzenieEfektow(praktyka_id=sample_praktyka.id, godziny_zrealizowane=120, status='Draft')
    db_session.add(potwierdzenie)
    db_session.commit()

    # Case: less than 13 effects rated
    for i in range(1, 13):
        ocena = PotwierdzenieEfektOcena(potwierdzenie_id=potwierdzenie.id, efekt_id=i, uzyskano=1)
        db_session.add(ocena)
    db_session.commit()

    valid, msg = validate_all_effects_rated(potwierdzenie.id)
    assert not valid
    assert "12/13" in msg

    # Add the 13th
    ocena_13 = PotwierdzenieEfektOcena(potwierdzenie_id=potwierdzenie.id, efekt_id=13, uzyskano=1)
    db_session.add(ocena_13)
    db_session.commit()

    valid, msg = validate_all_effects_rated(potwierdzenie.id)
    assert valid
    assert "Wszystkie 13" in msg

def test_validate_dates_range():
    # Correct range
    valid, msg = validate_dates_range("2026-07-01", "2026-09-30")
    assert valid
    
    # Same day is valid
    valid, msg = validate_dates_range("2026-07-01", "2026-07-01")
    assert valid

    # Incorrect range (to < from)
    valid, msg = validate_dates_range("2026-09-30", "2026-07-01")
    assert not valid
    assert "wcześniejsza" in msg

    # Invalid format
    valid, msg = validate_dates_range("2026-07-01", "invalid-date")
    assert not valid
    assert "format" in msg

def test_validate_ankieta_complete(db_session):
    ankieta = Ankieta(
        rok_akademicki="2025/2026",
        kierunek="Informatyka",
        forma_studiow="stacjonarne",
        semestr=6,
        godziny=120
    )
    db_session.add(ankieta)
    db_session.commit()

    # Less than 14 answers
    for i in range(1, 14):
        odp = AnkietaOdpowiedz(ankieta_id=ankieta.id, pytanie_nr=i, odpowiedz=5)
        db_session.add(odp)
    db_session.commit()

    valid, msg = validate_ankieta_complete(ankieta.id)
    assert not valid
    assert "13/14" in msg

    # Complete 14
    odp_14 = AnkietaOdpowiedz(ankieta_id=ankieta.id, pytanie_nr=14, odpowiedz=4)
    db_session.add(odp_14)
    db_session.commit()

    valid, msg = validate_ankieta_complete(ankieta.id)
    assert valid

def test_validate_payload():
    from app.routes.api.helpers import validate_payload
    schema = {
        "email": {"type": str, "required": True, "lowercase_email": True},
        "ocena": {"type": float, "required": True, "min": 2.0, "max": 5.0},
        "dzien_nr": {"type": int, "required": False, "min": 1, "max": 120},
        "status": {"type": str, "choices": ["Draft", "Submitted"]}
    }

    # Happy path
    data = {
        "email": "  TEST@ans-elblag.pl  ",
        "ocena": "4.5",
        "dzien_nr": "15",
        "status": "Draft"
    }
    sanitized, errors = validate_payload(data, schema)
    assert not errors
    assert sanitized["email"] == "test@ans-elblag.pl"
    assert sanitized["ocena"] == 4.5
    assert sanitized["dzien_nr"] == 15
    assert sanitized["status"] == "Draft"

    # Validation errors
    bad_data = {
        "email": None, # required
        "ocena": 5.5,  # out of range
        "dzien_nr": "invalid", # type error
        "status": "InvalidStatus" # not in choices
    }
    sanitized, errors = validate_payload(bad_data, schema)
    assert "email" in errors
    assert "ocena" in errors
    assert "dzien_nr" in errors
    assert "status" in errors

