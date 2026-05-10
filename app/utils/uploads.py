import os
from uuid import uuid4

from werkzeug.utils import secure_filename


MAX_UPLOAD_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'heic',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt',
    'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'
}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads_adjuntos')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size(file_storage):
    stream = file_storage.stream
    current_pos = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(current_pos)
    return size


def validate_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return False, 'No se selecciono ningun archivo.'
    if not allowed_file(file_storage.filename):
        return False, 'Tipo de archivo no permitido. Usa imagenes, documentos o videos de hasta 25 MB.'
    if get_file_size(file_storage) > MAX_UPLOAD_SIZE:
        return False, 'El archivo supera el limite de 25 MB.'
    return True, None


def save_upload(file_storage):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    unique_prefix = str(uuid4())[:8]
    filename = f"{unique_prefix}_{secure_filename(file_storage.filename)}"
    ruta_archivo = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(ruta_archivo)
    return ruta_archivo
