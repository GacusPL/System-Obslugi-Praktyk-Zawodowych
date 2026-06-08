import pytest
import os
from datetime import date
from app import db
from app.models import Uzytkownik, Student, ZakladPracy, Praktyka, Dokument

def test_document_download_ownership(client, db_session):
    # Setup users
    u_student1 = Uzytkownik(imie="Student1", nazwisko="Kowalski", email="student1@ans-elblag.pl", rola="student")
    u_student1.set_password("pass")
    
    u_student2 = Uzytkownik(imie="Student2", nazwisko="Nowak", email="student2@ans-elblag.pl", rola="student")
    u_student2.set_password("pass")
    
    u_admin = Uzytkownik(imie="Admin", nazwisko="Test", email="admin@ans-elblag.pl", rola="administrator")
    u_admin.set_password("pass")

    u_uopz = Uzytkownik(imie="Uopz", nazwisko="Test", email="uopz@ans-elblag.pl", rola="uopz")
    u_uopz.set_password("pass")

    db_session.add_all([u_student1, u_student2, u_admin, u_uopz])
    db_session.commit()

    s1 = Student(uzytkownik_id=u_student1.id, nr_albumu="1", kierunek="INF", specjalnosc="IO", semestr=6, forma_studiow="stacjonarne", rok_akademicki="2025/2026")
    s2 = Student(uzytkownik_id=u_student2.id, nr_albumu="2", kierunek="INF", specjalnosc="IO", semestr=6, forma_studiow="stacjonarne", rok_akademicki="2025/2026")
    z = ZakladPracy(nazwa="Test", adres="Test", nip="1234567890", zopz_imie="Adam", zopz_nazwisko="Zopz", zopz_stanowisko="Boss", zopz_wyksztalcenie="MSc", status="Approved")
    db_session.add_all([s1, s2, z])
    db_session.commit()

    p1 = Praktyka(student_id=s1.id, zaklad_id=z.id, uopz_id=u_uopz.id, termin_od=date(2026, 7, 1), termin_do=date(2026, 9, 30), rok_akademicki="2025/2026", status="Draft")
    p2 = Praktyka(student_id=s2.id, zaklad_id=z.id, uopz_id=u_uopz.id, termin_od=date(2026, 7, 1), termin_do=date(2026, 9, 30), rok_akademicki="2025/2026", status="Draft")
    db_session.add_all([p1, p2])
    db_session.commit()

    # Create temporary file to test downloading
    temp_file_path = os.path.abspath("temp_test_doc.pdf")
    with open(temp_file_path, "w") as f:
        f.write("PDF mock content")

    doc1 = Dokument(praktyka_id=p1.id, typ="zal_nr2a", sciezka_pliku=temp_file_path, status="Closed")
    db_session.add(doc1)
    db_session.commit()

    # 1. Student1 downloads their own document (happy)
    client.get('/auth/login?mock_email=student1@ans-elblag.pl&mock_rola=student')
    response = client.get(f'/api/v1/documents/{doc1.id}/download')
    assert response.status_code == 200
    assert response.data == b"PDF mock content"
    response.close()
    client.get('/auth/logout')

    # 2. Student2 attempts to download Student1's document (403 forbidden)
    client.get('/auth/login?mock_email=student2@ans-elblag.pl&mock_rola=student')
    response = client.get(f'/api/v1/documents/{doc1.id}/download')
    assert response.status_code == 403
    response.close()
    client.get('/auth/logout')

    # 3. Admin downloads Student1's document (happy)
    client.get('/auth/login?mock_email=admin@ans-elblag.pl&mock_rola=administrator')
    response = client.get(f'/api/v1/documents/{doc1.id}/download')
    assert response.status_code == 200
    response.close()
    client.get('/auth/logout')

    # Cleanup
    os.remove(temp_file_path)


def test_document_generate_api(client, db_session):
    # Setup users
    u_student1 = Uzytkownik(imie="Student1", nazwisko="Kowalski", email="student1@ans-elblag.pl", rola="student")
    u_student1.set_password("pass")
    u_uopz = Uzytkownik(imie="Uopz", nazwisko="Test", email="uopz@ans-elblag.pl", rola="uopz")
    u_uopz.set_password("pass")

    db_session.add_all([u_student1, u_uopz])
    db_session.commit()

    s1 = Student(uzytkownik_id=u_student1.id, nr_albumu="1", kierunek="INF", specjalnosc="IO", semestr=6, forma_studiow="stacjonarne", rok_akademicki="2025/2026")
    z = ZakladPracy(nazwa="Test", adres="Test", nip="1234567890", zopz_imie="Adam", zopz_nazwisko="Zopz", zopz_stanowisko="Boss", zopz_wyksztalcenie="MSc", status="Approved")
    db_session.add_all([s1, z])
    db_session.commit()

    p1 = Praktyka(student_id=s1.id, zaklad_id=z.id, uopz_id=u_uopz.id, termin_od=date(2026, 7, 1), termin_do=date(2026, 9, 30), rok_akademicki="2025/2026", status="Draft")
    db_session.add(p1)
    db_session.commit()

    # Generate document via API
    client.get('/auth/login?mock_email=student1@ans-elblag.pl&mock_rola=student')
    response = client.post('/api/v1/documents/generate', json={
        "praktyka_id": p1.id,
        "typ": "zal_nr2a"
    })
    
    assert response.status_code == 201
    res_data = response.get_json()
    assert "data" in res_data
    assert res_data["data"]["typ"] == "zal_nr2a"
    assert "download_url" in res_data["data"]

    # Verify document exists in DB and file exists
    doc = Dokument.query.get(res_data["data"]["id"])
    assert doc is not None
    assert os.path.exists(doc.sciezka_pliku)

    # Cleanup file
    os.remove(doc.sciezka_pliku)
    client.get('/auth/logout')
