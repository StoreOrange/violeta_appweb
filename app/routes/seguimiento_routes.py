from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from app import db
from app.models import Tarea, Sprint, Estado, SprintRol, SprintRetro, SprintBurndown
from app.crud.proyecto_crud import listar_proyectos
from app.crud.tarea_crud import listar_tareas
from app.crud.sprint_crud import crear_sprint, listar_sprints
from app.crud.sprint_grupo_crud import crear_grupo, listar_grupos
from app.crud.usuario_crud import listar_usuarios


seguimiento_bp = Blueprint('seguimiento', __name__, url_prefix='/seguimiento')


def _require_login():
    if not session.get('user_id'):
        flash('Debes iniciar sesion para continuar.')
        return redirect(url_for('usuario.login'))
    return None


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


def _is_done(tarea):
    if not tarea or not tarea.estado or not tarea.estado.nombre_estado:
        return False
    return 'completad' in tarea.estado.nombre_estado.strip().lower()


def _remaining_points(tareas):
    total = 0
    for t in tareas:
        points = t.story_points or 0
        if not _is_done(t):
            total += points
    return total


@seguimiento_bp.route('/', methods=['GET', 'POST'])
def vista_seguimiento():
    guard = _require_login()
    if guard:
        return guard

    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'crear_sprint':
            fecha_inicio = _parse_date(request.form.get('fecha_inicio'))
            fecha_fin = _parse_date(request.form.get('fecha_fin'))
            capacidad = request.form.get('capacidad')
            capacidad_val = int(capacidad) if str(capacidad).isdigit() else None
            idproyecto = request.form.get('idproyecto')
            nombre = request.form.get('nombre')
            if not nombre:
                count = Sprint.query.filter_by(idproyecto=idproyecto).count()
                nombre = f"Sprint {count + 1}"
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
            return redirect(url_for('seguimiento.vista_seguimiento'))

        if accion == 'crear_grupo':
            idsprint = request.form.get('idsprint')
            nombre = request.form.get('nombre_grupo')
            descripcion = request.form.get('descripcion_grupo')
            orden = request.form.get('orden_grupo')
            orden_val = int(orden) if str(orden).isdigit() else None
            if not idsprint or not nombre:
                flash('Completa el sprint y el nombre del grupo.')
                return redirect(url_for('seguimiento.vista_seguimiento'))
            sprint = Sprint.query.get(idsprint)
            if sprint and sprint.estado == 'Cerrado':
                flash('El sprint esta cerrado. No se pueden crear grupos.')
                return redirect(url_for('seguimiento.vista_seguimiento'))
            crear_grupo(nombre, descripcion, orden_val, idsprint)
            flash('Grupo creado correctamente.')
            return redirect(url_for('seguimiento.vista_seguimiento'))

        if accion == 'asignar_tareas':
            idsprint = request.form.get('idsprint')
            idgrupo = request.form.get('idsprint_grupo') or None
            tareas_ids = request.form.getlist('tareas_ids')
            if idsprint and tareas_ids:
                sprint = Sprint.query.get(idsprint)
                if sprint and sprint.estado == 'Cerrado':
                    flash('El sprint esta cerrado. No se pueden asignar tareas.')
                    return redirect(url_for('seguimiento.vista_seguimiento'))
                tareas = Tarea.query.filter(Tarea.idtarea.in_(tareas_ids)).all()
                for tarea in tareas:
                    tarea.idsprint = idsprint
                    tarea.idsprint_grupo = idgrupo
                db.session.commit()
                flash('Tareas asignadas al sprint.')
            else:
                flash('Selecciona un sprint y al menos una tarea.')
            return redirect(url_for('seguimiento.vista_seguimiento'))

        if accion == 'actualizar_backlog':
            tarea_id = request.form.get('idtarea')
            tarea = Tarea.query.get(tarea_id)
            if tarea:
                tarea.prioridad_scrum = request.form.get('prioridad_scrum')
                tarea.story_points = int(request.form.get('story_points') or 0)
                tarea.backlog_rank = int(request.form.get('backlog_rank') or 0)
                db.session.commit()
                flash('Backlog actualizado.')
            return redirect(url_for('seguimiento.vista_seguimiento'))

        if accion == 'actualizar_sprint_plan':
            idsprint = request.form.get('idsprint')
            sprint = Sprint.query.get(idsprint)
            if sprint:
                sprint.goal = request.form.get('goal')
                sprint.definicion_done = request.form.get('definicion_done')
                cap = request.form.get('capacidad')
                sprint.capacidad = int(cap) if str(cap).isdigit() else sprint.capacidad
                db.session.commit()
                flash('Sprint planning actualizado.')
            return redirect(url_for('seguimiento.vista_seguimiento'))

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
            return redirect(url_for('seguimiento.vista_seguimiento'))

        if accion == 'crear_retro':
            idsprint = request.form.get('idsprint')
            notas = request.form.get('notas_retro')
            if idsprint and notas:
                db.session.add(SprintRetro(idsprint=idsprint, notas=notas))
                db.session.commit()
                flash('Retrospectiva registrada.')
            return redirect(url_for('seguimiento.vista_seguimiento'))

    proyectos = listar_proyectos()
    tareas = listar_tareas()
    sprints = listar_sprints()
    grupos = listar_grupos()
    estados = Estado.query.order_by(Estado.orden.asc().nulls_last(), Estado.idestado.asc()).all()
    usuarios = listar_usuarios()

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

    sprint_items = []
    for sprint in sprints:
        tareas_sprint = sprint.tareas or []
        total = len(tareas_sprint)
        completadas = sum(1 for t in tareas_sprint if _is_done(t))
        progreso = int(round((completadas / total) * 100)) if total else 0
        puntos_totales = sum((t.story_points or 0) for t in tareas_sprint)
        puntos_restantes = _remaining_points(tareas_sprint)
        roles = SprintRol.query.filter_by(idsprint=sprint.idsprint).all()
        retros = SprintRetro.query.filter_by(idsprint=sprint.idsprint).order_by(SprintRetro.creado_en.desc()).all()
        burndown = SprintBurndown.query.filter_by(idsprint=sprint.idsprint).order_by(SprintBurndown.fecha.asc()).all()
        sprint_items.append({
            "idsprint": sprint.idsprint,
            "nombre": sprint.nombre,
            "objetivo": sprint.objetivo,
            "fecha_inicio": sprint.fecha_inicio,
            "fecha_fin": sprint.fecha_fin,
            "estado": sprint.estado,
            "capacidad": sprint.capacidad,
            "proyecto": sprint.proyecto.nombre_proyecto if sprint.proyecto else "",
            "total": total,
            "completadas": completadas,
            "progreso": progreso,
            "grupos": sprint.grupos or [],
            "goal": sprint.goal,
            "definicion_done": sprint.definicion_done,
            "puntos_totales": puntos_totales,
            "puntos_restantes": puntos_restantes,
            "roles": roles,
            "retros": retros,
            "burndown": burndown
        })

    backlog = tareas

    tareas_json = [
        {
            "idtarea": t.idtarea,
            "titulo": t.titulo,
            "idsprint": t.idsprint,
            "estado": t.estado.nombre_estado if t.estado else "Sin estado",
            "estado_color": t.estado.color if t.estado and t.estado.color else "#e2e8f0",
            "proyecto": t.proyecto.nombre_proyecto if t.proyecto else ""
        }
        for t in tareas
    ]

    sprint_json = [
        {
            "idsprint": s["idsprint"],
            "burndown": [
                {"fecha": b.fecha.isoformat(), "restante": b.restante}
                for b in s["burndown"]
            ]
        }
        for s in sprint_items
    ]

    return render_template(
        'seguimiento/seguimiento_view.html',
        proyectos=proyectos,
        tareas=tareas,
        sprints=sprint_items,
        backlog=backlog,
        grupos=grupos,
        estados=estados,
        tareas_json=tareas_json,
        sprint_json=sprint_json,
        usuarios=usuarios
    )
