import pytest
from datetime import date
from app import db
from app.models import WpisDziennika, Praktyka, Student, Uzytkownik, EfektUczenia

def test_dziennik_crud_and_signatures(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Setup ZOPZ user whose name matches the ZOPZ of sample_zaklad
    zopz_user = Uzytkownik(
        imie=sample_zaklad.zopz_imie,
        nazwisko=sample_zaklad.zopz_nazwisko,
        email="zopz@ans-elblag.pl",
        rola="zopz"
    )
    zopz_user.set_password("zopz123")
    db_session.add(zopz_user)

    # Setup some learning outcomes in DB (since we need to test referencing them)
    efekt1 = EfektUczenia(nr=1, opis="Efekt 1")
    efekt2 = EfektUczenia(nr=2, opis="Efekt 2")
    db_session.add_all([efekt1, efekt2])
    db_session.commit()

    # Create an APPROVED practice (required to add diary entries)
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 1, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()

    # Log in as student
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # 1. POST valid entry (happy path)
    data = {
        "praktyka_id": praktyka.id,
        "dzien_nr": 1,
        "data_wpisu": "2026-01-15",
        "opis_prac": "Konfiguracja środowiska",
        "efekty": [1, 2]
    }
    response = client.post('/api/v1/dziennik/wpisy', json=data)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["data"]["status"] == "Submitted"
    wpis_id = res_json["data"]["id"]

    # 2. POST duplicate entry for same day (error)
    response = client.post('/api/v1/dziennik/wpisy', json=data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "ENTRY_ALREADY_EXISTS"

    # 3. GET list of entries
    response = client.get(f'/api/v1/dziennik/{praktyka.id}')
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 1

    # 4. Student tries to approve/reject entry (403)
    response = client.patch(f'/api/v1/dziennik/wpisy/{wpis_id}', json={"status": "Approved"})
    assert response.status_code == 403

    # 5. Log in as ZOPZ to approve the entry
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={zopz_user.email}&mock_rola=zopz')

    # ZOPZ approves successfully
    response = client.patch(f'/api/v1/dziennik/wpisy/{wpis_id}', json={"status": "Approved", "komentarz_zopz": "Super robota"})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Approved"
    assert response.get_json()["data"]["podpis_zopz"] == 1

    # 6. Test automatic Under_Review transition after 120 Approved entries
    # Let's add the remaining 119 entries already marked as Approved
    for i in range(2, 121):
        wpis = WpisDziennika(
            praktyka_id=praktyka.id,
            dzien_nr=i,
            data_wpisu=date(2026, 7, 2),
            opis_prac=f"Praca dzien {i}",
            status="Draft"
        )
        db_session.add(wpis)
    db_session.commit()

    # Now approve the 120th entry as ZOPZ (let's say wpis for day 120 was Draft, now we approve it)
    wpis_120 = WpisDziennika.query.filter_by(praktyka_id=praktyka.id, dzien_nr=120).first()
    # Approve it
    response = client.patch(f'/api/v1/dziennik/wpisy/{wpis_120.id}', json={"status": "Approved"})
    assert response.status_code == 200

    # Wait, we need 120 APPROVED entries. Currently day 1 is Approved, day 120 is Approved,
    # but days 2-119 are Draft. Let's make all of them Approved.
    db_session.query(WpisDziennika).filter_by(praktyka_id=praktyka.id).update({"status": "Approved"})
    db_session.commit()

    # Let's make day 120 Draft again to test the transition on PATCH
    wpis_120.status = "Draft"
    db_session.commit()

    # Now approve day 120 via API
    response = client.patch(f'/api/v1/dziennik/wpisy/{wpis_120.id}', json={"status": "Approved"})
    assert response.status_code == 200
    
    # Check if Praktyka.dziennik_status is now 'Under_Review'
    p = Praktyka.query.get(praktyka.id)
    assert p.dziennik_status == "Under_Review"


def test_dziennik_rejects_future_date(client, db_session, sample_student, sample_zaklad, sample_uopz):
    from datetime import timedelta
    efekt = EfektUczenia(nr=1, opis="Efekt 1")
    db_session.add(efekt)
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 1, 1),
        termin_do=date(2026, 12, 31),
        rok_akademicki="2025/2026",
        status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    future = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
    response = client.post('/api/v1/dziennik/wpisy', json={
        "praktyka_id": praktyka.id,
        "dzien_nr": 1,
        "data_wpisu": future,
        "opis_prac": "Wpis z przyszłości",
        "efekty": [1]
    })
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_dziennik_rejects_duplicate_date(client, db_session, sample_student, sample_zaklad, sample_uopz):
    efekt = EfektUczenia(nr=1, opis="Efekt 1")
    db_session.add(efekt)
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 1, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    base = {"praktyka_id": praktyka.id, "data_wpisu": "2026-01-15", "opis_prac": "Praca", "efekty": [1]}
    r1 = client.post('/api/v1/dziennik/wpisy', json={**base, "dzien_nr": 1})
    assert r1.status_code == 201

    # Inny dzień, ta sama data -> odrzucone
    r2 = client.post('/api/v1/dziennik/wpisy', json={**base, "dzien_nr": 2})
    assert r2.status_code == 400
    assert r2.get_json()["error"]["code"] == "DUPLICATE_DATE"
