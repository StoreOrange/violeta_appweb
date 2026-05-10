from datetime import datetime
import os

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, send_file

from app.crud.adjunto_crud import listar_adjuntos, crear_adjunto, eliminar_adjunto, obtener_adjunto_por_id
from app.utils.uploads import validate_upload, save_upload


adjunto_bp = Blueprint('adjunto', __name__, url_prefix='/adjuntos')


@adjunto_bp.route('/')
def vista_adjuntos():
    adjuntos = listar_adjuntos()
    return render_template('adjuntos/adjuntos_view.html', adjuntos=adjuntos)


@adjunto_bp.route('/nuevo', methods=['POST'])
def nuevo_adjunto():
    file = request.files.get('adjunto')
    descripcion = request.form.get('descripcion', '')
    idusuario = request.form.get('idusuario', None)

    is_valid, error_message = validate_upload(file)
    if not is_valid:
        flash(error_message, 'danger')
        return redirect(url_for('adjunto.vista_adjuntos'))

    ruta_archivo = save_upload(file)
    crear_adjunto(
        ruta_archivo=ruta_archivo,
        tipo=file.mimetype,
        fecha_subida=datetime.now(),
        idusuario=idusuario,
        descripcion=descripcion
    )
    flash('Archivo subido correctamente.', 'success')
    return redirect(url_for('adjunto.vista_adjuntos'))


@adjunto_bp.route('/descargar/<int:idadjunto>')
def descargar_adjunto_view(idadjunto):
    adjunto = obtener_adjunto_por_id(idadjunto)
    if adjunto and adjunto.ruta_archivo and os.path.exists(adjunto.ruta_archivo):
        return send_file(adjunto.ruta_archivo, as_attachment=True)
    flash('Archivo no encontrado', 'warning')
    return redirect(url_for('adjunto.vista_adjuntos'))


@adjunto_bp.route('/eliminar/<int:idadjunto>', methods=['POST'])
def eliminar_adjunto_view(idadjunto):
    adjunto = obtener_adjunto_por_id(idadjunto)
    if adjunto:
        eliminar_adjunto(idadjunto)
        flash('Adjunto eliminado correctamente.', 'success')
    else:
        flash('Adjunto no encontrado.', 'danger')
    return redirect(url_for('adjunto.vista_adjuntos'))


@adjunto_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([a.as_dict() for a in listar_adjuntos()])
