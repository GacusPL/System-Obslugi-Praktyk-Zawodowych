import pytest
from app import db
from app.models import Ankieta, AnkietaOdpowiedz, Praktyka, Student, Uzytkownik, WpisDziennika


def _seed_full_dziennik(db_session, praktyka):
    """120 zatwierdzonych wpisów - warunek wysyłki ankiety (pkt 9)."""
    for i in range(1, 121):
        db_session.add(WpisDziennika(
            praktyka_id=praktyka.id, dzien_nr=i,
            data_wpisu=praktyka.termin_od, opis_prac=f"Opis prac dnia {i}",
            status='Approved'
        ))
    db_session.commit()


def test_ankieta_crud_and_anonymity(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Create a practice for testing
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026",
        status="Approved",
        ankieta_wypelniona=0
    )
    db_session.add(praktyka)
    db_session.commit()
    _seed_full_dziennik(db_session, praktyka)

    # Log in as student
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # 1. GET template
    response = client.get('/api/v1/ankieta/szablon')
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 14

    # 2. POST invalid answers count (13 answers)
    invalid_odp = [{"pytanie_nr": i, "odpowiedz": 5} for i in range(1, 14)]
    data = {
        "praktyka_id": praktyka.id,
        "odpowiedzi": invalid_odp,
        "uwagi": "Brak uwag"
    }
    response = client.post('/api/v1/ankieta', json=data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_ANSWERS_COUNT"

    # 3. POST valid answers
    valid_odp = [{"pytanie_nr": i, "odpowiedz": 5} for i in range(1, 15)]
    data = {
        "praktyka_id": praktyka.id,
        "odpowiedzi": valid_odp,
        "uwagi": "Brak uwag"
    }
    response = client.post('/api/v1/ankieta', json=data)
    assert response.status_code == 201
    assert response.get_json()["data"]["message"] == "Ankieta została zapisana pomyślnie. Dziękujemy!"

    # 4. Verify that the practice is updated
    updated_p = Praktyka.query.get(praktyka.id)
    assert updated_p.ankieta_wypelniona == 1

    # 5. Verify anonymity (no student_id or link to student in Ankieta table)
    # Check if there is an Ankieta row in database
    ankieta_row = Ankieta.query.first()
    assert ankieta_row is not None
    assert ankieta_row.uwagi == "Brak uwag"
    
    # Assert that no column in Ankieta table has student_id or practice_id
    # We can inspect the model mapper's columns
    columns = [c.key for c in Ankieta.__table__.columns]
    assert "student_id" not in columns
    assert "praktyka_id" not in columns


def test_ankieta_blocked_before_dziennik_complete(client, db_session, sample_student, sample_zaklad, sample_uopz):
    praktyka = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026", status="Approved", ankieta_wypelniona=0
    )
    db_session.add(praktyka)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    valid_odp = [{"pytanie_nr": i, "odpowiedz": 5} for i in range(1, 15)]
    response = client.post('/api/v1/ankieta', json={
        "praktyka_id": praktyka.id, "odpowiedzi": valid_odp, "uwagi": ""
    })
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "DZIENNIK_INCOMPLETE"
