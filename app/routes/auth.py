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
    
    is_dev = current_app.config.get('E2E') or current_app.config.get('TESTING')
    
    # In testing or E2E environment we can bypass Microsoft OAuth redirect by providing a mock login
    if is_dev:
        mock_email = request.args.get('mock_email')
        if mock_email:
            user = Uzytkownik.query.filter_by(email=mock_email).first()
            if not user:
                names_map = {
                    "admin@ans-elblag.pl": ("Admin", "Test"),
                    "dyrektor@ans-elblag.pl": ("Jan", "Dyrektor"),
                    "uopz@ans-elblag.pl": ("Anna", "Nowak"),
                    "zopz@ans-elblag.pl": ("Adam", "Zopz"),
                    "zopz2@ans-elblag.pl": ("Marek", "Kowalski"),
                    "student1@ans-elblag.pl": ("Kacper", "Student"),
                    "student2@ans-elblag.pl": ("Jan", "Kowalski"),
                    "student3@ans-elblag.pl": ("Michał", "Wiśniewski"),
                    "jan.kowalski@ans-elblag.pl": ("Jan", "Kowalski")
                }
                imie, nazwisko = names_map.get(mock_email, ("Mock", "User"))
                user = Uzytkownik(
                    imie=imie,
                    nazwisko=nazwisko,
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

    dev_users = []
    # If microsoft param is set, try to redirect to Microsoft OAuth
    if request.args.get('microsoft') == 'true':
        try:
            auth_url = get_auth_url()
            return redirect(auth_url)
        except Exception as e:
            current_app.logger.exception("Błąd inicjacji logowania Microsoft")
            flash("Nie można nawiązać połączenia z usługą Microsoft OAuth (sprawdź konfigurację MICROSOFT_* oraz dostęp do sieci). Spróbuj ponownie.", "danger")
            return redirect(url_for('auth.login'))

    if is_dev or current_app.config.get('TESTING'):
        try:
            dev_users = Uzytkownik.query.order_by(Uzytkownik.rola, Uzytkownik.nazwisko).all()
        except Exception:
            pass

    return render_template('auth/login.html', is_dev=is_dev, dev_users=dev_users)

@auth_bp.route('/callback')
@limiter.limit("10 per minute")
def callback():
    code = request.args.get('code')
    if not code:
        flash("Błąd logowania: brak kodu autoryzacyjnego.", "danger")
        return redirect(url_for('auth.login'))
        
    try:
        token_response = get_token_from_code(code)
        if "error" in token_response:
            flash(f"Błąd logowania Microsoft: {token_response.get('error_description')}", "danger")
            return redirect(url_for('auth.login'))

        access_token = token_response.get('access_token')
        user_info = get_user_info(access_token)
    except Exception:
        current_app.logger.exception("Błąd wymiany kodu / pobierania danych użytkownika Microsoft")
        flash("Błąd komunikacji z usługą Microsoft (sieć/konfiguracja). Spróbuj zalogować się ponownie.", "danger")
        return redirect(url_for('auth.login'))

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

    # Zarchiwizowane konto nie może się zalogować
    if user and user.archived:
        flash("To konto zostało zarchiwizowane. Skontaktuj się z administratorem.", "danger")
        return redirect(url_for('auth.login'))

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
    is_oauth = current_user.microsoft_id is not None
    logout_user()
    flash("Zostałeś wylogowany.", "success")
    
    if is_oauth:
        import urllib.parse
        tenant = current_app.config.get('MICROSOFT_TENANT_ID', 'common')
        post_logout = url_for('auth.login', _external=True)
        encoded_redirect = urllib.parse.quote_plus(post_logout)
        logout_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?post_logout_redirect_uri={encoded_redirect}"
        return redirect(logout_url)
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/waiting')
@login_required
def waiting():
    if current_user.rola is not None:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/waiting.html')
