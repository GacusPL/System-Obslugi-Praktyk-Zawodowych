import pytest
from app import db
from app.models import KartaPraktyki, Praktyka, Student, Uzytkownik

def test_karta_praktyki_crud_and_signatures(client, db_session, sample_student, sample_zaklad, sample_uopz):
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

    # Log in as ZOPZ
    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')

    # 1. POST valid grade (happy path)
    data = {
        "praktyka_id": praktyka.id,
        "ocena_param_zopz": 4.5,
        "ocena_opisowa_zopz": "Bardzo rzetelny student"
    }
    response = client.post('/api/v1/karta-praktyki/ocena', json=data)
    assert response.status_code == 201 or response.status_code == 200
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Under_Review"
    assert res_json["data"]["ocena_param_zopz"] == 4.5
    karta_id = res_json["data"]["id"]

    # 2. GET karta
    response = client.get(f'/api/v1/karta-praktyki/{praktyka.id}')
    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == karta_id

    # 3. Log in as UOPZ to evaluate/approve
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # PATCH invalid grade
    response = client.patch(f'/api/v1/karta-praktyki/{karta_id}', json={"ocena_param_uopz": 5.5})
    assert response.status_code == 400

    # PATCH valid UOPZ grade
    response = client.patch(f'/api/v1/karta-praktyki/{karta_id}', json={
        "ocena_param_uopz": 4.0,
        "ocena_opisowa_uopz": "Zaliczone bez uwag",
        "ocena_sprawozdania": 4.5,
        "status": "Approved"
    })
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Approved"
    assert res_json["data"]["ocena_param_uopz"] == 4.0
    assert res_json["data"]["ocena_sprawozdania"] == 4.5
