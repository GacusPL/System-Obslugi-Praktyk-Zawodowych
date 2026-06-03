import pytest
from datetime import datetime
from app import db
from app.models import Egzamin, KomisjaCzlonek, Praktyka, Student, Uzytkownik, KartaPraktyki

def test_egzamin_flow_and_export(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup some users for the commission
    dyrektor = Uzytkownik(
        imie="Janusz",
        nazwisko="Dyrektor",
        email="dyrektor@ans-elblag.pl",
        rola="dyrektor"
    )
    dyrektor.set_password("dyrektor123")
    db_session.add(dyrektor)
    db_session.commit()

    # Create a practice
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

    # 1. Log in as UOPZ to schedule exam
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # POST valid exam
    data = {
        "praktyka_id": praktyka.id,
        "termin": "2026-09-15 10:00:00",
        "komisja_sklad": [
            {"uzytkownik_id": sample_uopz.id, "rola_w_komisji": "czlonek"},
            {"uzytkownik_id": dyrektor.id, "rola_w_komisji": "przewodniczacy"}
        ]
    }
    response = client.post('/api/v1/egzamin', json=data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Draft"
    egzamin_id = res_json["data"]["id"]

    # 2. GET protocol
    response = client.get(f'/api/v1/egzamin/{egzamin_id}/protokol')
    assert response.status_code == 200
    assert response.get_json()["data"]["student"]["nr_albumu"] == sample_student.nr_albumu

    # 3. Submit exam results (fail case: grade 2.0 -> exam rejected and practice status set to Rejected)
    fail_data = {
        "ocena_ustna": 2.0,
        "ocena_koncowa": 2.0
    }
    response = client.post(f'/api/v1/egzamin/{egzamin_id}/wynik', json=fail_data)
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Rejected"
    assert Praktyka.query.get(praktyka.id).status == "Rejected"

    # 4. Schedule retake exam
    data2 = {
        "praktyka_id": praktyka.id,
        "termin": "2026-09-25 11:00:00",
        "komisja_sklad": [
            {"uzytkownik_id": sample_uopz.id, "rola_w_komisji": "czlonek"},
            {"uzytkownik_id": dyrektor.id, "rola_w_komisji": "przewodniczacy"}
        ]
    }
    response = client.post('/api/v1/egzamin', json=data2)
    assert response.status_code == 201
    retake_exam_id = response.get_json()["data"]["id"]

    # 5. Submit successful retake results (grade 4.5 -> exam approved and practice status set to Closed)
    success_data = {
        "ocena_ustna": 4.5,
        "ocena_koncowa": 4.5
    }
    response = client.post(f'/api/v1/egzamin/{retake_exam_id}/wynik', json=success_data)
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Approved"
    
    updated_p = Praktyka.query.get(praktyka.id)
    assert updated_p.status == "Closed"
    assert updated_p.ocena_koncowa == 4.5

    # 6. Export grades to XLSX
    response = client.get('/api/v1/eksport/oceny?format=xlsx')
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(response.data) > 0

    # 7. Export grades to CSV
    response = client.get('/api/v1/eksport/oceny?format=csv')
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert sample_student.nr_albumu.encode() in response.data
