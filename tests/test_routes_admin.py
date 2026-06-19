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

def test_admin_create_student_without_profile(client, db_session):
    from app.models import Student
    client.get('/auth/login?mock_email=admin_create@ans-elblag.pl&mock_rola=administrator')

    response = client.post('/admin/users/new', data={
        'imie': 'Nowy', 'nazwisko': 'Student', 'email': 'nowy.student@ans-elblag.pl',
        'rola': 'student', 'haslo': 'tajne123'
    }, follow_redirects=False)
    assert response.status_code == 302

    user = Uzytkownik.query.filter_by(email='nowy.student@ans-elblag.pl').first()
    assert user is not None
    assert user.rola == 'student'
    # Profil studenta NIE jest tworzony - student uzupełni go sam
    assert Student.query.filter_by(uzytkownik_id=user.id).first() is None

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


def test_admin_archive_and_restore_praktyka(client, db_session, sample_student, sample_zaklad, sample_uopz):
    from datetime import date
    from app.models import Praktyka
    p = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=date(2026, 1, 1), termin_do=date(2026, 6, 1),
        rok_akademicki="2025/2026", status="Draft",
    )
    db_session.add(p)
    db_session.commit()

    client.get('/auth/login?mock_email=admin_arch@ans-elblag.pl&mock_rola=administrator')

    r = client.post(f'/admin/praktyki/{p.id}/archive', follow_redirects=False)
    assert r.status_code == 302
    assert Praktyka.query.get(p.id).archived is True

    r = client.post(f'/admin/praktyki/{p.id}/restore', follow_redirects=False)
    assert r.status_code == 302
    assert Praktyka.query.get(p.id).archived is False

    client.get('/auth/logout')


def test_admin_soft_delete_praktyka_via_api(client, db_session, sample_student, sample_zaklad, sample_uopz):
    from datetime import date
    from app.models import Praktyka
    p = Praktyka(
        student_id=sample_student.id, zaklad_id=sample_zaklad.id, uopz_id=sample_uopz.id,
        termin_od=date(2026, 1, 1), termin_do=date(2026, 6, 1),
        rok_akademicki="2025/2026", status="Draft",
    )
    db_session.add(p)
    db_session.commit()

    client.get(f'/auth/login?mock_email={sample_student.uzytkownik.email}&mock_rola=student')
    r = client.delete(f'/api/v1/praktyki/{p.id}')
    assert r.status_code == 200
    # Dane są zachowane (soft-delete), nie usunięte z bazy
    refreshed = Praktyka.query.get(p.id)
    assert refreshed is not None
    assert refreshed.archived is True
