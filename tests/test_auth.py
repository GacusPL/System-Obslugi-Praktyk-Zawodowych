import pytest
from unittest.mock import patch
from app import db
from app.models import Uzytkownik

def test_login_redirect_to_microsoft(client):
    # Default access renders the login page (200)
    response = client.get('/auth/login', follow_redirects=False)
    assert response.status_code == 200

    # Access with microsoft=true redirects to Microsoft OAuth (302)
    with patch('app.routes.auth.get_auth_url') as mock_get_url:
        mock_get_url.return_value = "https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/authorize"
        response = client.get('/auth/login?microsoft=true', follow_redirects=False)
        assert response.status_code == 302
        assert "login.microsoftonline.com" in response.location


def test_mock_login_testing(client, db_session):
    # Testing mock login feature
    response = client.get('/auth/login?mock_email=new_student@ans-elblag.pl&mock_rola=student', follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/dashboard')
    
    # Check if user was created
    user = Uzytkownik.query.filter_by(email="new_student@ans-elblag.pl").first()
    assert user is not None
    assert user.rola == 'student'

def test_oauth_callback_new_user(client, db_session):
    with patch('app.routes.auth.get_token_from_code') as mock_token, \
         patch('app.routes.auth.get_user_info') as mock_user_info:
         
        mock_token.return_value = {"access_token": "mock-token"}
        mock_user_info.return_value = {
            "mail": "brand_new_user@ans-elblag.pl",
            "givenName": "Bolek",
            "surname": "Lolek",
            "id": "ms-id-123"
        }
        
        response = client.get('/auth/callback?code=mock-code', follow_redirects=False)
        assert response.status_code == 302
        assert response.location.endswith('/auth/waiting')
        
        # Verify user creation in DB with rola=None
        user = Uzytkownik.query.filter_by(email="brand_new_user@ans-elblag.pl").first()
        assert user is not None
        assert user.rola is None
        assert user.microsoft_id == "ms-id-123"

def test_oauth_callback_existing_user(client, db_session):
    # Setup existing user
    user = Uzytkownik(imie="Existing", nazwisko="User", email="existing@ans-elblag.pl", rola="uopz")
    user.set_password("pass")
    db_session.add(user)
    db_session.commit()
    
    with patch('app.routes.auth.get_token_from_code') as mock_token, \
         patch('app.routes.auth.get_user_info') as mock_user_info:
         
        mock_token.return_value = {"access_token": "mock-token"}
        mock_user_info.return_value = {
            "mail": "existing@ans-elblag.pl",
            "givenName": "Existing",
            "surname": "User",
            "id": "ms-id-exist"
        }
        
        response = client.get('/auth/callback?code=mock-code', follow_redirects=False)
        assert response.status_code == 302
        assert response.location.endswith('/dashboard')

def test_logout(client, db_session):
    # Log in mock user
    client.get('/auth/login?mock_email=logout_test@ans-elblag.pl&mock_rola=student')
    
    # Logout
    response = client.get('/auth/logout', follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/auth/login')

def test_rbac_decorators(client, db_session):
    # 1. Unauthenticated user gets redirected to login (which behaves as 302 redirect)
    response = client.get('/admin/users', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.location
    
    # 2. Logged in as student -> accessing admin route gets 403
    client.get('/auth/login?mock_email=student_test@ans-elblag.pl&mock_rola=student')
    response = client.get('/admin/users')
    assert response.status_code == 403
    client.get('/auth/logout')
    
    # 3. Logged in as administrator -> accessing admin route gets 200
    client.get('/auth/login?mock_email=admin_test@ans-elblag.pl&mock_rola=administrator')
    response = client.get('/admin/users')
    assert response.status_code == 200
    client.get('/auth/logout')
    
    # 4. Logged in user with rola=None -> redirected to waiting page
    client.get('/auth/login?mock_email=no_role@ans-elblag.pl') # rola=None
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/auth/waiting')
