import pytest
from app import db
from app.models import Uzytkownik

def test_admin_update_user_role(client, db_session):
    # Setup test user without role
    pending_user = Uzytkownik(imie="Test", nazwisko="Pending", email="pending@ans-elblag.pl", rola=None)
    pending_user.set_password("pass")
    db_session.add(pending_user)
    db_session.commit()

    # Log in as admin
    client.get('/auth/login?mock_email=admin_role@ans-elblag.pl&mock_rola=administrator')
    
    # 1. Update role to student (happy path)
    response = client.post(
        f'/admin/users/{pending_user.id}/role',
        data={'rola': 'student'},
        follow_redirects=False
    )
    assert response.status_code == 302
    assert response.location.endswith('/admin/users')
    
    updated_user = Uzytkownik.query.get(pending_user.id)
    assert updated_user.rola == 'student'

    # 2. Update role to invalid role (400 check)
    response = client.post(
        f'/admin/users/{pending_user.id}/role',
        data={'rola': 'invalid_role'},
        follow_redirects=False
    )
    assert response.status_code == 400

    client.get('/auth/logout')

def test_non_admin_update_user_role(client, db_session):
    pending_user = Uzytkownik(imie="Test", nazwisko="Pending", email="pending2@ans-elblag.pl", rola=None)
    pending_user.set_password("pass")
    db_session.add(pending_user)
    db_session.commit()

    # Log in as student
    client.get('/auth/login?mock_email=student_role@ans-elblag.pl&mock_rola=student')

    # Próba zmiany roli przez studenta -> 403
    response = client.post(
        f'/admin/users/{pending_user.id}/role',
        data={'rola': 'uopz'},
        follow_redirects=False
    )
    assert response.status_code == 403

    client.get('/auth/logout')
