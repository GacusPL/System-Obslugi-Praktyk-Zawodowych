import pytest
import threading
import time
from app import create_app, db
from app.models import Uzytkownik, Student, ZakladPracy, Praktyka
from playwright.sync_api import sync_playwright

def run_server(app):
    # Run the server on a random port or port 5001
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)

@pytest.fixture(scope='session')
def server():
    # Force loading 'testing' config with debug=True so mock login works!
    app = create_app('testing')
    from config import BASE_DIR
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR}/test_e2e.db'
    app.config['DEBUG'] = True  # crucial to allow is_dev check for mock login
    app.config['E2E'] = True
    
    # We must create all tables on the temporary db
    with app.app_context():
        db.create_all()
        # Seed initial data for E2E tests
        admin = Uzytkownik(imie="Admin", nazwisko="Test", email="admin@ans-elblag.pl", rola="administrator")
        admin.set_password("admin123")
        
        student_user = Uzytkownik(imie="Jan", nazwisko="Kowalski", email="jan.kowalski@ans-elblag.pl", rola="student")
        student_user.set_password("student123")
        
        uopz = Uzytkownik(imie="Anna", nazwisko="Nowak", email="uopz@ans-elblag.pl", rola="uopz")
        uopz.set_password("uopz123")
        
        zopz = Uzytkownik(imie="Adam", nazwisko="Zopz", email="zopz@ans-elblag.pl", rola="zopz")
        zopz.set_password("zopz123")
        
        dyrektor = Uzytkownik(imie="Dyrektor", nazwisko="Kowalski", email="dyrektor@ans-elblag.pl", rola="dyrektor")
        dyrektor.set_password("dyrektor123")
        
        db.session.add_all([admin, student_user, uopz, zopz, dyrektor])
        db.session.commit()
        
        student = Student(
            uzytkownik_id=student_user.id,
            nr_albumu="12345",
            kierunek="Informatyka",
            specjalnosc="Inżynieria Oprogramowania",
            semestr=6,
            forma_studiow="stacjonarne",
            rok_akademicki="2025/2026"
        )
        
        zaklad = ZakladPracy(
            nazwa="Firma Testowa",
            adres="Elbląg, ul. Testowa 1",
            nip="1234567890",
            zopz_imie="Adam",
            zopz_nazwisko="Zopz",
            zopz_stanowisko="Kierownik IT",
            zopz_wyksztalcenie="Wyższe",
            status="Approved"
        )
        
        db.session.add_all([student, zaklad])
        db.session.commit()

    # Start Flask app in a background thread
    thread = threading.Thread(target=run_server, args=(app,))
    thread.daemon = True
    thread.start()
    
    # Wait for the server to start
    time.sleep(1.5)
    
    yield "http://127.0.0.1:5001"
    
    with app.app_context():
        db.drop_all()

@pytest.fixture(scope='function')
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()
