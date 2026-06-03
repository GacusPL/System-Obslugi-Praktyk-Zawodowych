import pytest
from datetime import date, datetime
from app import create_app, db
from app.models import Uzytkownik, Student, ZakladPracy, Praktyka

@pytest.fixture
def app():
    # Force loading 'testing' config
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture
def db_session(app):
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_user(db_session):
    user = Uzytkownik(
        imie="Jan",
        nazwisko="Kowalski",
        email="jan.kowalski@ans-elblag.pl",
        rola="student"
    )
    user.set_password("student123")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_student(db_session, sample_user):
    student = Student(
        uzytkownik_id=sample_user.id,
        nr_albumu="12345",
        kierunek="Informatyka",
        specjalnosc="Inżynieria Oprogramowania",
        semestr=6,
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student)
    db_session.commit()
    return student

@pytest.fixture
def sample_uopz(db_session):
    uopz = Uzytkownik(
        imie="Anna",
        nazwisko="Nowak",
        email="anna.nowak@ans-elblag.pl",
        rola="uopz"
    )
    uopz.set_password("uopz123")
    db_session.add(uopz)
    db_session.commit()
    return uopz

@pytest.fixture
def sample_zaklad(db_session):
    zaklad = ZakladPracy(
        nazwa="Firma Testowa",
        adres="Elbląg, ul. Testowa 1",
        nip="1234567890",
        zopz_imie="Adam",
        zopz_nazwisko="Zopz",
        zopz_stanowisko="Kierownik IT",
        zopz_wyksztalcenie="Wyższe",
        status="Approved"
    )
    db_session.add(zaklad)
    db_session.commit()
    return zaklad

@pytest.fixture
def sample_praktyka(db_session, sample_student, sample_zaklad, sample_uopz):
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 7, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Draft"
    )
    db_session.add(praktyka)
    db_session.commit()
    return praktyka
