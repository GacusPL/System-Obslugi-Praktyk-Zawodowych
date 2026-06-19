import pytest
from app import db
from app.models import PotwierdzenieEfektow, PotwierdzenieEfektOcena, Praktyka, Student, Uzytkownik, EfektUczenia, WpisDziennika


def _seed_full_dziennik(db_session, praktyka):
    """120 zatwierdzonych wpisów - warunek wysyłki potwierdzenia efektów (pkt 9)."""
    for i in range(1, 121):
        db_session.add(WpisDziennika(
            praktyka_id=praktyka.id, dzien_nr=i,
            data_wpisu=praktyka.termin_od, opis_prac=f"Opis prac dnia {i}",
            status='Approved'
        ))
    db_session.commit()


def test_efekty_crud_and_signatures(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup ZOPZ user whose name matches the ZOPZ of sample_zaklad
    zopz_user = Uzytkownik(
        imie=sample_zaklad.zopz_imie,
        nazwisko=sample_zaklad.zopz_nazwisko,
        email="zopz@ans-elblag.pl",
        rola="zopz"
    )
    zopz_user.set_password("zopz123")
    db_session.add(zopz_user)

    # Setup exactly 13 learning outcomes in DB (since we need exactly 13 for evaluation)
    for i in range(1, 14):
        efekt = EfektUczenia(nr=i, opis=f"Efekt {i}")
        db_session.add(efekt)
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
    _seed_full_dziennik(db_session, praktyka)

    # Log in as ZOPZ to submit evaluation
    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')

    # 1. GET template
    response = client.get(f'/api/v1/efekty/szablon/{praktyka.id}')
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 13

    # 2. POST invalid count of effects (12 instead of 13)
    invalid_oceny = [{"efekt_nr": i, "uzyskano": 1} for i in range(1, 13)]
    data = {
        "praktyka_id": praktyka.id,
        "godziny_zrealizowane": 360,
        "oceny": invalid_oceny
    }
    response = client.post('/api/v1/efekty/potwierdzenie', json=data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_EFFECTS_COUNT"

    # 3. POST valid evaluation (13 effects)
    valid_oceny = [{"efekt_nr": i, "uzyskano": 1} for i in range(1, 14)]
    data = {
        "praktyka_id": praktyka.id,
        "godziny_zrealizowane": 360,
        "oceny": valid_oceny
    }
    response = client.post('/api/v1/efekty/potwierdzenie', json=data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Submitted"
    potwierdzenie_id = res_json["data"]["id"]

    # 4. GET confirmation
    response = client.get(f'/api/v1/efekty/potwierdzenie/{praktyka.id}')
    assert response.status_code == 200
    assert len(response.get_json()["data"]["oceny"]) == 13

    # 5. Log in as UOPZ to approve the confirmation
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    response = client.patch(f'/api/v1/efekty/potwierdzenie/{potwierdzenie_id}', json={
        "status": "Approved",
        "opinia_uopz": "Wszystko zaliczone"
    })
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Approved"
    assert response.get_json()["data"]["opinia_uopz"] == "Wszystko zaliczone"


def _setup_efekty_praktyka(db_session, sample_student, sample_zaklad, sample_uopz):
    zopz_user = Uzytkownik(
        imie=sample_zaklad.zopz_imie, nazwisko=sample_zaklad.zopz_nazwisko,
        email="zopz2@ans-elblag.pl", rola="zopz"
    )
    zopz_user.set_password("zopz123")
    db_session.add(zopz_user)
    for i in range(1, 14):
        db_session.add(EfektUczenia(nr=i, opis=f"Efekt {i}"))
    db_session.commit()
    praktyka = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026", status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()
    return zopz_user, praktyka


def test_efekty_create_blocked_before_dziennik(client, db_session, sample_student, sample_zaklad, sample_uopz):
    zopz_user, praktyka = _setup_efekty_praktyka(db_session, sample_student, sample_zaklad, sample_uopz)
    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')
    oceny = [{"efekt_nr": i, "uzyskano": 1} for i in range(1, 14)]
    response = client.post('/api/v1/efekty/potwierdzenie', json={
        "praktyka_id": praktyka.id, "godziny_zrealizowane": 360, "oceny": oceny
    })
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "DZIENNIK_INCOMPLETE"


def test_efekty_approve_blocked_when_none_confirmed(client, db_session, sample_student, sample_zaklad, sample_uopz):
    zopz_user, praktyka = _setup_efekty_praktyka(db_session, sample_student, sample_zaklad, sample_uopz)
    _seed_full_dziennik(db_session, praktyka)

    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')
    oceny = [{"efekt_nr": i, "uzyskano": 0} for i in range(1, 14)]
    response = client.post('/api/v1/efekty/potwierdzenie', json={
        "praktyka_id": praktyka.id, "godziny_zrealizowane": 360, "oceny": oceny
    })
    assert response.status_code == 201
    potwierdzenie_id = response.get_json()["data"]["id"]

    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')
    response = client.patch(f'/api/v1/efekty/potwierdzenie/{potwierdzenie_id}', json={"status": "Approved"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "NO_EFFECTS_CONFIRMED"
