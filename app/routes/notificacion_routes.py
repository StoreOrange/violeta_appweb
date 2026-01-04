from datetime import datetime, timedelta, time

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash

from app import db
from app.models import Notificacion
from app.crud.notificacion_crud import *
from app.crud.tarea_crud import listar_tareas_pendientes
from app.utils.email import get_active_recipient_emails, send_notification_resend

notificacion_bp = Blueprint('notificacion', __name__, url_prefix='/notificaciones')


@notificacion_bp.route('/nuevo', methods=['POST'])
def nueva_notificacion():
    crear_notificacion(**request.form.to_dict())
    return redirect(url_for('notificacion.vista_notificaciones'))

@notificacion_bp.route('/editar/<int:idnotificacion>', methods=['POST'])
def editar_notificacion(idnotificacion):
    datos = request.form.to_dict()
    actualizar_notificacion(idnotificacion, datos)
    return redirect(url_for('notificacion.vista_notificaciones'))

@notificacion_bp.route('/eliminar/<int:idnotificacion>', methods=['POST'])
def eliminar_notificacion_view(idnotificacion):
    eliminar_notificacion(idnotificacion)
    return redirect(url_for('notificacion.vista_notificaciones'))

@notificacion_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([n.as_dict() for n in listar_notificaciones()])

@notificacion_bp.route('/reenviar/<int:idnotificacion>', methods=['POST'])
def reenviar_notificacion(idnotificacion):
    notif = obtener_notificacion_por_id(idnotificacion)
    if not notif:
        flash('Notificacion no encontrada.')
        return redirect(request.referrer or url_for('notificacion.vista_notificaciones'))

    destinatarios = []
    if notif.destinatarios:
        destinatarios = [d.strip() for d in notif.destinatarios.split(',') if d.strip()]
    if not destinatarios:
        destinatarios = get_active_recipient_emails()

    if not destinatarios:
        flash('No hay destinatarios activos para reenviar.')
        return redirect(request.referrer or url_for('notificacion.vista_notificaciones'))

    ok, error = send_notification_resend(notif, destinatarios)
    if not ok:
        flash(f'No se pudo reenviar: {error}')
    else:
        flash('Notificacion reenviada correctamente.')
    return redirect(request.referrer or url_for('notificacion.vista_notificaciones'))



@notificacion_bp.route('/')
def vista_notificaciones():
    tipo_sel = (request.args.get('tipo') or '').strip()
    fecha_inicio_raw = request.args.get('fecha_inicio')
    fecha_fin_raw = request.args.get('fecha_fin')

    now = datetime.now()
    if not fecha_inicio_raw and not fecha_fin_raw:
        fecha_inicio = (now - timedelta(days=3)).date()
        fecha_fin = now.date()
    else:
        fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date() if fecha_inicio_raw else None
        fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date() if fecha_fin_raw else None

    query = Notificacion.query
    if fecha_inicio:
        query = query.filter(Notificacion.fecha_envio >= datetime.combine(fecha_inicio, time.min))
    if fecha_fin:
        query = query.filter(Notificacion.fecha_envio <= datetime.combine(fecha_fin, time.max))
    if tipo_sel:
        query = query.filter(Notificacion.tipo == tipo_sel)

    notificaciones = query.order_by(Notificacion.fecha_envio.desc()).all()
    tipos = [row[0] for row in db.session.query(Notificacion.tipo).distinct().order_by(Notificacion.tipo).all() if row[0]]
    tareas_pendientes = listar_tareas_pendientes()  # Debes crear esto en el crud de tareas
    return render_template(
        'notificaciones/notificaciones_view.html',
        notificaciones=notificaciones,
        tareas_pendientes=tareas_pendientes,
        tipos=tipos,
        tipo_sel=tipo_sel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
