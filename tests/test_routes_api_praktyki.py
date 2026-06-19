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

    # 4. PATCH status Draft -> Submitted (student składa zgłoszenie)
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Submitted"})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Submitted"

    # 5. Student może wycofać własne zgłoszenie Submitted -> Draft
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Draft"})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Draft"

    # Ponowne złożenie do weryfikacji
    client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Submitted"})

    # Log in as uopz to verify the zgłoszenie
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # Odrzucenie bez komentarza jest blokowane
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Rejected"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_COMMENT"

    # Odrzucenie z komentarzem: Submitted -> Rejected
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}',
                            json={"status": "Rejected", "komentarz_odrzucenia": "Popraw termin praktyki."})
    assert response.status_code == 200
    assert Praktyka.query.get(praktyka_id).komentarz_odrzucenia == "Popraw termin praktyki."

    # 6. Student poprawia: Rejected -> Draft czyści komentarz
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={student_email}&mock_rola=student')
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Draft"})
    assert response.status_code == 200
    assert Praktyka.query.get(praktyka_id).komentarz_odrzucenia is None

    # 7. DELETE Draft (soft-delete: dane zachowane, oznaczone jako archived)
    response = client.delete(f'/api/v1/praktyki/{praktyka_id}')
    assert response.status_code == 200
    deleted = Praktyka.query.get(praktyka_id)
    assert deleted is not None
    assert deleted.archived is True

    # 8. Create another and submit, try to delete Submitted (error check)
    response = client.post('/api/v1/praktyki', json=data)
    assert response.status_code == 201
    praktyka_id = response.get_json()["data"]["id"]

    client.patch(f'/api/v1/praktyki/{praktyka_id}', json={"status": "Submitted"})

    response = client.delete(f'/api/v1/praktyki/{praktyka_id}')
    assert response.status_code == 400
    assert "Draft" in response.get_json()["error"]["message"]


def test_praktyka_create_with_new_zaklad(client, db_session, sample_student, sample_uopz):
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    data = {
        "uopz_id": sample_uopz.id,
        "termin_od": "2026-07-01",
        "termin_do": "2026-09-30",
        "rok_akademicki": "2025/2026",
        "new_zaklad": {
            "nazwa": "Nowa Firma", "adres": "Elbląg, ul. Nowa 5", "nip": "9998887776",
            "zopz_imie": "Jan", "zopz_nazwisko": "Opiekun",
            "zopz_stanowisko": "Kierownik", "zopz_wyksztalcenie": "Wyższe"
        }
    }
    response = client.post('/api/v1/praktyki', json=data)
    assert response.status_code == 201
    zaklad_id = response.get_json()["data"]["zaklad_id"]
    assert ZakladPracy.query.get(zaklad_id).nip == "9998887776"

    # Duplikat NIP -> błąd
    response = client.post('/api/v1/praktyki', json=data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "NIP_NOT_UNIQUE"


def test_praktyka_draft_field_edit(client, db_session, sample_student, sample_zaklad, sample_uopz):
    # Drugi UOPZ do podmiany
    uopz2 = Uzytkownik(imie="Piotr", nazwisko="Drugi", email="uopz2@ans-elblag.pl", rola="uopz")
    uopz2.set_password("x")
    db_session.add(uopz2)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    data = {
        "zaklad_id": sample_zaklad.id, "uopz_id": sample_uopz.id,
        "termin_od": "2026-07-01", "termin_do": "2026-09-30", "rok_akademicki": "2025/2026"
    }
    response = client.post('/api/v1/praktyki', json=data)
    praktyka_id = response.get_json()["data"]["id"]

    # Edycja pól szkicu bez zmiany statusu
    response = client.patch(f'/api/v1/praktyki/{praktyka_id}', json={
        "uopz_id": uopz2.id, "rok_akademicki": "2026/2027"
    })
    assert response.status_code == 200
    p = Praktyka.query.get(praktyka_id)
    assert p.uopz_id == uopz2.id
    assert p.rok_akademicki == "2026/2027"
    assert p.status == "Draft"
