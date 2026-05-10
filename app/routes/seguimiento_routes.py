from collections import Counter, defaultdict
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from markupsafe import escape

from app import db
from app.crud.adjunto_crud import crear_adjunto
from app.crud.estado_crud import listar_estados
from app.crud.notificacion_crud import crear_notificacion
from app.crud.prioridad_crud import listar_prioridades
from app.crud.proyecto_crud import listar_proyectos
from app.crud.sprint_crud import crear_sprint, listar_sprints
from app.crud.sprint_grupo_crud import crear_grupo, listar_grupos
from app.crud.tarea_crud import crear_tarea, listar_tareas
from app.crud.tipo_tarea_crud import listar_tipos_tarea
from app.crud.usuario_crud import listar_usuarios
from app.models import Comentario, Sprint, SprintBurndown, SprintRetro, SprintRol, Tarea
from app.utils.email import get_task_involved_recipient_emails, send_new_task_email
from app.utils.uploads import save_upload, validate_upload


seguimiento_bp = Blueprint('seguimiento', __name__, url_prefix='/seguimiento')
TEAM_DESARROLLO_VALUE = 'team_desarrollo'


def _require_login():
    if not session.get('user_id'):
        flash('Debes iniciar sesion para continuar.')
        return redirect(url_for('usuario.login'))
    return None


def _get_current_user_id():
    return session.get('user_id') or session.get('idusuario') or 1


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


def _normalize_text(value):
    return (value or '').strip().lower()


def _is_closed_name(name):
    normalized = _normalize_text(name)
    return any(word in normalized for word in ('cerrad', 'terminad', 'completad', 'finalizad'))


def _is_done(tarea):
    if not tarea or not tarea.estado or not tarea.estado.nombre_estado:
        return False
    return _is_closed_name(tarea.estado.nombre_estado)


def _remaining_points(tareas):
    return sum((t.story_points or 0) for t in tareas if not _is_done(t))


def _completed_points(tareas):
    return sum((t.story_points or 0) for t in tareas if _is_done(t))


def _summarize_roles(roles):
    grouped = defaultdict(list)
    for role in roles:
        if role.usuario:
            grouped[role.rol].append(role.usuario)
    return grouped


def _task_comment_metrics(tarea):
    comentarios = sorted(
        tarea.comentarios or [],
        key=lambda item: (item.fecha or datetime.min, item.idcomentario or 0)
    )
    ultimo = comentarios[-1] if comentarios else None
    participantes = []
    vistos = set()
    for comentario in comentarios:
        if comentario.usuario and comentario.usuario.idusuario not in vistos:
            vistos.add(comentario.usuario.idusuario)
            participantes.append(comentario.usuario)
    return {
        'total_comentarios': len(comentarios),
        'ultimo_comentario': ultimo,
        'participantes': participantes,
    }


def _build_task_card(tarea):
    metrics = _task_comment_metrics(tarea)
    return {
        'idtarea': tarea.idtarea,
        'titulo': tarea.titulo,
        'descripcion': tarea.descripcion or 'Sin descripcion',
        'responsable': tarea.nombre_responsable,
        'proyecto': tarea.proyecto.nombre_proyecto if tarea.proyecto else 'Sin proyecto',
        'estado_nombre': tarea.estado.nombre_estado if tarea.estado else 'Sin estado',
        'estado_color': tarea.estado.color if tarea.estado and tarea.estado.color else '#94a3b8',
        'prioridad': tarea.prioridad.nombre_prioridad if tarea.prioridad else 'Sin prioridad',
        'prioridad_color': tarea.prioridad.color if tarea.prioridad and tarea.prioridad.color else '#cbd5e1',
        'story_points': tarea.story_points or 0,
        'backlog_rank': tarea.backlog_rank or 0,
        'sprint_id': tarea.idsprint,
        'sprint_grupo': tarea.sprint_grupo.nombre if tarea.sprint_grupo else 'Sin grupo',
        'fecha_limite': tarea.fecha_limite,
        'comentarios_total': metrics['total_comentarios'],
        'ultimo_comentario': metrics['ultimo_comentario'],
        'participantes': metrics['participantes'],
        'comment_url': url_for('comentario.vista_comentarios', idproyecto=tarea.idproyecto, idtarea=tarea.idtarea),
    }


def _redirect_back():
    idproyecto = request.form.get('return_project_id') or request.args.get('idproyecto')
    idsprint = request.form.get('return_sprint_id') or request.args.get('idsprint')
    params = {}
    if idproyecto:
        params['idproyecto'] = idproyecto
    if idsprint:
        params['idsprint'] = idsprint
    return redirect(url_for('seguimiento.vista_seguimiento', **params))


def _create_scrum_task():
    titulo = (request.form.get('titulo') or '').strip()
    idproyecto = request.form.get('idproyecto')
    idsprint = request.form.get('idsprint') or None
    idsprint_grupo = request.form.get('idsprint_grupo') or None
    idusuario_asignado = request.form.get('idusuario_asignado') or None
    equipo_desarrollo = idusuario_asignado == TEAM_DESARROLLO_VALUE
    if equipo_desarrollo:
        idusuario_asignado = None

    if not titulo or not idproyecto:
        flash('Completa al menos proyecto y titulo para crear la tarea Scrum.')
        return _redirect_back()

    sprint = Sprint.query.get(idsprint) if idsprint else None
    if sprint and sprint.estado == 'Cerrado':
        flash('El sprint esta cerrado. No se pueden crear tareas nuevas en ese sprint.')
        return _redirect_back()

    idadjunto = None
    file = request.files.get('adjunto')
    current_user_id = _get_current_user_id()
    if file and file.filename:
        is_valid, error_message = validate_upload(file)
        if not is_valid:
            flash(error_message)
            return _redirect_back()
        ruta_archivo = save_upload(file)
        adjunto_obj = crear_adjunto(
            ruta_archivo=ruta_archivo,
            tipo=file.mimetype,
            fecha_subida=datetime.now(),
            idusuario=current_user_id,
            descripcion='Adjunto de tarea Scrum'
        )
        idadjunto = adjunto_obj.idadjunto

    tarea = crear_tarea(
        titulo=titulo,
        descripcion=request.form.get('descripcion'),
        idproyecto=idproyecto,
        idusuario_asignado=idusuario_asignado,
        fecha_creacion=datetime.now(),
        fecha_limite=request.form.get('fecha_limite') or None,
        idtipo_tarea=request.form.get('idtipo_tarea') or None,
        idprioridad=request.form.get('idprioridad') or None,
        idestado=request.form.get('idestado') or None,
        idadjunto=idadjunto,
        creada_por=current_user_id,
        equipo_desarrollo=equipo_desarrollo
    )

    tarea.idsprint = idsprint
    tarea.idsprint_grupo = idsprint_grupo
    tarea.story_points = int(request.form.get('story_points') or 0)
    tarea.backlog_rank = int(request.form.get('backlog_rank') or 0)
    tarea.prioridad_scrum = request.form.get('prioridad_scrum') or 'Media'
    db.session.commit()

    recipients = []
    try:
        recipients = get_task_involved_recipient_emails(tarea)
        if recipients:
            ok, error = send_new_task_email(tarea, recipients)
            if not ok:
                current_app.logger.warning('Email not sent from Scrum module: %s', error)
    except Exception as exc:
        current_app.logger.exception('Email send failed from Scrum module: %s', exc)

    destinatarios = []
    if tarea.equipo_desarrollo:
        destinatarios = [usuario for usuario in listar_usuarios() if getattr(usuario, 'activo', False)]
    elif tarea.usuario_asignado:
        destinatarios = [tarea.usuario_asignado]

    for usuario in destinatarios:
        crear_notificacion(
            idusuario=usuario.idusuario,
            idtarea=tarea.idtarea,
            mensaje=f'Se ha creado una tarea Scrum: {tarea.titulo}',
            fecha_envio=datetime.now(),
            tipo='Scrum',
            destinatarios=', '.join(recipients) if recipients else None
        )

    flash('Tarea Scrum creada correctamente.')
    return _redirect_back()


def _build_sprint_item(sprint):
    tareas_sprint = sorted(
        sprint.tareas or [],
        key=lambda item: (
            item.backlog_rank if item.backlog_rank is not None else 999999,
            item.fecha_limite or datetime.max.date(),
            item.titulo or ''
        )
    )
    total = len(tareas_sprint)
    completadas = sum(1 for tarea in tareas_sprint if _is_done(tarea))
    progreso = int(round((completadas / total) * 100)) if total else 0
    puntos_totales = sum((t.story_points or 0) for t in tareas_sprint)
    puntos_completados = _completed_points(tareas_sprint)
    puntos_restantes = _remaining_points(tareas_sprint)
    comentarios_total = sum(len(t.comentarios or []) for t in tareas_sprint)
    adjuntos_total = sum(1 for t in tareas_sprint if t.idadjunto)
    roles = SprintRol.query.filter_by(idsprint=sprint.idsprint).all()
    retros = (
        SprintRetro.query
        .filter_by(idsprint=sprint.idsprint)
        .order_by(SprintRetro.creado_en.desc())
        .all()
    )
    burndown = (
        SprintBurndown.query
        .filter_by(idsprint=sprint.idsprint)
        .order_by(SprintBurndown.fecha.asc())
        .all()
    )
    today = datetime.now().date()
    total_days = ((sprint.fecha_fin - sprint.fecha_inicio).days + 1) if sprint.fecha_inicio and sprint.fecha_fin else 0
    elapsed_days = 0
    if sprint.fecha_inicio and sprint.fecha_fin:
        if today < sprint.fecha_inicio:
            elapsed_days = 0
        elif today > sprint.fecha_fin:
            elapsed_days = total_days
        else:
            elapsed_days = (today - sprint.fecha_inicio).days + 1
    carga = int(round((puntos_totales / sprint.capacidad) * 100)) if sprint.capacidad else 0

    return {
        'idsprint': sprint.idsprint,
        'nombre': sprint.nombre,
        'objetivo': sprint.objetivo,
        'fecha_inicio': sprint.fecha_inicio,
        'fecha_fin': sprint.fecha_fin,
        'estado': sprint.estado,
        'capacidad': sprint.capacidad,
        'goal': sprint.goal,
        'definicion_done': sprint.definicion_done,
        'proyecto': sprint.proyecto.nombre_proyecto if sprint.proyecto else '',
        'proyecto_id': sprint.idproyecto,
        'grupos': sprint.grupos or [],
        'roles': roles,
        'roles_grouped': _summarize_roles(roles),
        'retros': retros,
        'burndown': burndown,
        'tasks': [_build_task_card(tarea) for tarea in tareas_sprint],
        'total': total,
        'completadas': completadas,
        'progreso': progreso,
        'puntos_totales': puntos_totales,
        'puntos_completados': puntos_completados,
        'puntos_restantes': puntos_restantes,
        'comentarios_total': comentarios_total,
        'adjuntos_total': adjuntos_total,
        'total_days': total_days,
        'elapsed_days': elapsed_days,
        'remaining_days': max(total_days - elapsed_days, 0),
        'carga': carga,
    }


@seguimiento_bp.route('/', methods=['GET', 'POST'])
def vista_seguimiento():
    try:
        guard = _require_login()
        if guard:
            return guard

        if request.method == 'POST':
            accion = request.form.get('accion')

            if accion == 'crear_tarea_scrum':
                return _create_scrum_task()

            if accion == 'crear_sprint':
                fecha_inicio = _parse_date(request.form.get('fecha_inicio'))
                fecha_fin = _parse_date(request.form.get('fecha_fin'))
                capacidad = request.form.get('capacidad')
                capacidad_val = int(capacidad) if str(capacidad).isdigit() else None
                idproyecto = request.form.get('idproyecto')
                nombre = request.form.get('nombre')
                if not nombre:
                    count = Sprint.query.filter_by(idproyecto=idproyecto).count()
                    nombre = f'Sprint {count + 1}'
                crear_sprint(
                    nombre=nombre,
                    objetivo=request.form.get('objetivo'),
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    capacidad=capacidad_val,
                    estado=request.form.get('estado') or 'Planeado',
                    idproyecto=idproyecto
                )
                flash('Sprint creado correctamente.')
                return _redirect_back()

            if accion == 'crear_grupo':
                idsprint = request.form.get('idsprint')
                nombre = request.form.get('nombre_grupo')
                descripcion = request.form.get('descripcion_grupo')
                orden = request.form.get('orden_grupo')
                orden_val = int(orden) if str(orden).isdigit() else None
                if not idsprint or not nombre:
                    flash('Completa el sprint y el nombre del grupo.')
                    return _redirect_back()
                sprint = Sprint.query.get(idsprint)
                if sprint and sprint.estado == 'Cerrado':
                    flash('El sprint esta cerrado. No se pueden crear grupos.')
                    return _redirect_back()
                crear_grupo(nombre, descripcion, orden_val, idsprint)
                flash('Grupo creado correctamente.')
                return _redirect_back()

            if accion == 'asignar_tareas':
                idsprint = request.form.get('idsprint')
                idgrupo = request.form.get('idsprint_grupo') or None
                tareas_ids = request.form.getlist('tareas_ids')
                if idsprint and tareas_ids:
                    sprint = Sprint.query.get(idsprint)
                    if sprint and sprint.estado == 'Cerrado':
                        flash('El sprint esta cerrado. No se pueden asignar tareas.')
                        return _redirect_back()
                    tareas = Tarea.query.filter(Tarea.idtarea.in_(tareas_ids)).all()
                    for tarea in tareas:
                        tarea.idsprint = idsprint
                        tarea.idsprint_grupo = idgrupo
                    db.session.commit()
                    flash('Tareas asignadas al sprint.')
                else:
                    flash('Selecciona un sprint y al menos una tarea.')
                return _redirect_back()

            if accion == 'actualizar_backlog':
                tarea_id = request.form.get('idtarea')
                tarea = Tarea.query.get(tarea_id)
                if tarea:
                    tarea.prioridad_scrum = request.form.get('prioridad_scrum')
                    tarea.story_points = int(request.form.get('story_points') or 0)
                    tarea.backlog_rank = int(request.form.get('backlog_rank') or 0)
                    tarea.idsprint = request.form.get('set_idsprint') or None
                    db.session.commit()
                    flash('Backlog actualizado.')
                return _redirect_back()

            if accion == 'actualizar_sprint_plan':
                idsprint = request.form.get('idsprint')
                sprint = Sprint.query.get(idsprint)
                if sprint:
                    sprint.goal = request.form.get('goal')
                    sprint.definicion_done = request.form.get('definicion_done')
                    cap = request.form.get('capacidad')
                    sprint.capacidad = int(cap) if str(cap).isdigit() else sprint.capacidad
                    sprint.estado = request.form.get('estado') or sprint.estado
                    db.session.commit()
                    flash('Sprint planning actualizado.')
                return _redirect_back()

            if accion == 'asignar_roles':
                idsprint = request.form.get('idsprint')
                rol = request.form.get('rol')
                usuarios_ids = request.form.getlist('usuarios_ids')
                if idsprint and rol and usuarios_ids:
                    SprintRol.query.filter_by(idsprint=idsprint, rol=rol).delete()
                    for uid in usuarios_ids:
                        db.session.add(SprintRol(idsprint=idsprint, idusuario=uid, rol=rol))
                    db.session.commit()
                    flash('Roles Scrum actualizados.')
                return _redirect_back()

            if accion == 'crear_retro':
                idsprint = request.form.get('idsprint')
                notas = request.form.get('notas_retro')
                if idsprint and notas:
                    db.session.add(SprintRetro(idsprint=idsprint, notas=notas))
                    db.session.commit()
                    flash('Retrospectiva registrada.')
                return _redirect_back()

        proyectos = listar_proyectos()
        tareas = listar_tareas()
        sprints = listar_sprints()
        grupos = listar_grupos()
        estados = listar_estados()
        usuarios = listar_usuarios()
        prioridades = listar_prioridades()
        tipos_tarea = listar_tipos_tarea()

        today = datetime.now().date()
        for sprint in sprints:
            tareas_sprint = sprint.tareas or []
            restante = _remaining_points(tareas_sprint)
            existing = SprintBurndown.query.filter_by(idsprint=sprint.idsprint, fecha=today).first()
            if existing:
                existing.restante = restante
            else:
                db.session.add(SprintBurndown(idsprint=sprint.idsprint, fecha=today, restante=restante))
        db.session.commit()

        selected_project_id = request.args.get('idproyecto', type=int)
        selected_sprint_id = request.args.get('idsprint', type=int)

        sprint_items = [_build_sprint_item(sprint) for sprint in sprints]
        sprint_lookup = {item['idsprint']: item for item in sprint_items}

        filtered_sprints = [
            item for item in sprint_items
            if (not selected_project_id or item['proyecto_id'] == selected_project_id)
        ]
        if not selected_sprint_id and filtered_sprints:
            active = next((item for item in filtered_sprints if item['estado'] == 'Activo'), None)
            selected_sprint_id = active['idsprint'] if active else filtered_sprints[0]['idsprint']

        sprint_actual = sprint_lookup.get(selected_sprint_id) if selected_sprint_id else None

        task_cards = [_build_task_card(tarea) for tarea in tareas]
        backlog_items = [
            card for card in task_cards
            if not card['sprint_id'] and (not selected_project_id or card['proyecto'] == next((p.nombre_proyecto for p in proyectos if p.idproyecto == selected_project_id), ''))
        ]
        backlog_items.sort(key=lambda item: (item['backlog_rank'] or 999999, item['titulo']))

        board_source = sprint_actual['tasks'] if sprint_actual else []
        board_columns = []
        for estado in estados:
            estado_tasks = [task for task in board_source if task['estado_nombre'] == estado.nombre_estado]
            board_columns.append({
                'idestado': estado.idestado,
                'nombre': estado.nombre_estado,
                'color': estado.color or '#94a3b8',
                'tasks': estado_tasks,
                'total': len(estado_tasks),
            })

        total_comments = Comentario.query.count()
        filtered_tasks_count = len(board_source) if sprint_actual else 0
        filtered_comments = sum(task['comentarios_total'] for task in board_source)
        filtered_points = sum(task['story_points'] for task in board_source)
        filtered_done = sum(task['story_points'] for task in board_source if _is_closed_name(task['estado_nombre']))

        estado_counter = Counter(task['estado_nombre'] for task in board_source)
        scrum_report_rows = []
        for item in filtered_sprints:
            scrum_report_rows.append({
                'idsprint': item['idsprint'],
                'nombre': item['nombre'],
                'proyecto': item['proyecto'],
                'estado': item['estado'],
                'capacidad': item['capacidad'] or 0,
                'progreso': item['progreso'],
                'carga': item['carga'],
                'puntos_totales': item['puntos_totales'],
                'puntos_completados': item['puntos_completados'],
                'puntos_restantes': item['puntos_restantes'],
                'comentarios_total': item['comentarios_total'],
                'total_tareas': item['total'],
                'adjuntos_total': item['adjuntos_total'],
                'fecha_inicio': item['fecha_inicio'],
                'fecha_fin': item['fecha_fin'],
                'gantt_url': url_for('reports.project_report', proyecto_id=item['proyecto_id']),
            })

        tareas_por_proyecto = defaultdict(int)
        for tarea in tareas:
            if tarea.proyecto:
                tareas_por_proyecto[tarea.proyecto.nombre_proyecto] += 1

        selected_project_name = next(
            (proyecto.nombre_proyecto for proyecto in proyectos if proyecto.idproyecto == selected_project_id),
            None
        )

        sprint_json = [
            {
                'idsprint': item['idsprint'],
                'burndown': [
                    {'fecha': punto.fecha.isoformat(), 'restante': punto.restante}
                    for punto in item['burndown']
                ]
            }
            for item in sprint_items
        ]

        return render_template(
            'seguimiento/seguimiento_view.html',
            proyectos=proyectos,
            sprints=filtered_sprints,
            sprint_actual=sprint_actual,
            backlog=backlog_items,
            board_columns=board_columns,
            grupos=grupos,
            estados=estados,
            usuarios=usuarios,
            prioridades=prioridades,
            tipos_tarea=tipos_tarea,
            sprint_json=sprint_json,
            scrum_report_rows=scrum_report_rows,
            selected_project_id=selected_project_id,
            selected_project_name=selected_project_name,
            selected_sprint_id=selected_sprint_id,
            team_desarrollo_value=TEAM_DESARROLLO_VALUE,
            total_sprints=len(filtered_sprints),
            total_tareas=len(tareas),
            total_comentarios=total_comments,
            total_proyectos=len(proyectos),
            filtered_tasks_count=filtered_tasks_count,
            filtered_comments=filtered_comments,
            filtered_points=filtered_points,
            filtered_done=filtered_done,
            estado_counter=estado_counter,
            tareas_por_proyecto=tareas_por_proyecto,
        )
    except Exception as exc:
        db.session.rollback()
        return (
            '<h2>Error en Seguimiento</h2>'
            '<p>Ocurrio un problema al cargar el modulo.</p>'
            f'<pre>{escape(str(exc))}</pre>'
        )
