from flask import Blueprint, redirect, request, url_for, render_template, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import Uzytkownik
from app.auth import get_auth_url, get_token_from_code, get_user_info

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.rola is None:
            return redirect(url_for('auth.waiting'))
        return redirect(url_for('main.dashboard'))
    
    is_dev = (current_app.config.get('DEBUG') and not current_app.config.get('TESTING')) or current_app.config.get('E2E')
    
    # In testing or debug environment we can bypass Microsoft OAuth redirect by providing a mock login
    if current_app.config.get('TESTING') or is_dev:
        mock_email = request.args.get('mock_email')
        if mock_email:
            user = Uzytkownik.query.filter_by(email=mock_email).first()
            if not user:
                user = Uzytkownik(
                    imie="Mock",
                    nazwisko="User",
                    email=mock_email,
                    rola=request.args.get('mock_rola'),
                    haslo_hash="mock"
                )
                db.session.add(user)
                db.session.commit()
            login_user(user)
            if user.rola is None:
                return redirect(url_for('auth.waiting'))
            return redirect(url_for('main.dashboard'))

    # If microsoft param is set or we are not in dev/testing mode, try to redirect to Microsoft OAuth
    if request.args.get('microsoft') == 'true' or not is_dev:
        try:
            auth_url = get_auth_url()
            return redirect(auth_url)
        except ValueError as e:
            flash("Nie można nawiązać połączenia z usługą Microsoft OAuth. Sprawdź konfigurację MICROSOFT_AUTHORITY / tenant ID lub użyj logowania lokalnego.", "danger")
            # If we are not in dev mode, redirecting here would cause a loop, so let's render login page instead of looping
            if not is_dev:
                return render_template('auth/login.html', is_dev=is_dev, error=str(e))
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html', is_dev=is_dev)

@auth_bp.route('/callback')
@limiter.limit("10 per minute")
def callback():
    code = request.args.get('code')
    if not code:
        flash("Błąd logowania: brak kodu autoryzacyjnego.", "danger")
        return redirect(url_for('auth.login'))
        
    token_response = get_token_from_code(code)
    if "error" in token_response:
        flash(f"Błąd logowania Microsoft: {token_response.get('error_description')}", "danger")
        return redirect(url_for('auth.login'))
        
    access_token = token_response.get('access_token')
    user_info = get_user_info(access_token)
    if not user_info:
        flash("Nie udało się pobrać informacji o użytkowniku z Microsoft Graph.", "danger")
        return redirect(url_for('auth.login'))
        
    email = user_info.get('mail') or user_info.get('userPrincipalName')
    imie = user_info.get('givenName', 'Użytkownik')
    nazwisko = user_info.get('surname', 'Microsoft')
    microsoft_id = user_info.get('id')
    
    if not email:
        flash("Konto Microsoft nie posiada powiązanego adresu e-mail.", "danger")
        return redirect(url_for('auth.login'))
        
    user = Uzytkownik.query.filter_by(email=email).first()
    
    if not user:
        # Create user with rola = None (first login)
        user = Uzytkownik(
            imie=imie,
            nazwisko=nazwisko,
            email=email,
            rola=None,
            microsoft_id=microsoft_id,
            haslo_hash="OAuthUser"
        )
        db.session.add(user)
        db.session.commit()
        
    login_user(user)
    
    if user.rola is None:
        return redirect(url_for('auth.waiting'))
        
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Zostałeś wylogowany.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/waiting')
@login_required
def waiting():
    if current_user.rola is not None:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/waiting.html')
