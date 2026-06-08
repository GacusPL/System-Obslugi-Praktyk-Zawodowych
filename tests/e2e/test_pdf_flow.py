import pytest
import os
from datetime import date
from app import db
from app.models import Uzytkownik, Student, ZakladPracy, Praktyka, Harmonogram, KartaPraktyki, PotwierdzenieEfektow, Sprawozdanie, WpisDziennika

@pytest.fixture
def e2e_app(app):
    from config import BASE_DIR
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR}/test_e2e.db'
    with app.app_context():
        yield app

def test_pdf_generation_and_download_flow(page, server, e2e_app):
    # Setup test practice data in test_e2e.db
    with e2e_app.app_context():
        student_user = Uzytkownik.query.filter_by(email="jan.kowalski@ans-elblag.pl").first()
        uopz_user = Uzytkownik.query.filter_by(email="uopz@ans-elblag.pl").first()
        student = Student.query.filter_by(uzytkownik_id=student_user.id).first()
        zaklad = ZakladPracy.query.filter_by(nip="1234567890").first()

        # Delete existing practices to ensure clean state
        Praktyka.query.filter_by(student_id=student.id).delete()
        db.session.commit()

        # Create new practice
        p = Praktyka(
            student_id=student.id,
            zaklad_id=zaklad.id,
            uopz_id=uopz_user.id,
            termin_od=date(2026, 7, 1),
            termin_do=date(2026, 9, 30),
            rok_akademicki="2025/2026",
            status="Draft"
        )
        db.session.add(p)
        db.session.commit()

        # Add mock checklists
        h = Harmonogram(praktyka_id=p.id, status="Approved", podpis_student=True, podpis_zopz=True, podpis_uopz=True)
        kp = KartaPraktyki(praktyka_id=p.id, status="Approved", ocena_param_zopz=5.0, ocena_param_uopz=5.0, ocena_sprawozdania=5.0)
        pe = PotwierdzenieEfektow(praktyka_id=p.id, status="Approved", godziny_zrealizowane=960)
        sp = Sprawozdanie(praktyka_id=p.id, status="Approved", sekcja_I="Sekcja I content"*10, sekcja_II="Sekcja II content"*10, sekcja_III="Sekcja III content"*10)
        
        # Add 120 approved days
        for i in range(1, 121):
            day = WpisDziennika(
                praktyka_id=p.id,
                dzien_nr=i,
                data_wpisu=date(2026, 7, 1),
                opis_prac="Mock works",
                status="Approved",
                podpis_zopz=1
            )
            db.session.add(day)
            
        p.dziennik_status = 'Closed'
        p.ankieta_wypelniona = 1
        db.session.add_all([h, kp, pe, sp])
        db.session.commit()
        
        praktyka_id = p.id
        db.session.remove()

    # 1. Login as Student and submit documentation
    page.goto(f"{server}/auth/login")
    page.click("text=Student (Jan Kowalski)")
    
    # Go to checklist
    page.wait_for_url(f"{server}/dashboard")
    page.click("text=Checklist P6")
    page.wait_for_url(f"{server}/praktyka/{praktyka_id}/dokumentacja/checklist")
    
    # Check that "Złóż kompletną dokumentację praktyki" is enabled and click it
    submit_btn = page.locator("button:has-text('Złóż kompletną dokumentację')")
    assert submit_btn.is_enabled()
    submit_btn.click()
    
    # Verify redirected back to dashboard and status is Submitted
    page.wait_for_url(f"{server}/dashboard")
    
    # Logout student
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")

    # 2. Login as UOPZ and approve documentation
    page.click("text=UOPZ")
    page.wait_for_url(f"{server}/dashboard")
    
    # Go to review
    page.click(f"a[href='/praktyka/{praktyka_id}/dokumentacja/weryfikacja']")
    page.wait_for_url(f"{server}/praktyka/{praktyka_id}/dokumentacja/weryfikacja")
    
    # Select Approved status, then submit
    page.select_option("select[name='status']", "Approved")
    
    # Handle the alert dialog automatically
    page.on("dialog", lambda dialog: dialog.accept())
    page.click("button[type='submit']")
    
    # Wait for redirect back to dashboard
    page.wait_for_url(f"{server}/dashboard")
    
    # Logout UOPZ
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")

    # 3. Login back as Student and download PDFs
    page.click("text=Student (Jan Kowalski)")
    page.wait_for_url(f"{server}/dashboard")
    
    # Navigate to checklist/download page
    page.click("text=Checklist P6")
    page.wait_for_url(f"{server}/praktyka/{praktyka_id}/dokumentacja/checklist")
    
    # Verify we see "Wygenerowane Dokumenty Oficjalne"
    assert "Wygenerowane Dokumenty Oficjalne" in page.content()
    
    # Count how many download links are visible
    pdf_links = page.locator("a:has-text('Pobierz PDF')")
    assert pdf_links.count() == 5
    
    # Verify that clicking the first link downloads a valid file
    with page.expect_download() as download_info:
        pdf_links.first.click()
    download = download_info.value
    
    # Save the downloaded file to verify size
    temp_download_path = os.path.join("D:\\Dokumenty\\GitHub\\System-Obslugi-Praktyk-Zawodowych", "downloaded_test.pdf")
    download.save_as(temp_download_path)
    assert os.path.exists(temp_download_path)
    assert os.path.getsize(temp_download_path) > 0
    os.remove(temp_download_path)
