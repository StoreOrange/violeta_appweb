# app/crud/agenda_crud.py
from app import db
from app.models import Agenda


def crear_agenda(
    titulo,
    descripcion,
    tipo,
    fecha_inicio,
    fecha_fin,
    ubicacion,
    cliente,
    contacto,
    notas,
    estado,
    idusuario,
    idproyecto
):
    agenda = Agenda(
        titulo=titulo,
        descripcion=descripcion,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        ubicacion=ubicacion,
        cliente=cliente,
        contacto=contacto,
        notas=notas,
        estado=estado,
        idusuario=idusuario,
        idproyecto=idproyecto
    )
    db.session.add(agenda)
    db.session.commit()
    return agenda


def obtener_agenda_por_id(idagenda):
    return Agenda.query.get(idagenda)


def listar_agenda(idusuario=None):
    if idusuario is not None:
        return Agenda.query.filter_by(idusuario=idusuario).order_by(Agenda.fecha_inicio.desc()).all()
    return Agenda.query.order_by(Agenda.fecha_inicio.desc()).all()


def actualizar_agenda(idagenda, datos):
    agenda = Agenda.query.get(idagenda)
    if not agenda:
        return None
    for clave, valor in datos.items():
        setattr(agenda, clave, valor)
    db.session.commit()
    return agenda


def eliminar_agenda(idagenda):
    agenda = Agenda.query.get(idagenda)
    if agenda:
        db.session.delete(agenda)
        db.session.commit()
        return True
    return False
