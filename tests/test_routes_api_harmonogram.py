import pytest
from app import db
from app.models import Harmonogram, HarmonogramDzial, Praktyka, Student, Uzytkownik

def test_harmonogram_crud_and_signatures(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup ZOPZ user whose name matches the ZOPZ of sample_zaklad
    zopz_user = Uzytkownik(
        imie=sample_zaklad.zopz_imie,
        nazwisko=sample_zaklad.zopz_nazwisko,
        email="zopz@ans-elblag.pl",
        rola="zopz"
    )
    zopz_user.set_password("zopz123")
    db_session.add(zopz_user)
    db_session.commit()

    # Log in as uopz to create harmonogram
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # Create a practice for testing
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(), # just some dates
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026",
        status="Draft"
    )
    db_session.add(praktyka)
    db_session.commit()

    # 1. POST valid harmonogram (sum of days = 120)
    data = {
        "praktyka_id": praktyka.id,
        "dzialy": [
            {"nazwa_dzialu": "Kwalifikacja I", "planowane_dni": 40},
            {"nazwa_dzialu": "Kwalifikacja II", "planowane_dni": 80}
        ]
    }
    response = client.post('/api/v1/harmonogramy', json=data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Draft"
    harmonogram_id = res_json["data"]["id"]

    # 2. POST duplicate harmonogram for same practice (error)
    response = client.post('/api/v1/harmonogramy', json=data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "HARMONOGRAM_ALREADY_EXISTS"

    # 3. POST invalid harmonogram (sum of days != 120)
    praktyka2 = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=praktyka.termin_od,
        termin_do=praktyka.termin_do,
        rok_akademicki="2025/2026",
        status="Draft"
    )
    db_session.add(praktyka2)
    db_session.commit()
    
    invalid_data = {
        "praktyka_id": praktyka2.id,
        "dzialy": [
            {"nazwa_dzialu": "Kwalifikacja I", "planowane_dni": 30},
            {"nazwa_dzialu": "Kwalifikacja II", "planowane_dni": 80}
        ]
    }
    response = client.post('/api/v1/harmonogramy', json=invalid_data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_TOTAL_DAYS"

    # 4. GET harmonogram (as uopz)
    response = client.get(f'/api/v1/harmonogramy/{praktyka.id}')
    assert response.status_code == 200
    assert len(response.get_json()["data"]["dzialy"]) == 2

    # 5. Student signs their part
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # Student cannot change status or other signatures
    response = client.patch(f'/api/v1/harmonogramy/{harmonogram_id}', json={"podpis_zopz": 1})
    assert response.status_code == 403

    # Student signs successfully
    response = client.patch(f'/api/v1/harmonogramy/{harmonogram_id}', json={"podpis_student": 1})
    assert response.status_code == 200
    assert response.get_json()["data"]["podpis_student"] == 1

    # 6. ZOPZ signs their part
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')

    # ZOPZ cannot change status or other signatures
    response = client.patch(f'/api/v1/harmonogramy/{harmonogram_id}', json={"podpis_uopz": 1})
    assert response.status_code == 403

    # ZOPZ signs successfully
    response = client.patch(f'/api/v1/harmonogramy/{harmonogram_id}', json={"podpis_zopz": 1})
    assert response.status_code == 200
    assert response.get_json()["data"]["podpis_zopz"] == 1

    # 7. UOPZ signs their part -> Auto-approve
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    response = client.patch(f'/api/v1/harmonogramy/{harmonogram_id}', json={"podpis_uopz": 1})
    assert response.status_code == 200
    assert response.get_json()["data"]["podpis_uopz"] == 1
    assert response.get_json()["data"]["status"] == "Approved"

    # Verify that the practice status is also updated to Under_Review
    assert Praktyka.query.get(praktyka.id).status == "Under_Review"

    # 8. Test PUT save and PATCH /signature routes (using student login)
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # Create a fresh practice and harmonogram in draft for student to edit and sign
    praktyka3 = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=praktyka.termin_od,
        termin_do=praktyka.termin_do,
        rok_akademicki="2025/2026",
        status="Draft"
    )
    db_session.add(praktyka3)
    db_session.commit()

    h3 = Harmonogram(praktyka_id=praktyka3.id, status="Draft")
    db_session.add(h3)
    db_session.commit()

    # Save divisions via PUT (sum = 120)
    put_data = {
        "dzialy": [
            {"nazwa_dzialu": "A", "planowane_dni": 50},
            {"nazwa_dzialu": "B", "planowane_dni": 70}
        ]
    }
    response = client.put(f'/api/v1/harmonogramy/{h3.id}', json=put_data)
    assert response.status_code == 200
    assert len(response.get_json()["data"]["dzialy"]) == 2

    # Save divisions via PUT (invalid sum != 120) -> 400
    invalid_put_data = {
        "dzialy": [
            {"nazwa_dzialu": "A", "planowane_dni": 50},
            {"nazwa_dzialu": "B", "planowane_dni": 60}
        ]
    }
    response = client.put(f'/api/v1/harmonogramy/{h3.id}', json=invalid_put_data)
    assert response.status_code == 400

    # Sign via PATCH .../signature
    response = client.patch(f'/api/v1/harmonogramy/{h3.id}/signature', json={"rola": "student"})
    assert response.status_code == 200
    assert response.get_json()["data"]["podpis_student"] == 1

