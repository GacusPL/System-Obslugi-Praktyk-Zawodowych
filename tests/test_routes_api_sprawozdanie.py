import pytest
from app import db
from app.models import Sprawozdanie, Praktyka, Student, Uzytkownik, WpisDziennika, KartaPraktyki


def _seed_full_dziennik(db_session, praktyka):
    """120 zatwierdzonych wpisów - warunek wysyłki sprawozdania (pkt 9)."""
    for i in range(1, 121):
        db_session.add(WpisDziennika(
            praktyka_id=praktyka.id, dzien_nr=i,
            data_wpisu=praktyka.termin_od, opis_prac=f"Opis prac dnia {i}",
            status='Approved'
        ))
    db_session.commit()


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
    _seed_full_dziennik(db_session, praktyka)

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


def test_sprawozdanie_blocked_before_dziennik_complete(client, db_session, sample_student, sample_zaklad, sample_uopz):
    praktyka = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026", status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    long_text = "A" * 105
    # Szkic dozwolony bez kompletnego dziennika
    response = client.post('/api/v1/sprawozdanie', json={
        "praktyka_id": praktyka.id, "sekcja_I": long_text, "sekcja_II": long_text,
        "sekcja_III": long_text, "status": "Draft"
    })
    assert response.status_code == 201
    sprawozdanie_id = response.get_json()["data"]["id"]

    # Wysłanie zablokowane - dziennik niekompletny
    response = client.put(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={
        "sekcja_I": long_text, "sekcja_II": long_text, "sekcja_III": long_text, "status": "Submitted"
    })
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "DZIENNIK_INCOMPLETE"


def test_sprawozdanie_reject_requires_comment_and_resubmit(client, db_session, sample_student, sample_zaklad, sample_uopz):
    praktyka = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026", status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()
    _seed_full_dziennik(db_session, praktyka)

    long_text = "A" * 105
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    response = client.post('/api/v1/sprawozdanie', json={
        "praktyka_id": praktyka.id, "sekcja_I": long_text, "sekcja_II": long_text,
        "sekcja_III": long_text, "status": "Submitted"
    })
    assert response.status_code == 201
    sprawozdanie_id = response.get_json()["data"]["id"]

    # UOPZ: odrzucenie bez komentarza blokowane
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')
    response = client.patch(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={"status": "Rejected"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_COMMENT"

    # UOPZ: odrzucenie z komentarzem
    response = client.patch(f'/api/v1/sprawozdanie/{sprawozdanie_id}',
                            json={"status": "Rejected", "komentarz_odrzucenia": "Rozwiń sekcję II."})
    assert response.status_code == 200
    assert Sprawozdanie.query.get(sprawozdanie_id).komentarz_odrzucenia == "Rozwiń sekcję II."

    # Student: poprawia i wysyła ponownie -> komentarz wyczyszczony
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    longer = "B" * 110
    response = client.put(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={
        "sekcja_I": longer, "sekcja_II": longer, "sekcja_III": longer, "status": "Submitted"
    })
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Submitted"
    assert Sprawozdanie.query.get(sprawozdanie_id).komentarz_odrzucenia is None


def test_sprawozdanie_approval_propagates_ocena_to_karta(client, db_session, sample_student, sample_zaklad, sample_uopz):
    praktyka = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=sample_student.uzytkownik.created_at.date(),
        termin_do=sample_student.uzytkownik.created_at.date(),
        rok_akademicki="2025/2026", status="Approved"
    )
    db_session.add(praktyka)
    db_session.commit()
    _seed_full_dziennik(db_session, praktyka)

    long_text = "A" * 105
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    response = client.post('/api/v1/sprawozdanie', json={
        "praktyka_id": praktyka.id, "sekcja_I": long_text, "sekcja_II": long_text,
        "sekcja_III": long_text, "status": "Submitted"
    })
    sprawozdanie_id = response.get_json()["data"]["id"]

    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')
    response = client.patch(f'/api/v1/sprawozdanie/{sprawozdanie_id}', json={"ocena": 4.5, "status": "Approved"})
    assert response.status_code == 200

    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka.id).first()
    assert karta is not None
    assert karta.ocena_sprawozdania == 4.5
