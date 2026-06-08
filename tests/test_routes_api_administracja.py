import pytest
from datetime import date
from app import db
from app.models import ZakladPracy, Praktyka, Student, Uzytkownik

def test_administracja_endpoints(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup Admin user
    admin_user = Uzytkownik(
        imie="Kacper",
        nazwisko="Admin",
        email="admin@ans-elblag.pl",
        rola="administrator"
    )
    admin_user.set_password("admin123")
    db_session.add(admin_user)
    db_session.commit()

    # Log in as Admin
    client.get(f'/auth/login?mock_email={admin_user.email}&mock_rola=administrator')

    # 1. POST zaklad with higher education (happy path)
    data = {
        "nazwa": "Super Code sp. z o.o.",
        "adres": "Elbląg, Grunwaldzka 1",
        "nip": "9876543210",
        "zopz_imie": "Tomasz",
        "zopz_nazwisko": "Kowalski",
        "zopz_stanowisko": "Dyrektor handlowy",
        "zopz_wyksztalcenie": "Wyższe magisterskie"
    }
    response = client.post('/api/v1/zaklady', json=data)
    assert response.status_code == 201
    assert response.get_json()["data"]["nip"] == "9876543210"

    # 2. POST zaklad with low qualifications (422)
    invalid_data = {
        "nazwa": "Code sp. z o.o.",
        "adres": "Elbląg, Grunwaldzka 1",
        "nip": "1111111111",
        "zopz_imie": "Tomasz",
        "zopz_nazwisko": "Kowalski",
        "zopz_stanowisko": "Dyrektor handlowy",
        "zopz_wyksztalcenie": "brak" # invalid
    }
    response = client.post('/api/v1/zaklady', json=invalid_data)
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INVALID_ZOPZ_QUALIFICATION"

    # 3. GET list of companies
    response = client.get('/api/v1/zaklady')
    assert response.status_code == 200
    assert len(response.get_json()["data"]) >= 2

    # 4. POST przypisania (Admin assigns UOPZ to student practices)
    # Create practice first
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id, # assign sample_uopz initially
        termin_od=date(2026, 7, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Draft"
    )
    db_session.add(praktyka)
    db_session.commit()

    # Define another uopz
    uopz2 = Uzytkownik(
        imie="Mariusz",
        nazwisko="Praktyk",
        email="mariusz.praktyk@ans-elblag.pl",
        rola="uopz"
    )
    uopz2.set_password("uopz222")
    db_session.add(uopz2)
    db_session.commit()

    assign_data = {
        "uopz_id": uopz2.id,
        "studenci_ids": [sample_student.id]
    }
    response = client.post('/api/v1/przypisania', json=assign_data)
    assert response.status_code == 200
    assert "Przypisano opiekuna UOPZ" in response.get_json()["data"]["message"]
    assert Praktyka.query.get(praktyka.id).uopz_id == uopz2.id

    # 5. UOPZ extends the practice (przedluzenie)
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={uopz2.email}&mock_rola=uopz')

    extend_data = {
        "praktyka_id": praktyka.id,
        "nowa_data_do": "2026-10-15" # Extended by 15 days (<= 31 days)
    }
    response = client.post('/api/v1/przedluzenie', json=extend_data)
    assert response.status_code == 200
    assert response.get_json()["data"]["termin_do"] == "2026-10-15"

    # Too long extension (>31 days)
    too_long_data = {
        "praktyka_id": praktyka.id,
        "nowa_data_do": "2026-12-30"
    }
    response = client.post('/api/v1/przedluzenie', json=too_long_data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "EXTENSION_TOO_LONG"

    # 6. GET stats report (stan-praktyk)
    response = client.get('/api/v1/raporty/stan-praktyk?rok_ak=2025/2026')
    assert response.status_code == 200
    assert response.get_json()["data"]["lacznie"] == 1

    # 7. GET stats csv export
    response = client.get('/api/v1/raporty/eksport?rok_ak=2025/2026')
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert b"Draft" in response.data

    # 8. POST control/students (Student creates academic profile)
    client.get('/auth/logout')
    new_student_user = Uzytkownik(
        imie="Michał",
        nazwisko="Kowalski",
        email="michal.kowalski@ans-elblag.pl",
        rola="student"
    )
    new_student_user.set_password("student123")
    db_session.add(new_student_user)
    db_session.commit()

    client.get(f'/auth/login?mock_email={new_student_user.email}&mock_rola=student')
    
    student_data = {
        "uzytkownik_id": new_student_user.id,
        "nr_albumu": "88776",
        "kierunek": "Informatyka",
        "specjalnosc": "Cyberbezpieczeństwo",
        "semestr": 6,
        "forma_studiow": "stacjonarne",
        "rok_akademicki": "2025/2026"
    }
    response = client.post('/api/v1/control/students', json=student_data)
    assert response.status_code == 201
    assert response.get_json()["data"]["nr_albumu"] == "88776"

    # Double save -> error (400)
    response = client.post('/api/v1/control/students', json=student_data)
    assert response.status_code == 400

