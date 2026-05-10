import html
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

from app.models import CorreosDestino, Usuario


def get_active_recipient_emails():
    return [d.correo for d in CorreosDestino.query.filter_by(activo=True).all()]


def _clean_email(value):
    if not value:
        return None
    email = value.strip().lower()
    return email or None


def _dedupe_emails(emails):
    unique = []
    seen = set()
    for email in emails:
        normalized = _clean_email(email)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def get_task_involved_recipient_emails(tarea, include_commenters=False):
    recipients = []

    if tarea.equipo_desarrollo:
        recipients.extend(
            u.correo for u in Usuario.query.filter_by(activo=True).all() if u.correo
        )
    else:
        if tarea.usuario_asignado and tarea.usuario_asignado.correo:
            recipients.append(tarea.usuario_asignado.correo)

    if tarea.creador and tarea.creador.correo:
        recipients.append(tarea.creador.correo)

    if tarea.proyecto and tarea.proyecto.usuario and tarea.proyecto.usuario.correo:
        recipients.append(tarea.proyecto.usuario.correo)

    if include_commenters:
        for comentario in tarea.comentarios:
            if comentario.usuario and comentario.usuario.correo:
                recipients.append(comentario.usuario.correo)

    return _dedupe_emails(recipients)


def send_password_change_code_email(usuario, codigo):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    subject = "Codigo de confirmacion para cambio de contrasena"
    nombre = (usuario.nombre or 'Usuario').strip()
    correo = usuario.correo

    text_body = (
        f"Hola {nombre},\n\n"
        "Recibimos una solicitud para cambiar tu contrasena.\n"
        f"Tu codigo de confirmacion es: {codigo}\n\n"
        "Si no solicitaste este cambio, ignora este mensaje."
    )

    mensaje_html = html.escape(mensaje).replace("\n", "<br>")

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:560px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 24px; color:#ffffff;">
                <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                <div style="font-size:20px; font-weight:600; margin-top:6px;">Codigo de confirmacion</div>
                <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de gestion</div>
              </td>
            </tr>
            <tr>
              <td style="padding:22px 24px 8px 24px; font-size:15px; line-height:1.6;">
                Hola {html.escape(nombre)}, te enviamos el codigo para confirmar el cambio de contrasena.
              </td>
            </tr>
            <tr>
              <td style="padding:0 24px 20px 24px;">
                <div style="background-color:#f3edf9; border-radius:12px; padding:14px 18px; font-size:22px; font-weight:700; letter-spacing:3px; text-align:center; color:#3b1588;">
                  {codigo}
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 24px 24px 24px; font-size:13px; color:#5b4b66;">
                Si no solicitaste este cambio, ignora este mensaje.
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = correo
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None


def send_new_task_email(tarea, recipients):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    subject = f"Nueva tarea: {tarea.titulo}"
    proyecto = tarea.proyecto.nombre_proyecto if tarea.proyecto else 'Sin proyecto'
    asignado = tarea.nombre_responsable if hasattr(tarea, 'nombre_responsable') else (
        tarea.usuario_asignado.nombre if tarea.usuario_asignado else 'Sin asignar'
    )
    fecha_fin = tarea.fecha_limite.strftime('%Y-%m-%d') if tarea.fecha_limite else 'Sin fecha'
    descripcion = tarea.descripcion.strip() if tarea.descripcion else 'Sin descripcion'
    descripcion_html = html.escape(descripcion).replace('\n', '<br>')

    text_body = (
        "Se creo una nueva tarea en el sistema.\n\n"
        f"Proyecto: {proyecto}\n"
        f"Titulo: {tarea.titulo}\n"
        f"Descripcion: {descripcion}\n"
        f"Asignado: {asignado}\n"
        f"Fecha limite: {fecha_fin}\n\n"
        "Ingresa al sistema para ver mas detalles."
    )

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td style="width:52px;">
                      <div style="width:42px; height:42px; border-radius:12px; background-color:#6a33a5; display:block;">
                        <svg width="42" height="42" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="display:block; padding:9px;">
                          <path fill="#ffffff" d="M12 2a4 4 0 0 0-3.86 2.98A3.5 3.5 0 0 0 4.5 8.5a3.5 3.5 0 0 0 .98 2.41A4 4 0 0 0 12 18a4 4 0 0 0 6.52-3.09A3.5 3.5 0 0 0 19.5 8.5a3.5 3.5 0 0 0-3.64-3.52A4 4 0 0 0 12 2zm-1 5h2v3h3v2h-3v3h-2v-3H8v-2h3z"/>
                        </svg>
                      </div>
                    </td>
                    <td>
                      <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                      <div style="font-size:22px; font-weight:600; color:#ffffff; margin-top:6px;">Informe de nueva tarea</div>
                      <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de gestion</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 10px 28px;">
                <div style="font-size:15px; line-height:1.6; color:#3a2b45;">
                  Se creo una nueva tarea en el sistema. A continuacion se muestra el resumen:
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; border:1px solid #efe6f7; border-radius:10px; overflow:hidden;">
                  <tr>
                    <td style="background-color:#fbf8fe; padding:14px 16px; border-bottom:1px solid #efe6f7; font-weight:600; color:#4b2d66;">Detalle de la tarea</td>
                  </tr>
                  <tr>
                    <td style="padding:14px 16px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;">
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Proyecto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{proyecto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Titulo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{tarea.titulo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74; vertical-align:top;">Descripcion</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:500; line-height:1.5;">{descripcion_html}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Asignado</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{asignado}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Fecha limite</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{fecha_fin}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 28px 28px;">
                <div style="font-size:14px; line-height:1.6; color:#3a2b45;">
                  Ingresa al sistema para ver mas detalles y gestionar la tarea.
                </div>
              </td>
            </tr>
            <tr>
              <td style="background-color:#f7f2fb; padding:16px 28px; border-top:1px solid #efe6f7;">
                <div style="font-size:12px; color:#7a6a86;">Este es un mensaje automatico. No responder.</div>
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None


def send_new_comment_email(tarea, comentario, autor, fecha, comentario_anterior, recipients):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    subject = f"Nuevo comentario en tarea: {tarea.titulo}"
    proyecto = tarea.proyecto.nombre_proyecto if tarea.proyecto else 'Sin proyecto'
    autor_nombre = autor.nombre if autor else 'Usuario'
    fecha_txt = fecha.strftime('%Y-%m-%d %H:%M') if fecha else 'Sin fecha'
    comentario_texto = comentario.strip() if comentario else ''
    comentario_html = html.escape(comentario_texto).replace('\n', '<br>')

    prev_text = None
    prev_fecha = None
    prev_autor = None
    if comentario_anterior:
        prev_text = comentario_anterior.comentario.strip() if comentario_anterior.comentario else ''
        prev_fecha = comentario_anterior.fecha.strftime('%Y-%m-%d %H:%M') if comentario_anterior.fecha else ''
        prev_autor = comentario_anterior.usuario.nombre if comentario_anterior.usuario else 'Usuario'

    prev_text_html = html.escape(prev_text or 'Sin comentario anterior.').replace('\n', '<br>')

    text_body = (
        "Se registro un nuevo comentario en el sistema.\n\n"
        f"Proyecto: {proyecto}\n"
        f"Tarea: {tarea.titulo}\n"
        f"Autor: {autor_nombre}\n"
        f"Fecha: {fecha_txt}\n"
        f"Comentario: {comentario_texto}\n\n"
        "Comentario anterior relevante:\n"
        f"{prev_text or 'Sin comentario anterior.'}\n"
    )

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td style="width:52px;">
                      <div style="width:42px; height:42px; border-radius:12px; background-color:#6a33a5; display:block;">
                        <svg width="42" height="42" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="display:block; padding:9px;">
                          <path fill="#ffffff" d="M12 2a4 4 0 0 0-3.86 2.98A3.5 3.5 0 0 0 4.5 8.5a3.5 3.5 0 0 0 .98 2.41A4 4 0 0 0 12 18a4 4 0 0 0 6.52-3.09A3.5 3.5 0 0 0 19.5 8.5a3.5 3.5 0 0 0-3.64-3.52A4 4 0 0 0 12 2zm-1 5h2v3h3v2h-3v3h-2v-3H8v-2h3z"/>
                        </svg>
                      </div>
                    </td>
                    <td>
                      <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                      <div style="font-size:22px; font-weight:600; color:#ffffff; margin-top:6px;">Nuevo comentario registrado</div>
                      <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de gestion</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 10px 28px;">
                <div style="font-size:15px; line-height:1.6; color:#3a2b45;">
                  Se registro un nuevo comentario en el sistema. A continuacion se muestra el resumen:
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; border:1px solid #efe6f7; border-radius:10px; overflow:hidden;">
                  <tr>
                    <td style="background-color:#fbf8fe; padding:14px 16px; border-bottom:1px solid #efe6f7; font-weight:600; color:#4b2d66;">Detalle del comentario</td>
                  </tr>
                  <tr>
                    <td style="padding:14px 16px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;">
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Proyecto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{proyecto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Tarea</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{tarea.titulo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Autor</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{autor_nombre}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Fecha</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{fecha_txt}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74; vertical-align:top;">Comentario</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:500; line-height:1.5;">{comentario_html}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="background-color:#f7f2fb; padding:16px 28px; border-top:1px solid #efe6f7;">
                <div style="font-size:12px; color:#7a6a86; font-weight:600;">Comentario anterior relevante</div>
                <div style="font-size:12px; color:#7a6a86; margin-top:6px; line-height:1.5;">{prev_text_html}</div>
                <div style="font-size:11px; color:#9b8aa8; margin-top:6px;">
                  {prev_autor or ''} {f'- {prev_fecha}' if prev_fecha else ''}
                </div>
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None


def send_new_agenda_email(agenda, recipients):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    subject = f"Nuevo evento en agenda: {agenda.titulo}"
    proyecto = agenda.proyecto.nombre_proyecto if agenda.proyecto else 'Sin proyecto'
    tipo = agenda.tipo or 'Evento'
    estado = agenda.estado or 'Pendiente'
    inicio = agenda.fecha_inicio.strftime('%Y-%m-%d %H:%M') if agenda.fecha_inicio else 'Sin fecha'
    fin = agenda.fecha_fin.strftime('%Y-%m-%d %H:%M') if agenda.fecha_fin else 'Sin fecha'
    ubicacion = agenda.ubicacion or 'Sin ubicacion'
    cliente = agenda.cliente or 'Sin cliente'
    contacto = agenda.contacto or 'Sin contacto'
    notas = agenda.notas.strip() if agenda.notas else 'Sin notas'
    notas_html = html.escape(notas).replace('\n', '<br>')

    text_body = (
        "Se registro un nuevo evento en la agenda.\n\n"
        f"Proyecto: {proyecto}\n"
        f"Titulo: {agenda.titulo}\n"
        f"Tipo: {tipo}\n"
        f"Estado: {estado}\n"
        f"Inicio: {inicio}\n"
        f"Fin: {fin}\n"
        f"Ubicacion: {ubicacion}\n"
        f"Cliente: {cliente}\n"
        f"Contacto: {contacto}\n"
        f"Notas: {notas}\n\n"
        "Ingresa al sistema para ver mas detalles."
    )

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td style="width:52px;">
                      <div style="width:42px; height:42px; border-radius:12px; background-color:#6a33a5; display:block;">
                        <svg width="42" height="42" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="display:block; padding:9px;">
                          <path fill="#ffffff" d="M7 2h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 4h10V4H7v2zm2 4h6v2H9v-2zm0 4h4v2H9v-2z"/>
                        </svg>
                      </div>
                    </td>
                    <td>
                      <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                      <div style="font-size:22px; font-weight:600; color:#ffffff; margin-top:6px;">Nuevo evento de agenda</div>
                      <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de gestion</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 10px 28px;">
                <div style="font-size:15px; line-height:1.6; color:#3a2b45;">
                  Se registro un nuevo evento en la agenda. A continuacion se muestra el resumen:
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; border:1px solid #efe6f7; border-radius:10px; overflow:hidden;">
                  <tr>
                    <td style="background-color:#fbf8fe; padding:14px 16px; border-bottom:1px solid #efe6f7; font-weight:600; color:#4b2d66;">Detalle del evento</td>
                  </tr>
                  <tr>
                    <td style="padding:14px 16px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;">
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Proyecto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{proyecto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Titulo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{agenda.titulo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Tipo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{tipo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Estado</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{estado}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Inicio</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{inicio}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Fin</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{fin}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Ubicacion</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{ubicacion}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Cliente</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{cliente}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Contacto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{contacto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74; vertical-align:top;">Notas</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:500; line-height:1.5;">{notas_html}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 28px 28px;">
                <div style="font-size:14px; line-height:1.6; color:#3a2b45;">
                  Ingresa al sistema para ver mas detalles y gestionar la agenda.
                </div>
              </td>
            </tr>
            <tr>
              <td style="background-color:#f7f2fb; padding:16px 28px; border-top:1px solid #efe6f7;">
                <div style="font-size:12px; color:#7a6a86;">Este es un mensaje automatico. No responder.</div>
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None


def send_agenda_reminder_email(agenda, recipients, hours_before=1):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    subject = f"Recordatorio: {agenda.titulo}"
    proyecto = agenda.proyecto.nombre_proyecto if agenda.proyecto else 'Sin proyecto'
    tipo = agenda.tipo or 'Evento'
    estado = agenda.estado or 'Pendiente'
    inicio = agenda.fecha_inicio.strftime('%Y-%m-%d %H:%M') if agenda.fecha_inicio else 'Sin fecha'
    fin = agenda.fecha_fin.strftime('%Y-%m-%d %H:%M') if agenda.fecha_fin else 'Sin fecha'
    ubicacion = agenda.ubicacion or 'Sin ubicacion'
    cliente = agenda.cliente or 'Sin cliente'
    contacto = agenda.contacto or 'Sin contacto'
    notas = agenda.notas.strip() if agenda.notas else 'Sin notas'
    notas_html = html.escape(notas).replace('\n', '<br>')

    text_body = (
        f"Recordatorio: el evento inicia en aproximadamente {hours_before} hora(s).\n\n"
        f"Proyecto: {proyecto}\n"
        f"Titulo: {agenda.titulo}\n"
        f"Tipo: {tipo}\n"
        f"Estado: {estado}\n"
        f"Inicio: {inicio}\n"
        f"Fin: {fin}\n"
        f"Ubicacion: {ubicacion}\n"
        f"Cliente: {cliente}\n"
        f"Contacto: {contacto}\n"
        f"Notas: {notas}\n\n"
        "Ingresa al sistema para ver mas detalles."
    )

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td style="width:52px;">
                      <div style="width:42px; height:42px; border-radius:12px; background-color:#6a33a5; display:block;">
                        <svg width="42" height="42" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="display:block; padding:9px;">
                          <path fill="#ffffff" d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0-6a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 5h-2v6h5v-2h-3z"/>
                        </svg>
                      </div>
                    </td>
                    <td>
                      <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                      <div style="font-size:22px; font-weight:600; color:#ffffff; margin-top:6px;">Recordatorio de agenda</div>
                      <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de gestion</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 10px 28px;">
                <div style="font-size:15px; line-height:1.6; color:#3a2b45;">
                  El evento inicia en aproximadamente {hours_before} hora(s). Resumen:
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px 28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; border:1px solid #efe6f7; border-radius:10px; overflow:hidden;">
                  <tr>
                    <td style="background-color:#fbf8fe; padding:14px 16px; border-bottom:1px solid #efe6f7; font-weight:600; color:#4b2d66;">Detalle del evento</td>
                  </tr>
                  <tr>
                    <td style="padding:14px 16px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;">
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Proyecto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{proyecto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Titulo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{agenda.titulo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Tipo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{tipo}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Estado</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{estado}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Inicio</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{inicio}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Fin</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{fin}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Ubicacion</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{ubicacion}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Cliente</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{cliente}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Contacto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{contacto}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74; vertical-align:top;">Notas</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:500; line-height:1.5;">{notas_html}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 28px 28px;">
                <div style="font-size:14px; line-height:1.6; color:#3a2b45;">
                  Ingresa al sistema para ver mas detalles.
                </div>
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None


def send_notification_resend(notif, recipients):
    config = current_app.config
    smtp_user = config.get('SMTP_USER')
    smtp_password = config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_password:
        return False, 'SMTP credentials missing'

    host = config.get('SMTP_HOST', 'smtp.zoho.com')
    port = int(config.get('SMTP_PORT', 587))
    sender_name = config.get('SMTP_SENDER_NAME', 'Violeta Workspace')
    use_tls = bool(config.get('SMTP_USE_TLS', True))

    tipo = notif.tipo or 'General'
    fecha_txt = notif.fecha_envio.strftime('%Y-%m-%d %H:%M') if notif.fecha_envio else 'Sin fecha'
    mensaje = notif.mensaje or 'Sin mensaje'
    proyecto = None
    if notif.tarea and notif.tarea.proyecto:
        proyecto = notif.tarea.proyecto.nombre_proyecto
    proyecto = proyecto or 'Sin proyecto'

    subject = f"Reenvio de notificacion: {tipo}"

    text_body = (
        "Reenvio de notificacion desde Violeta Workspace.\n\n"
        f"Tipo: {tipo}\n"
        f"Proyecto: {proyecto}\n"
        f"Fecha original: {fecha_txt}\n"
        f"Mensaje: {mensaje}\n"
    )

    html_body = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f6f3f9;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f6f3f9; padding:24px 12px; font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; color:#2e2136;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background-color:#ffffff; border:1px solid #e6d8f2; border-radius:14px; overflow:hidden;">
            <tr>
              <td style="background-color:#4b1a73; padding:20px 24px; color:#ffffff;">
                <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#e9def5;">Violeta Workspace</div>
                <div style="font-size:20px; font-weight:600; margin-top:6px;">Reenvio de notificacion</div>
                <div style="font-size:12px; color:#dccbf0; margin-top:4px;">Sistema de notificaciones</div>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 24px 6px 24px; font-size:14px; line-height:1.6;">
                Se reenvia una notificacion registrada por el sistema.
              </td>
            </tr>
            <tr>
              <td style="padding:0 24px 20px 24px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; border:1px solid #efe6f7; border-radius:10px; overflow:hidden;">
                  <tr>
                    <td style="background-color:#fbf8fe; padding:12px 14px; border-bottom:1px solid #efe6f7; font-weight:600; color:#4b2d66;">Detalle</td>
                  </tr>
                  <tr>
                    <td style="padding:12px 14px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;">
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Tipo</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{html.escape(tipo)}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Proyecto</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{html.escape(proyecto)}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74;">Fecha</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:600;">{html.escape(fecha_txt)}</td>
                        </tr>
                        <tr>
                          <td style="padding:6px 0; width:140px; color:#6a5a74; vertical-align:top;">Mensaje</td>
                          <td style="padding:6px 0; color:#2e2136; font-weight:500; line-height:1.5;">{mensaje_html}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="background-color:#f7f2fb; padding:14px 24px; border-top:1px solid #efe6f7;">
                <div style="font-size:12px; color:#7a6a86;">Este es un reenvio automatico del sistema. No responder.</div>
              </td>
            </tr>
          </table>
          <div style="font-size:11px; color:#8b7b96; padding-top:14px;">Violeta Workspace</div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True, None
