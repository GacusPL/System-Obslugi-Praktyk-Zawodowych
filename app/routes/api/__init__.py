from flask import Blueprint
from app.routes.api.helpers import api_error, api_success

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Import and register sub-blueprints
from app.routes.api.praktyki import praktyki_api_bp
from app.routes.api.harmonogramy import harmonogramy_api_bp
from app.routes.api.dziennik import dziennik_api_bp
from app.routes.api.efekty import efekty_api_bp
from app.routes.api.sprawozdanie import sprawozdanie_api_bp
from app.routes.api.ankieta import ankieta_api_bp
from app.routes.api.karta_praktyki import karta_praktyki_api_bp
from app.routes.api.dokumentacja import dokumentacja_api_bp
from app.routes.api.wniosek import wniosek_api_bp
from app.routes.api.egzamin import egzamin_api_bp
from app.routes.api.administracja import administracja_api_bp
from app.routes.api.files import files_api_bp
from app.routes.api.documents import documents_api_bp
api_bp.register_blueprint(praktyki_api_bp)
api_bp.register_blueprint(harmonogramy_api_bp)
api_bp.register_blueprint(dziennik_api_bp)
api_bp.register_blueprint(efekty_api_bp)
api_bp.register_blueprint(sprawozdanie_api_bp)
api_bp.register_blueprint(ankieta_api_bp)
api_bp.register_blueprint(karta_praktyki_api_bp)
api_bp.register_blueprint(dokumentacja_api_bp)
api_bp.register_blueprint(wniosek_api_bp)
api_bp.register_blueprint(egzamin_api_bp)
api_bp.register_blueprint(administracja_api_bp)
api_bp.register_blueprint(files_api_bp)
api_bp.register_blueprint(documents_api_bp)

@api_bp.route('/health')
def health():
    from app import db
    try:
        db.session.execute(db.text('SELECT 1'))
        return api_success({"status": "ok"})
    except Exception:
        return api_error("DATABASE_UNAVAILABLE", "Baza danych jest niedostępna", status=503)

# Global API error handlers
@api_bp.app_errorhandler(400)
def bad_request(error):
    return api_error("BAD_REQUEST", str(error.description) if hasattr(error, 'description') else "Błędne zapytanie", status=400)

@api_bp.app_errorhandler(401)
def unauthorized(error):
    return api_error("UNAUTHORIZED", "Brak uwierzytelnienia", status=401)

@api_bp.app_errorhandler(403)
def forbidden(error):
    return api_error("FORBIDDEN", "Brak uprawnień do tego zasobu", status=403)

@api_bp.app_errorhandler(404)
def not_found(error):
    return api_error("NOT_FOUND", "Zasób nie istnieje", status=404)

@api_bp.app_errorhandler(422)
def unprocessable_entity(error):
    # Support for validation errors
    details = getattr(error, "data", {}).get("messages", None)
    return api_error("UNPROCESSABLE_ENTITY", "Błąd walidacji danych", details=details, status=422)

@api_bp.app_errorhandler(500)
def internal_server_error(error):
    return api_error("INTERNAL_SERVER_ERROR", "Wystąpił wewnętrzny błąd serwera", status=500)
