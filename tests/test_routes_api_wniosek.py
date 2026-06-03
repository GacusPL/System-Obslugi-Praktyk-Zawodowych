import pytest
from io import BytesIO
from app import db
from app.models import WniosekAlternatywny, Student, Uzytkownik, EfektUczenia, PotwierdzenieEfektow, PotwierdzenieEfektOcena

def test_wniosek_crud_and_upload(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup Dyrektor user
    dyrektor = Uzytkownik(
        imie="Janusz",
        nazwisko="Dyrektor",
        email="dyrektor@ans-elblag.pl",
        rola="dyrektor"
    )
    dyrektor.set_password("dyrektor123")
    db_session.add(dyrektor)

    # Setup exactly 13 learning outcomes in DB (since we need exactly 13 for evaluation)
    for i in range(1, 14):
        efekt = EfektUczenia(nr=i, opis=f"Efekt {i}")
        db_session.add(efekt)
    db_session.commit()

    # Log in as student
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # 1. POST wniosek with invalid file extension (.exe)
    invalid_data = {
        "typ": "praca_zawodowa",
        "uzasadnienie": "Pracuję jako programista",
        "skany": (BytesIO(b"some exe bytes"), "hack.exe")
    }
    response = client.post('/api/v1/wniosek-zaliczenia', data=invalid_data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "Niedozwolony typ pliku" in response.get_json()["error"]["message"]

    # 2. POST wniosek with too large file (>10MB)
    large_content = b"0" * (11 * 1024 * 1024) # 11MB
    large_data = {
        "typ": "praca_zawodowa",
        "uzasadnienie": "Pracuję jako programista",
        "skany": (BytesIO(large_content), "large.pdf")
    }
    response = client.post('/api/v1/wniosek-zaliczenia', data=large_data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "przekracza maksymalny rozmiar" in response.get_json()["error"]["message"]

    # 3. POST wniosek with valid PDF file (happy path)
    valid_data = {
        "typ": "praca_zawodowa",
        "uzasadnienie": "Pracuję jako programista",
        "skany": (BytesIO(b"valid pdf data"), "cv.pdf")
    }
    response = client.post('/api/v1/wniosek-zaliczenia', data=valid_data, content_type='multipart/form-data')
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Submitted"
    wniosek_id = res_json["data"]["id"]

    # 4. GET wniosek
    response = client.get(f'/api/v1/wniosek/{wniosek_id}')
    assert response.status_code == 200
    skany_info = response.get_json()["data"]["skany"]
    assert len(skany_info) == 1
    assert skany_info[0]["nazwa_pliku"] == "cv.pdf"
    
    sciezka = skany_info[0]["sciezka_pliku"]
    # Path is uploads/wnioski/<uuid>/cv.pdf, so split and get the second-to-last element
    file_uuid = sciezka.split('/')[-2]

    # Download as student (allowed)
    response = client.get(f'/api/v1/files/{file_uuid}')
    assert response.status_code == 200
    assert response.data == b"valid pdf data"

    # Try to download as ZOPZ (forbidden)
    client.get('/auth/logout')
    client.get('/auth/login?mock_email=zopz_test@ans-elblag.pl&mock_rola=zopz')
    response = client.get(f'/api/v1/files/{file_uuid}')
    assert response.status_code == 403

    # 5. Log in as Dyrektor to evaluate the request
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={dyrektor.email}&mock_rola=dyrektor')

    # Post commission decision and 13 outcome evaluations
    oceny = [{"efekt_nr": i, "uzyskano": 1} for i in range(1, 14)]
    eval_data = {
        "wniosek_id": wniosek_id,
        "opinia_komisji": "Komisja akceptuje wniosek na podstawie stażu pracy",
        "decyzja": "zgoda_pelna",
        "oceny": oceny
    }
    response = client.post('/api/v1/komisja/ocena', json=eval_data)
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Approved"
    assert response.get_json()["data"]["decyzja"] == "zgoda_pelna"

    # Verify that learning outcomes were successfully saved in the DB
    w = WniosekAlternatywny.query.get(wniosek_id)
    pe = PotwierdzenieEfektow.query.first()
    assert pe is not None
    assert pe.status == "Approved"
    assert pe.godziny_zrealizowane == 360
    assert PotwierdzenieEfektOcena.query.count() == 13
