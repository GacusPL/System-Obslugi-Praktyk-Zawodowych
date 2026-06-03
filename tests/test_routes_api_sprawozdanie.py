import pytest
from app import db
from app.models import Sprawozdanie, Praktyka, Student, Uzytkownik

def test_sprawozdanie_crud_and_validation(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Create a practice for testing
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026",
        status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()

    # Log in as student
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # 1. GET template
    response = client.get(f'/api/v1/sprawozdanie/szablon/{praktyka.id}')
    assert response.status_code == 200
    assert response.get_json()["data"]["praktyka_id"] == praktyka.id

    # 2. POST with short content (error)
    short_data = {
        "praktyka_id": praktyka.id,
        "sekcja_I": "Krótki opis",
        "sekcja_II": "Krótki opis",
        "sekcja_III": "Krótki opis",
        "status": "Submitted"
    }
    response = client.post('/api/v1/sprawozdanie', json=short_data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "SECTION_TOO_SHORT"

    # 3. POST valid content (>= 100 chars each)
    long_text = "A" * 105
    valid_data = {
        "praktyka_id": praktyka.id,
        "sekcja_I": long_text,
        "sekcja_II": long_text,
        "sekcja_III": long_text,
        "status": "Draft"
    }
    response = client.post('/api/v1/sprawozdanie', json=valid_data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Draft"
    assert res_json["data"]["wersja"] == 1
    sprawozdanie_id = res_json["data"]["id"]

    # 4. PUT update (wersja should increment)
    longer_text = "B" * 110
    update_data = {
        "sekcja_I": longer_text,
        "sekcja_II": longer_text,
        "sekcja_III": longer_text,
        "status": "Submitted"
    }
    response = client.put(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json=update_data)
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Submitted"
    assert response.get_json()["data"]["wersja"] == 2

    # 5. UOPZ reviews/grades
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # Try invalid grade range
    response = client.patch(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={"ocena": 6.0, "status": "Approved"})
    assert response.status_code == 400

    # Grade correctly
    response = client.patch(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={"ocena": 4.5, "status": "Approved"})
    assert response.status_code == 200
    assert response.get_json()["data"]["ocena"] == 4.5
    assert response.get_json()["data"]["status"] == "Approved"
