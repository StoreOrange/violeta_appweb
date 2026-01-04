from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash, current_app
from app.crud.estado_crud import listar_estados
from app.crud.notificacion_crud import crear_notificacion
from app.crud.prioridad_crud import listar_prioridades
from app.crud.tarea_crud import *
from app.crud.proyecto_crud import listar_proyectos
from app.crud.tipo_tarea_crud import listar_tipos_tarea
from app.crud.usuario_crud import listar_usuarios
from app.utils.email import get_active_recipient_emails, send_new_task_email
from datetime import datetime
from collections import defaultdict

tarea_bp = Blueprint('tarea', __name__, url_prefix='/tareas')

# REGISTRO DE NUEVA TAREA
@tarea_bp.route('/nuevo', methods=['POST'])
def nueva_tarea():
    form = request.form
    accion = form.get('accion')
    idusuario_admin = session.get('idusuario') or 1
    idadjunto = form.get('idadjunto') or None
    if idadjunto == "":
        idadjunto = None

    tarea = crear_tarea(
        titulo=form.get('titulo'),
        descripcion=form.get('descripcion'),
        idproyecto=form.get('idproyecto'),
        idusuario_asignado=form.get('idusuario_asignado'),
        fecha_creacion=form.get('fecha_creacion'),
        fecha_limite=form.get('fecha_limite'),
        idtipo_tarea=form.get('idtipo_tarea'),
        idprioridad=form.get('idprioridad'),
        idestado=form.get('idestado'),
        idadjunto=idadjunto,
        creada_por=idusuario_admin
    )

    recipients = []
    try:
        recipients = get_active_recipient_emails()
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
        crear_notificacion(
            idusuario=tarea.idusuario_asignado,
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
                "usuario": tarea.usuario_asignado.nombre if tarea.usuario_asignado else '',
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
