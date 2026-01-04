from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, send_file
from app.crud.adjunto_crud import listar_adjuntos, crear_adjunto, eliminar_adjunto, obtener_adjunto_por_id
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from uuid import uuid4

adjunto_bp = Blueprint('adjunto', __name__, url_prefix='/adjuntos')

# Carpeta donde se guardan los archivos adjuntos
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads_adjuntos')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Listar todos los adjuntos
@adjunto_bp.route('/')
def vista_adjuntos():
    adjuntos = listar_adjuntos()
    return render_template('adjuntos/adjuntos_view.html', adjuntos=adjuntos)

# Subir un nuevo adjunto
@adjunto_bp.route('/nuevo', methods=['POST'])
def nuevo_adjunto():
    # Cambia a 'adjunto' si tu form lo envía así
    file = request.files.get('adjunto')
    descripcion = request.form.get('descripcion', '')
    idusuario = request.form.get('idusuario', None)  # Si tienes usuario logueado usa session['user_id']

    if not file or not file.filename:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('adjunto.vista_adjuntos'))

    if allowed_file(file.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        unique_prefix = str(uuid4())[:8]
        filename = f"{unique_prefix}_{secure_filename(file.filename)}"
        ruta_archivo = os.path.join(UPLOAD_FOLDER, filename)
        file.save(ruta_archivo)
        crear_adjunto(
            ruta_archivo=ruta_archivo,
            tipo=file.mimetype,
            fecha_subida=datetime.now(),
            idusuario=idusuario,
            descripcion=descripcion
        )
        flash('Archivo subido correctamente.', 'success')
    else:
        flash('Tipo de archivo no permitido.', 'danger')
    return redirect(url_for('adjunto.vista_adjuntos'))

# Descargar/ver un adjunto (este endpoint usa el blueprint adjunto)
@adjunto_bp.route('/descargar/<int:idadjunto>')
def descargar_adjunto_view(idadjunto):
    adjunto = obtener_adjunto_por_id(idadjunto)
    if adjunto and adjunto.ruta_archivo and os.path.exists(adjunto.ruta_archivo):
        return send_file(adjunto.ruta_archivo, as_attachment=True)
    flash('Archivo no encontrado', 'warning')
    return redirect(url_for('adjunto.vista_adjuntos'))

# Eliminar un adjunto
@adjunto_bp.route('/eliminar/<int:idadjunto>', methods=['POST'])
def eliminar_adjunto_view(idadjunto):
    adjunto = obtener_adjunto_por_id(idadjunto)
    if adjunto:
        # Si quieres borrar también el archivo físico del disco, descomenta lo siguiente:
        # try:
        #     if os.path.exists(adjunto.ruta_archivo):
        #         os.remove(adjunto.ruta_archivo)
        # except Exception as e:
        #     print(f"Error borrando archivo físico: {e}")
        eliminar_adjunto(idadjunto)
        flash('Adjunto eliminado correctamente.', 'success')
    else:
        flash('Adjunto no encontrado.', 'danger')
    return redirect(url_for('adjunto.vista_adjuntos'))

# API para listar todos los adjuntos en formato JSON
@adjunto_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([a.as_dict() for a in listar_adjuntos()])
