# app/crud/notificacion_crud.py
from app import db
from app.models import Notificacion
from app.models import Tarea, Estado

def crear_notificacion(idusuario, idtarea, mensaje, fecha_envio, tipo, leida=False, destinatarios=None):
    notif = Notificacion(
        idusuario=idusuario,
        idtarea=idtarea,
        mensaje=mensaje,
        fecha_envio=fecha_envio,
        tipo=tipo,
        leida=leida,
        destinatarios=destinatarios
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def obtener_notificacion_por_id(idnotificacion):
    return Notificacion.query.get(idnotificacion)

def listar_notificaciones():
    return Notificacion.query.all()

def actualizar_notificacion(idnotificacion, datos):
    notif = Notificacion.query.get(idnotificacion)
    if not notif:
        return None
    for clave, valor in datos.items():
        setattr(notif, clave, valor)
    db.session.commit()
    return notif

def eliminar_notificacion(idnotificacion):
    notif = Notificacion.query.get(idnotificacion)
    if notif:
        db.session.delete(notif)
        db.session.commit()
        return True
    return False


def listar_tareas_pendientes():
    # Suponiendo que el estado "Completada" es id=... (o busca por nombre)
    return Tarea.query.join(Estado).filter(Estado.nombre_estado != 'Completada').all()

