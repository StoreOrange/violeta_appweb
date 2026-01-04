# app/crud/sprint_crud.py
from app import db
from app.models import Sprint


def crear_sprint(nombre, objetivo, fecha_inicio, fecha_fin, capacidad, estado, idproyecto):
    sprint = Sprint(
        nombre=nombre,
        objetivo=objetivo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        capacidad=capacidad,
        estado=estado,
        idproyecto=idproyecto
    )
    db.session.add(sprint)
    db.session.commit()
    return sprint


def listar_sprints(idproyecto=None):
    query = Sprint.query
    if idproyecto is not None:
        query = query.filter_by(idproyecto=idproyecto)
    return query.order_by(Sprint.fecha_inicio.asc()).all()


def obtener_sprint_por_id(idsprint):
    return Sprint.query.get(idsprint)


def actualizar_sprint(idsprint, datos):
    sprint = Sprint.query.get(idsprint)
    if not sprint:
        return None
    for clave, valor in datos.items():
        setattr(sprint, clave, valor)
    db.session.commit()
    return sprint


def eliminar_sprint(idsprint):
    sprint = Sprint.query.get(idsprint)
    if sprint:
        db.session.delete(sprint)
        db.session.commit()
        return True
    return False
