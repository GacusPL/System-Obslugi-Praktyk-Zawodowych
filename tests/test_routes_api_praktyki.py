import pytest
from app import db
from app.models import Praktyka, Student, ZakladPracy, Uzytkownik

def test_praktyki_crud_and_transitions(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Log in as student using the sample_student's user email
    student_email = sample_student.uzytkownik.email
    client.get(f'/auth/login?mock_email={student_email}&mock_rola=student')

    # 1. POST (happy path)
    data = {
        "zaklad_id": sample_zaklad.id,
        "uopz_id": sample_uopz.id,
        "termin_od": "2026-07-01",
        "termin_do": "2026-09-30",
        "rok_akademicki": "2025/2026"
    }
    response = client.post('/api/v1/praktyki', json=data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Draft"
    praktyka_id = res_json["data"]["id"]

    # 2. GET single
    response = client.get(f'/api/v1/praktyki/{praktyka_id}')
    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == praktyka_id

    # 3. GET list
    response = client.get('/api/v1/praktyki')
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 1

    # 4. PATCH status Draft -> Submitted (happy path)
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Submitted"})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Submitted"

    # 5. PATCH status Submitted -> Draft (invalid transition for student)
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Draft"})
    assert response.status_code == 403
    
    # Let's log in as uopz
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # UOPZ transitions Submitted -> Draft (happy path)
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Draft"})
    assert response.status_code == 200

    # Log in as student again
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={student_email}&mock_rola=student')

    # 6. DELETE Draft (happy path)
    response = client.delete(f'/api/v1/praktyki/{praktyka_id}')
    assert response.status_code == 200
    assert Praktyka.query.get(praktyka_id) is None

    # 7. Create another and submit, try to delete Submitted (error check)
    response = client.post('/api/v1/praktyki', json=data)
    assert response.status_code == 201
    praktyka_id = response.get_json()["data"]["id"]
    
    client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Submitted"})
    
    response = client.delete(f'/api/v1/praktyki/{praktyka_id}')
    assert response.status_code == 400
    assert "Draft" in response.get_json()["error"]["message"]
