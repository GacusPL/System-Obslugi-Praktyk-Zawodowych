import pytest
from flask import url_for
from app.models import Uzytkownik, Student, ZakladPracy, Praktyka

def test_dashboard_roles_rendering(client, db_session):
    # 1. Niezalogowany -> redirect do /auth/login
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.location

    # 2. Zalogowany jako student
    u_student = Uzytkownik(imie="Jan", nazwisko="Kowalski", email="jan@ans-elblag.pl", rola="student")
    u_student.set_password("pass")
    db_session.add(u_student)
    db_session.commit()
    
    student = Student(
        uzytkownik_id=u_student.id,
        nr_albumu="12345",
        kierunek="Informatyka",
        specjalnosc="IO",
        semestr=6,
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student)
    db_session.commit()

    # Log in
    client.get('/auth/login?mock_email=jan@ans-elblag.pl&mock_rola=student')
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Dashboard Studenta" in response.data or b"Witaj w SOPZ!" in response.data
    assert b"student" in response.data

    # Logout
    client.get('/auth/logout')

    # 3. Zalogowany jako ZOPZ
    u_zopz = Uzytkownik(imie="Adam", nazwisko="Zopz", email="zopz@ans-elblag.pl", rola="zopz")
    u_zopz.set_password("pass")
    db_session.add(u_zopz)
    db_session.commit()

    client.get('/auth/login?mock_email=zopz@ans-elblag.pl&mock_rola=zopz')
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Opiekun Zak\xc5\x82adowy" in response.data or b"zopz" in response.data
    client.get('/auth/logout')

    # 4. Zalogowany jako administrator
    u_admin = Uzytkownik(imie="Admin", nazwisko="Test", email="admin@ans-elblag.pl", rola="administrator")
    u_admin.set_password("pass")
    db_session.add(u_admin)
    db_session.commit()

    client.get('/auth/login?mock_email=admin@ans-elblag.pl&mock_rola=administrator')
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Dashboard Administratora" in response.data
    assert b"administrator" in response.data
    client.get('/auth/logout')


def test_navigation_role_rbac_restrictions(client, db_session):
    # Setup users
    u_student = Uzytkownik(imie="Jan", nazwisko="Kowalski", email="jan@ans-elblag.pl", rola="student")
    u_student.set_password("pass")
    
    u_admin = Uzytkownik(imie="Admin", nazwisko="Test", email="admin@ans-elblag.pl", rola="administrator")
    u_admin.set_password("pass")

    db_session.add_all([u_student, u_admin])
    db_session.commit()
    
    student = Student(
        uzytkownik_id=u_student.id,
        nr_albumu="12345",
        kierunek="Informatyka",
        specjalnosc="IO",
        semestr=6,
        forma_studiow="stacjonarne",
        rok_akademicki="2025/2026"
    )
    db_session.add(student)
    db_session.commit()

    # 1. Student attempts to access admin users page
    client.get('/auth/login?mock_email=jan@ans-elblag.pl&mock_rola=student')
    response = client.get('/admin/users')
    assert response.status_code == 403 or response.status_code == 302 # Redirect or Forbidden depending on RBAC
    client.get('/auth/logout')

    # 2. Admin accesses admin users page
    client.get('/auth/login?mock_email=admin@ans-elblag.pl&mock_rola=administrator')
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b"Zarz\xc4\x85dzanie U\xc5\xbcytkownikami" in response.data
    client.get('/auth/logout')
