import os
from flask import Blueprint, send_file, abort, request
from flask_login import login_required, current_user
from app import db
from app.models import ZalacznikSkan, Student, Dokument, Praktyka
from app.utils.upload import save_uploaded_file
from app.routes.api.helpers import api_success, api_error

files_api_bp = Blueprint('files_api', __name__)

@files_api_bp.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    praktyka_id = request.form.get('praktyka_id')
    if not praktyka_id:
        return api_error("MISSING_PRAKTYKA_ID", "Brakujące ID praktyki", status=400)
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or praktyka.student_id != student.id:
            abort(403)
    elif current_user.rola not in ['uopz', 'administrator']:
        abort(403)
        
    file = request.files.get('skan_pdf') or request.files.get('file')
    if not file:
        return api_error("MISSING_FILE", "Brak pliku w żądaniu", status=400)
        
    path, err = save_uploaded_file(file, 'signed_docs')
    if err:
        return api_error("UPLOAD_ERROR", err, status=400)
        
    # Create or update Dokument record
    doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ='signed_karta_sprawozdanie').first()
    if not doc:
        doc = Dokument(
            praktyka_id=praktyka.id,
            typ='signed_karta_sprawozdanie',
            sciezka_pliku=path,
            status='Submitted'
        )
        db.session.add(doc)
    else:
        doc.sciezka_pliku = path
        doc.status = 'Submitted'
        
    db.session.commit()
    return api_success({"message": "Plik przesłany pomyślnie", "sciezka_pliku": path}, status=201)

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
