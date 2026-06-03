import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_type, max_size_mb=10):
    if not file or file.filename == '':
        return None, "Brak pliku"

    if not allowed_file(file.filename):
        return None, "Niedozwolony typ pliku (dozwolone: pdf, png, jpg, jpeg)"

    # Check file size (need to seek to end, get length, then seek back)
    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    file.seek(0)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        return None, f"Plik przekracza maksymalny rozmiar {max_size_mb}MB"

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    # Create directory structure inside app/static/uploads/<typ>/<uuid>/
    # To keep it within the workspace, use relative path relative to app's static root
    # Wait, the app root is app/. So app/static/uploads/...
    # Let's get the absolute path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', upload_type, unique_id))
    os.makedirs(base_dir, exist_ok=True)

    dest_path = os.path.join(base_dir, filename)
    file.save(dest_path)

    # Return relative path for web access / database storing
    rel_path = f"uploads/{upload_type}/{unique_id}/{filename}"
    return rel_path, None
