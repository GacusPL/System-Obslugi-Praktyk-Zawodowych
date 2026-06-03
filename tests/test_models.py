import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import (
    EfektUczenia, Uzytkownik, Student, ZakladPracy, Praktyka,
    Harmonogram, HarmonogramDzial, WpisDziennika, Ankieta, AnkietaOdpowiedz,
    Egzamin, KomisjaCzlonek, Dokument, PotwierdzenieEfektow, PotwierdzenieEfektOcena
)

def test_efekt_uczenia_creation(db_session):
    # Happy path: nr 1-13
    efekt = EfektUczenia(nr=1, opis="Wiedza matematyczna")
    db_session.add(efekt)
    db_session.commit()
    assert EfektUczenia.query.count() == 1

    # Unique check
    dup = EfektUczenia(nr=1, opis="Inna wiedza")
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Range check - SQLite CheckConstraint is sometimes only enforced on insert or if supported by db.
    # Let's test if range constraint triggers an integrity error (SQLite supports CHECK constraints)
    out_of_range = EfektUczenia(nr=14, opis="Błędny efekt")
    db_session.add(out_of_range)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_uzytkownik_creation(db_session):
    # Happy path with valid rola
    user = Uzytkownik(imie="Test", nazwisko="User", email="test@ans-elblag.pl", rola="student")
    user.set_password("pass")
    db_session.add(user)
    db_session.commit()
    assert user.check_password("pass")
    assert user.is_authenticated

    # Duplicate email check
    dup = Uzytkownik(imie="Test2", nazwisko="User2", email="test@ans-elblag.pl", rola="zopz")
    dup.set_password("pass")
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid rola check
    invalid_rola = Uzytkownik(imie="Test3", nazwisko="User3", email="test3@ans-elblag.pl", rola="invalid")
    invalid_rola.set_password("pass")
    db_session.add(invalid_rola)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_student_creation(db_session, sample_user):
    # Happy path
    student = Student(
        uzytkownik_id=sample_user.id,
        nr_albumu="54321",
        kierunek="Informatyka",
        semestr=6,
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student)
    db_session.commit()
    assert student.uzytkownik == sample_user
    assert sample_user.student == student

    # Duplicate nr_albumu check
    user2 = Uzytkownik(imie="Jan2", nazwisko="Kowalski2", email="jan2.kowalski@ans-elblag.pl", rola="student")
    user2.set_password("pass")
    db_session.add(user2)
    db_session.commit()

    student_dup = Student(
        uzytkownik_id=user2.id,
        nr_albumu="54321", # duplicate album
        kierunek="Informatyka",
        semestr=6,
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Semestr check (must be 6 or 7)
    student_invalid_sem = Student(
        uzytkownik_id=user2.id,
        nr_albumu="99999",
        kierunek="Informatyka",
        semestr=5, # invalid semestr
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student_invalid_sem)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_praktyka_creation(db_session, sample_student, sample_zaklad, sample_uopz):
    # Happy path
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 7, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Draft",
        dziennik_status="Draft"
    )
    db_session.add(praktyka)
    db_session.commit()
    assert praktyka.student == sample_student
    assert praktyka.zaklad_pracy == sample_zaklad
    assert praktyka.uopz == sample_uopz

    # Invalid status check
    praktyka.status = "invalid_status"
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid ocena check
    praktyka_invalid_ocena = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 7, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Draft",
        ocena_koncowa=5.5 # invalid ocena
    )
    db_session.add(praktyka_invalid_ocena)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_harmonogram_and_dzial(db_session, sample_praktyka):
    # Happy path
    harmonogram = Harmonogram(praktyka_id=sample_praktyka.id, status='Draft')
    db_session.add(harmonogram)
    db_session.commit()

    dzial1 = HarmonogramDzial(harmonogram_id=harmonogram.id, nazwa_dzialu="Programowanie", planowane_dni=60)
    dzial2 = HarmonogramDzial(harmonogram_id=harmonogram.id, nazwa_dzialu="Testowanie", planowane_dni=60)
    db_session.add_all([dzial1, dzial2])
    db_session.commit()

    assert len(harmonogram.dzialy) == 2
    assert harmonogram.validate_total_days() is True

    # Duplicate check: 1:1 praktyka to harmonogram
    dup_harmonogram = Harmonogram(praktyka_id=sample_praktyka.id, status='Draft')
    db_session.add(dup_harmonogram)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_wpis_dziennika_and_efekt(db_session, sample_praktyka):
    efekt1 = EfektUczenia(nr=1, opis="Matematyka")
    efekt2 = EfektUczenia(nr=2, opis="Fizyka")
    db_session.add_all([efekt1, efekt2])
    db_session.commit()

    # Happy path
    wpis = WpisDziennika(
        praktyka_id=sample_praktyka.id,
        dzien_nr=1,
        data_wpisu=date(2026, 7, 1),
        opis_prac="Wykonano zadania testowe",
        status="Draft"
    )
    wpis.efekty.append(efekt1)
    wpis.efekty.append(efekt2)
    db_session.add(wpis)
    db_session.commit()

    assert len(wpis.efekty) == 2
    assert wpis.dzien_nr == 1

    # Duplicate dzien_nr check per praktyka
    wpis_dup = WpisDziennika(
        praktyka_id=sample_praktyka.id,
        dzien_nr=1,
        data_wpisu=date(2026, 7, 2),
        opis_prac="Inna praca",
        status="Draft"
    )
    db_session.add(wpis_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid range dzien_nr check (>120)
    wpis_invalid_day = WpisDziennika(
        praktyka_id=sample_praktyka.id,
        dzien_nr=121,
        data_wpisu=date(2026, 7, 2),
        opis_prac="Inna praca",
        status="Draft"
    )
    db_session.add(wpis_invalid_day)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_ankieta_anonymity_and_validation(db_session):
    # Happy path: no student_id link
    ankieta = Ankieta(
        rok_akademicki="2025/2026",
        kierunek="Informatyka",
        forma_studiow="stacjonarne",
        semestr=6,
        godziny=120
    )
    db_session.add(ankieta)
    db_session.commit()

    for i in range(1, 15):
        odp = AnkietaOdpowiedz(ankieta_id=ankieta.id, pytanie_nr=i, odpowiedz=4)
        db_session.add(odp)
    db_session.commit()

    assert len(ankieta.odpowiedzi) == 14
    
    # Invalid answer score (e.g. 6)
    odp_invalid = AnkietaOdpowiedz(ankieta_id=ankieta.id, pytanie_nr=1, odpowiedz=6)
    db_session.add(odp_invalid)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_egzamin_and_komisja(db_session, sample_praktyka, sample_uopz):
    # Happy path
    egzamin = Egzamin(praktyka_id=sample_praktyka.id, termin=datetime(2026, 10, 10, 10, 0))
    db_session.add(egzamin)
    db_session.commit()

    czlonek = KomisjaCzlonek(egzamin_id=egzamin.id, uzytkownik_id=sample_uopz.id, rola_w_komisji="przewodniczacy")
    db_session.add(czlonek)
    db_session.commit()

    assert len(egzamin.komisja) == 1
    assert egzamin.komisja[0].uzytkownik == sample_uopz

    # Duplicate member in commission
    dup_czlonek = KomisjaCzlonek(egzamin_id=egzamin.id, uzytkownik_id=sample_uopz.id, rola_w_komisji="czlonek")
    db_session.add(dup_czlonek)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
