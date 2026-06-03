import os
from flask import Blueprint, send_file, abort
from flask_login import login_required, current_user
from app.models import ZalacznikSkan, Student

files_api_bp = Blueprint('files_api', __name__)

@files_api_bp.route('/files/<string:file_uuid>', methods=['GET'])
@login_required
def download_file(file_uuid):
    # Search for scan attachment in database by matching path containing the uuid
    skan = ZalacznikSkan.query.filter(ZalacznikSkan.sciezka_pliku.like(f"%/{file_uuid}/%")).first()
    if not skan:
        abort(404)

    wniosek = skan.wniosek
    if not wniosek:
        abort(404)

    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or wniosek.student_id != student.id:
            abort(403)
    elif current_user.rola == 'zopz':
        abort(403)

    # Build absolute path to the file
    # __file__ is app/routes/api/files.py -> go 3 levels up to workspace root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    # Try different potential path layouts
    paths_to_try = [
        os.path.join(base_dir, 'app', 'static', skan.sciezka_pliku),
        os.path.join(base_dir, 'app', skan.sciezka_pliku),
        os.path.join(base_dir, skan.sciezka_pliku)
    ]

    abs_path = None
    for p in paths_to_try:
        if os.path.exists(p):
            abs_path = p
            break

    if not abs_path:
        abort(404)

    return send_file(abs_path)
