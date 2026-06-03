import pytest
from datetime import date
from app import db
from app.models import (
    Praktyka, Student, Uzytkownik, Harmonogram, KartaPraktyki,
    PotwierdzenieEfektow, WpisDziennika, Sprawozdanie
)

def test_dokumentacja_checklist_and_submission(client, db_session, sample_student, sample_zaklad, sample_uopz):
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

    # Create a practice
    praktyka = Praktyka(
        student_id=sample_student.id,
        zaklad_id=sample_zaklad.id,
        uopz_id=sample_uopz.id,
        termin_od=date(2026, 7, 1),
        termin_do=date(2026, 9, 30),
        rok_akademicki="2025/2026",
        status="Approved",
        ankieta_wypelniona=0
    )
    db_session.add(praktyka)
    db_session.commit()

    # Log in as student
    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')

    # 1. GET checklist when empty (everything should be false)
    response = client.get(f'/api/v1/dokumentacja/checklist/{praktyka.id}')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json["data"]["harmonogram_approved"] is False
    assert res_json["data"]["karta_approved"] is False
    assert res_json["data"]["ankieta_complete"] is False

    # 2. Try to submit documentation when incomplete (should return 422)
    response = client.post('/api/v1/dokumentacja/zloz', json={"praktyka_id": praktyka.id})
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INCOMPLETE_DOCUMENTATION"

    # 3. Create/approve all necessary parts
    # Harmonogram approved
    h = Harmonogram(praktyka_id=praktyka.id, status='Approved', podpis_student=1, podpis_zopz=1, podpis_uopz=1)
    db_session.add(h)
    
    # Karta approved
    k = KartaPraktyki(praktyka_id=praktyka.id, status='Approved', ocena_param_zopz=4.0, ocena_param_uopz=4.0)
    db_session.add(k)

    # PotwierdzenieEfektow approved
    pe = PotwierdzenieEfektow(praktyka_id=praktyka.id, status='Approved', godziny_zrealizowane=360)
    db_session.add(pe)

    # Dziennik Closed + 120 approved entries
    praktyka.dziennik_status = 'Closed'
    for i in range(1, 121):
        wpis = WpisDziennika(praktyka_id=praktyka.id, dzien_nr=i, data_wpisu=date(2026, 7, 2), opis_prac="X", status="Approved")
        db_session.add(wpis)

    # Sprawozdanie approved
    s = Sprawozdanie(praktyka_id=praktyka.id, sekcja_I="x"*110, sekcja_II="y"*110, sekcja_III="z"*110, status='Approved')
    db_session.add(s)

    # Ankieta complete flag
    praktyka.ankieta_wypelniona = 1

    db_session.commit()

    # 4. GET checklist again (should be completely true)
    response = client.get(f'/api/v1/dokumentacja/checklist/{praktyka.id}')
    assert response.status_code == 200
    res_json = response.get_json()
    assert all(res_json["data"].values())

    # 5. Submit documentation (should transition practice to Under_Review)
    response = client.post('/api/v1/dokumentacja/zloz', json={"praktyka_id": praktyka.id})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "Under_Review"

    # 6. Log in as UOPZ to review/approve the submitted documentation
    client.get('/auth/logout')
    client.get(f'/auth/login?mock_email={sample_uopz.email}&mock_rola=uopz')

    # GET full documentation details
    response = client.get(f'/api/v1/dokumentacja/{praktyka.id}/pelna')
    assert response.status_code == 200
    assert response.get_json()["data"]["documents"]["harmonogram"]["status"] == "Approved"

    # UOPZ approves documentation (sets practice status to Approved or Closed/Rejected)
    # Wait, valid transition from Under_Review is Approved or Rejected
    response = client.patch(f'/api/v1/dokumentacja/{praktyka.id}', json={"status": "Approved"})
    assert response.status_code == 200
    assert Praktyka.query.get(praktyka.id).status == "Approved"
