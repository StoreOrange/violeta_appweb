from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, send_file
from datetime import datetime, timedelta
from io import BytesIO

from app import db
from app.crud.agenda_crud import (
    crear_agenda,
    listar_agenda,
    actualizar_agenda,
    eliminar_agenda,
)
from app.crud.notificacion_crud import crear_notificacion
from app.crud.proyecto_crud import listar_proyectos
from app.utils.email import (
    get_active_recipient_emails,
    send_new_agenda_email,
    send_agenda_reminder_email
)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None


def _agenda_status_color(estado):
    if estado == 'Pendiente':
        return '#f59e0b'
    if estado == 'Confirmado':
        return '#10b981'
    if estado == 'En curso':
        return '#0ea5e9'
    if estado == 'Completado':
        return '#16a34a'
    if estado == 'Cancelado':
        return '#f43f5e'
    if estado == 'Pasada':
        return '#64748b'
    return '#94a3b8'


@agenda_bp.route('/', methods=['GET', 'POST'])
def vista_agenda():
    proyectos = listar_proyectos()

    if request.method == 'POST':
        form = request.form
        idusuario = session.get('user_id') or session.get('idusuario') or 1
        idproyecto = form.get('idproyecto') or None
        if idproyecto == "":
            idproyecto = None

        fecha_inicio = _parse_datetime(form.get('fecha_inicio')) or datetime.now()
        fecha_fin = _parse_datetime(form.get('fecha_fin'))

        agenda = crear_agenda(
            titulo=form.get('titulo'),
            descripcion=form.get('descripcion'),
            tipo=form.get('tipo') or 'Reunion',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ubicacion=form.get('ubicacion'),
            cliente=form.get('cliente'),
            contacto=form.get('contacto'),
            notas=form.get('notas'),
            estado=form.get('estado') or 'Pendiente',
            idusuario=idusuario,
            idproyecto=idproyecto
        )

        recipients = []
        try:
            recipients = get_active_recipient_emails()
            if recipients:
                ok, error = send_new_agenda_email(agenda, recipients)
                if not ok:
                    current_app.logger.warning('Email not sent: %s', error)
        except Exception as exc:
            current_app.logger.exception('Email send failed: %s', exc)
            recipients = []

        if form.get('enviar_notificacion') == 'on':
            mensaje = f"Nuevo evento en agenda: {agenda.titulo}"
            destinatarios_txt = ', '.join(recipients) if recipients else None
            crear_notificacion(
                idusuario=idusuario,
                idtarea=None,
                mensaje=mensaje,
                fecha_envio=datetime.now(),
                tipo='Agenda',
                destinatarios=destinatarios_txt
            )

        flash('Evento agregado a la agenda.')
        return redirect(url_for('agenda.vista_agenda'))

    agendas = listar_agenda()
    now = datetime.now()
    updated = False

    for agenda in agendas:
        if agenda.estado not in ('Cancelado', 'Completado', 'Pasada'):
            fecha_ref = agenda.fecha_fin or agenda.fecha_inicio
            if fecha_ref and fecha_ref < now:
                agenda.estado = 'Pasada'
                updated = True

        if agenda.fecha_inicio and not agenda.recordatorio_enviado:
            delta = agenda.fecha_inicio - now
            if timedelta(seconds=0) <= delta <= timedelta(hours=1):
                try:
                    recipients = get_active_recipient_emails()
                    if recipients:
                        ok, error = send_agenda_reminder_email(agenda, recipients, hours_before=1)
                        if ok:
                            agenda.recordatorio_enviado = True
                            agenda.recordatorio_enviado_en = now
                            updated = True
                        else:
                            current_app.logger.warning('Reminder email not sent: %s', error)
                except Exception as exc:
                    current_app.logger.exception('Reminder email failed: %s', exc)

    if updated:
        db.session.commit()
    agendas_json = [
        {
            "idagenda": a.idagenda,
            "titulo": a.titulo,
            "descripcion": a.descripcion,
            "tipo": a.tipo,
            "estado": a.estado,
            "fecha_inicio": a.fecha_inicio.strftime('%Y-%m-%dT%H:%M') if a.fecha_inicio else "",
            "fecha_fin": a.fecha_fin.strftime('%Y-%m-%dT%H:%M') if a.fecha_fin else "",
            "ubicacion": a.ubicacion,
            "cliente": a.cliente,
            "contacto": a.contacto,
            "proyecto": a.proyecto.nombre_proyecto if a.proyecto else ""
        }
        for a in agendas
    ]

    return render_template(
        'agenda/agenda_view.html',
        agendas=agendas,
        agendas_json=agendas_json,
        proyectos=proyectos
    )


@agenda_bp.route('/editar/<int:idagenda>', methods=['POST'])
def editar_agenda(idagenda):
    datos = request.form.to_dict()
    fecha_inicio = _parse_datetime(datos.get('fecha_inicio'))
    fecha_fin = _parse_datetime(datos.get('fecha_fin'))
    if fecha_inicio:
        datos['fecha_inicio'] = fecha_inicio
    if fecha_fin:
        datos['fecha_fin'] = fecha_fin
    if 'idproyecto' in datos and datos['idproyecto'] == '':
        datos['idproyecto'] = None
    actualizar_agenda(idagenda, datos)
    flash('Evento actualizado.')
    return redirect(url_for('agenda.vista_agenda'))


@agenda_bp.route('/eliminar/<int:idagenda>', methods=['POST'])
def eliminar_agenda_view(idagenda):
    eliminar_agenda(idagenda)
    flash('Evento eliminado.')
    return redirect(url_for('agenda.vista_agenda'))


@agenda_bp.route('/api', methods=['GET'])
def api_listar():
    agendas = listar_agenda()
    return jsonify([
        {
            "idagenda": a.idagenda,
            "titulo": a.titulo,
            "descripcion": a.descripcion,
            "tipo": a.tipo,
            "estado": a.estado,
            "fecha_inicio": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None,
            "ubicacion": a.ubicacion,
            "cliente": a.cliente,
            "contacto": a.contacto,
            "idusuario": a.idusuario,
            "idproyecto": a.idproyecto
        }
        for a in agendas
    ])


@agenda_bp.route('/report/pdf', methods=['GET'])
def export_agenda_pdf():
    agendas = listar_agenda()
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=32,
        rightMargin=32,
        topMargin=32,
        bottomMargin=28
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]
    body_style.fontSize = 8
    body_style.leading = 10

    elements = [Paragraph("Reporte de agenda", title_style), Spacer(1, 8)]

    headers = ["Titulo", "Tipo", "Estado", "Inicio", "Fin", "Proyecto", "Cliente", "Contacto", "Ubicacion"]
    data = [[Paragraph(h, body_style) for h in headers]]
    for a in agendas:
        data.append([
            Paragraph(a.titulo or "", body_style),
            Paragraph(a.tipo or "", body_style),
            Paragraph(a.estado or "", body_style),
            Paragraph(a.fecha_inicio.strftime("%Y-%m-%d %H:%M") if a.fecha_inicio else "", body_style),
            Paragraph(a.fecha_fin.strftime("%Y-%m-%d %H:%M") if a.fecha_fin else "", body_style),
            Paragraph(a.proyecto.nombre_proyecto if a.proyecto else "", body_style),
            Paragraph(a.cliente or "", body_style),
            Paragraph(a.contacto or "", body_style),
            Paragraph(a.ubicacion or "", body_style),
        ])

    available_width = letter[0] - doc.leftMargin - doc.rightMargin
    col_widths = [
        available_width * 0.19,
        available_width * 0.07,
        available_width * 0.07,
        available_width * 0.11,
        available_width * 0.11,
        available_width * 0.13,
        available_width * 0.10,
        available_width * 0.10,
        available_width * 0.12,
    ]
    table = Table(data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="agenda_report.pdf",
        mimetype="application/pdf"
    )


@agenda_bp.route('/report/text', methods=['GET'])
def export_agenda_text():
    agendas = listar_agenda()
    lines = []
    lines.append("Reporte de agenda")
    lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("-" * 60)
    for a in agendas:
        lines.append(f"Titulo: {a.titulo or ''}")
        lines.append(f"Tipo: {a.tipo or ''}")
        lines.append(f"Estado: {a.estado or ''}")
        lines.append(f"Inicio: {a.fecha_inicio.strftime('%Y-%m-%d %H:%M') if a.fecha_inicio else ''}")
        lines.append(f"Fin: {a.fecha_fin.strftime('%Y-%m-%d %H:%M') if a.fecha_fin else ''}")
        lines.append(f"Proyecto: {a.proyecto.nombre_proyecto if a.proyecto else ''}")
        lines.append(f"Cliente: {a.cliente or ''}")
        lines.append(f"Contacto: {a.contacto or ''}")
        lines.append(f"Ubicacion: {a.ubicacion or ''}")
        lines.append(f"Descripcion: {a.descripcion or ''}")
        lines.append(f"Notas: {a.notas or ''}")
        lines.append("-" * 60)

    content = "\n".join(lines)
    output = BytesIO(content.encode("utf-8"))
    return send_file(
        output,
        as_attachment=True,
        download_name="agenda_report.txt",
        mimetype="text/plain; charset=utf-8"
    )
