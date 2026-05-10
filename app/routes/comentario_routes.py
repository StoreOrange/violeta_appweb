from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, current_app
from app.crud.comentario_crud import *
from app.crud.proyecto_crud import listar_proyectos
from app.crud.tarea_crud import listar_tareas, obtener_tarea_por_id, actualizar_tarea
from app.crud.usuario_crud import listar_usuarios, obtener_usuario_por_id
from app.crud.adjunto_crud import listar_adjuntos, crear_adjunto, obtener_adjunto_por_id, eliminar_adjunto
from app.crud.estado_crud import listar_estados
from app.utils.email import get_task_involved_recipient_emails, send_new_comment_email
from app.utils.uploads import validate_upload, save_upload
from datetime import datetime
import os

comentario_bp = Blueprint('comentario', __name__, url_prefix='/comentarios')


def _get_current_user_id():
    return session.get('user_id') or session.get('idusuario') or 1

@comentario_bp.route('/', methods=['GET', 'POST'])
def vista_comentarios():
    proyectos = listar_proyectos()
    tareas = listar_tareas()
    usuarios = listar_usuarios()
    adjuntos = listar_adjuntos()
    estados = listar_estados()

    idproyecto = request.args.get('idproyecto', type=int)
    idtarea = request.args.get('idtarea', type=int)
    tareas_filtradas = [t for t in tareas if (not idproyecto or t.idproyecto == idproyecto)]

    comentarios_tarea = []
    tarea_sel = None
    if idtarea:
        tarea_sel = obtener_tarea_por_id(idtarea)
        comentarios_tarea = tarea_sel.comentarios if tarea_sel else []

    now = datetime.now().strftime('%Y-%m-%dT%H:%M')

    # --- REGISTRO DE NUEVO COMENTARIO CON ARCHIVO ---
    if request.method == 'POST':
        form = request.form
        comentario = (form.get('comentario') or '').strip()
        idtarea_form = form.get('idtarea')
        idestado = form.get('idestado')
        idusuario = _get_current_user_id()
        notificar_email = form.get('notificar_email') == 'on'

        if not idtarea_form:
            flash('Debes seleccionar una tarea para registrar el comentario.')
            return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto))

        if not idestado:
            flash('Debes seleccionar un estado para registrar el avance del ticket.')
            return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto, idtarea=idtarea_form))

        if not comentario:
            flash('Debes escribir un comentario para registrar el avance del ticket.')
            return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto, idtarea=idtarea_form))

        # --- MANEJO DE ARCHIVO ADJUNTO ---
        idadjunto = None
        file = request.files.get('adjunto')  # <input name="adjunto">
        if file and file.filename:
            is_valid, error_message = validate_upload(file)
            if not is_valid:
                flash(error_message)
                return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto, idtarea=idtarea_form))
            ruta_archivo = save_upload(file)
            adjunto_obj = crear_adjunto(
                ruta_archivo=ruta_archivo,
                tipo=file.mimetype,
                fecha_subida=datetime.now(),
                idusuario=idusuario,
                descripcion='Adjunto de comentario'
            )
            idadjunto = adjunto_obj.idadjunto
        else:
            # Por si se selecciona uno ya existente por id (si tu form lo soporta, opcional)
            idadjunto_form = form.get('idadjunto') or None
            if idadjunto_form and str(idadjunto_form).isdigit():
                idadjunto = int(idadjunto_form)

        fecha_str = form.get('fecha')
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            except Exception:
                fecha = datetime.now()
        else:
            fecha = datetime.now()

        tarea_actual = obtener_tarea_por_id(idtarea_form)
        if not tarea_actual:
            flash('La tarea seleccionada no existe o ya no esta disponible.')
            return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto))

        comentario_anterior = None
        if tarea_actual and tarea_actual.comentarios:
            comentario_anterior = max(
                tarea_actual.comentarios,
                key=lambda c: c.fecha or datetime.min
            )
        if tarea_actual and idestado and str(tarea_actual.idestado) != str(idestado):
            actualizar_tarea(idtarea_form, {"idestado": idestado})

        nuevo_comentario = crear_comentario(
            idtarea=idtarea_form,
            idusuario=idusuario,
            comentario=comentario,
            fecha=fecha,
            idadjunto=idadjunto,
            idestado=idestado
        )
        if notificar_email:
            try:
                recipients = get_task_involved_recipient_emails(tarea_actual, include_commenters=True)
                if recipients and tarea_actual:
                    autor = obtener_usuario_por_id(idusuario)
                    ok, error = send_new_comment_email(
                        tarea_actual,
                        nuevo_comentario.comentario,
                        autor,
                        nuevo_comentario.fecha,
                        comentario_anterior,
                        recipients
                    )
                    if not ok:
                        current_app.logger.warning('Email not sent: %s', error)
            except Exception as exc:
                current_app.logger.exception('Email send failed: %s', exc)
        flash("Comentario agregado correctamente.")
        return redirect(url_for('comentario.vista_comentarios', idproyecto=idproyecto, idtarea=idtarea_form))

    return render_template(
        'comentarios/comentarios_view.html',
        proyectos=proyectos,
        tareas=tareas_filtradas,
        usuarios=usuarios,
        adjuntos=adjuntos,
        estados=estados,
        idproyecto=idproyecto,
        idtarea=idtarea,
        comentarios=comentarios_tarea,
        tarea_sel=tarea_sel,
        now=now
    )

@comentario_bp.route('/editar/<int:idcomentario>', methods=['POST'])
def editar_comentario(idcomentario):
    datos = request.form.to_dict()
    actualizar_comentario(idcomentario, datos)
    return redirect(url_for('comentario.vista_comentarios'))

@comentario_bp.route('/eliminar/<int:idcomentario>', methods=['POST'])
def eliminar_comentario_view(idcomentario):
    # Opcional: elimina adjunto físico también si lo deseas
    comentario = obtener_comentario_por_id(idcomentario)
    if comentario and comentario.idadjunto:
        adjunto = obtener_adjunto_por_id(comentario.idadjunto)
        if adjunto and adjunto.ruta_archivo and os.path.exists(adjunto.ruta_archivo):
            try:
                os.remove(adjunto.ruta_archivo)
            except Exception as e:
                print(f"Error eliminando archivo adjunto: {e}")
        eliminar_adjunto(comentario.idadjunto)
    eliminar_comentario(idcomentario)
    return redirect(url_for('comentario.vista_comentarios'))

@comentario_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([c.as_dict() for c in listar_comentarios()])
