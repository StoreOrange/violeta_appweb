from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash, current_app
from app.crud.estado_crud import listar_estados
from app.crud.notificacion_crud import crear_notificacion
from app.crud.prioridad_crud import listar_prioridades
from app.crud.tarea_crud import *
from app.crud.proyecto_crud import listar_proyectos
from app.crud.tipo_tarea_crud import listar_tipos_tarea
from app.crud.usuario_crud import listar_usuarios
from app.crud.adjunto_crud import crear_adjunto
from app.utils.email import get_task_involved_recipient_emails, send_new_task_email
from app.utils.uploads import validate_upload, save_upload
from datetime import datetime
from collections import defaultdict

tarea_bp = Blueprint('tarea', __name__, url_prefix='/tareas')
TEAM_DESARROLLO_VALUE = 'team_desarrollo'


def _get_current_user_id():
    return session.get('user_id') or session.get('idusuario') or 1


def _get_team_desarrollo_users():
    return [u for u in listar_usuarios() if getattr(u, 'activo', False)]

# REGISTRO DE NUEVA TAREA
@tarea_bp.route('/nuevo', methods=['POST'])
def nueva_tarea():
    form = request.form
    accion = form.get('accion')
    idusuario_admin = _get_current_user_id()
    idadjunto = form.get('idadjunto') or None
    idusuario_asignado = form.get('idusuario_asignado')
    equipo_desarrollo = idusuario_asignado == TEAM_DESARROLLO_VALUE
    if idadjunto == "":
        idadjunto = None
    if equipo_desarrollo:
        idusuario_asignado = None

    file = request.files.get('adjunto')
    if file and file.filename:
        is_valid, error_message = validate_upload(file)
        if not is_valid:
            flash(error_message)
            return redirect(url_for('tarea.vista_tareas'))
        ruta_archivo = save_upload(file)
        adjunto_obj = crear_adjunto(
            ruta_archivo=ruta_archivo,
            tipo=file.mimetype,
            fecha_subida=datetime.now(),
            idusuario=idusuario_admin,
            descripcion='Adjunto de tarea'
        )
        idadjunto = adjunto_obj.idadjunto

    tarea = crear_tarea(
        titulo=form.get('titulo'),
        descripcion=form.get('descripcion'),
        idproyecto=form.get('idproyecto'),
        idusuario_asignado=idusuario_asignado,
        fecha_creacion=form.get('fecha_creacion'),
        fecha_limite=form.get('fecha_limite'),
        idtipo_tarea=form.get('idtipo_tarea'),
        idprioridad=form.get('idprioridad'),
        idestado=form.get('idestado'),
        idadjunto=idadjunto,
        creada_por=idusuario_admin,
        equipo_desarrollo=equipo_desarrollo
    )

    recipients = []
    try:
        recipients = get_task_involved_recipient_emails(tarea)
        if recipients:
            ok, error = send_new_task_email(tarea, recipients)
            if not ok:
                current_app.logger.warning('Email not sent: %s', error)
    except Exception as exc:
        current_app.logger.exception('Email send failed: %s', exc)
        recipients = []

    if form.get('enviar_notificacion') == 'on':
        mensaje = f"Se ha asignado una nueva tarea: {tarea.titulo}"
        destinatarios_txt = ', '.join(recipients) if recipients else None
        destinatarios_notificacion = (
            _get_team_desarrollo_users() if tarea.equipo_desarrollo else [tarea.usuario_asignado] if tarea.usuario_asignado else []
        )
        for usuario in destinatarios_notificacion:
            crear_notificacion(
                idusuario=usuario.idusuario,
                idtarea=tarea.idtarea,
                mensaje=mensaje,
                fecha_envio=datetime.now(),
                tipo='Tarea',
                destinatarios=destinatarios_txt
            )

    flash('Tarea registrada exitosamente')
    if accion == 'guardar_nueva':
        return redirect(url_for('tarea.vista_tareas', nuevo=1))
    return redirect(url_for('tarea.vista_tareas'))

# ELIMINAR TAREA
@tarea_bp.route('/eliminar/<int:idtarea>', methods=['POST'])
def eliminar_tarea_view(idtarea):
    eliminar_tarea(idtarea)
    flash('Tarea eliminada correctamente')
    return redirect(url_for('tarea.vista_tareas'))

# API para listar todas las tareas en JSON
@tarea_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([t.as_dict() for t in listar_tareas()])

# VISTA PRINCIPAL DE TAREAS (panel Kanban y registro)
@tarea_bp.route('/')
def vista_tareas():
    tareas = listar_tareas()
    proyectos = listar_proyectos()
    usuarios = listar_usuarios()
    estados = listar_estados()
    tipos_tarea = listar_tipos_tarea()
    prioridades = listar_prioridades()

    # Serialización para JS (proyectos y usuarios)
    proyectos_json = [
        {
            "idproyecto": p.idproyecto,
            "nombre_proyecto": p.nombre_proyecto,
            "idusuario": p.idusuario,
            "fecha_creacion": p.fecha_creacion.strftime('%Y-%m-%d') if p.fecha_creacion else ""
        }
        for p in proyectos
    ]
    usuarios_json = [
        {
            "idusuario": u.idusuario,
            "nombre": u.nombre
        }
        for u in usuarios
    ]
    usuarios_json.append(
        {
            "idusuario": TEAM_DESARROLLO_VALUE,
            "nombre": "Team Desarrollo"
        }
    )

    # Agrupar tareas por proyecto (solo las pendientes)
    tareas_por_proyecto = defaultdict(list)
    for tarea in tareas:
        if hasattr(tarea, 'idestado'):
            estado_obj = next((e for e in estados if e.idestado == int(tarea.idestado)), None)
            if estado_obj and estado_obj.nombre_estado != 'Completada':
                proyecto_nombre = tarea.proyecto.nombre_proyecto if tarea.proyecto else "Sin Proyecto"
                tareas_por_proyecto[proyecto_nombre].append(tarea)

    # --- NUEVO: Serializa las tareas agrupadas para el filtro JS ---
    tareas_por_proyecto_json = {}
    for proyecto, tareas_grupo in tareas_por_proyecto.items():
        tareas_por_proyecto_json[proyecto] = []
        for tarea in tareas_grupo:
            tareas_por_proyecto_json[proyecto].append({
                "idtarea": tarea.idtarea,
                "titulo": tarea.titulo,
                "descripcion": tarea.descripcion,
                "usuario": tarea.nombre_responsable,
                "prioridad": tarea.prioridad.nombre_prioridad if tarea.prioridad else 'Sin Prioridad',
                "prioridad_color": tarea.prioridad.color if tarea.prioridad and tarea.prioridad.color else '#a386e6',
                "estado": tarea.estado.nombre_estado if tarea.estado else 'Sin Estado',
                "estado_color": tarea.estado.color if tarea.estado and tarea.estado.color else '#d3bfff',
                "fecha_limite": tarea.fecha_limite.strftime('%d-%m-%Y') if tarea.fecha_limite else ''
            })

    return render_template(
        'tareas/tareas_view.html',
        tareas=tareas,
        proyectos=proyectos,
        usuarios=usuarios,
        estados=estados,
        tipos_tarea=tipos_tarea,
        prioridades=prioridades,
        proyectos_json=proyectos_json,
        usuarios_json=usuarios_json,
        tareas_por_proyecto=tareas_por_proyecto,
        tareas_por_proyecto_json=tareas_por_proyecto_json  # <-- agrega esta línea
    )
