# app/crud/estado_crud.py
from app import db
from app.models import Estado

def crear_estado(nombre_estado, orden=None, color=None):
    estado = Estado(nombre_estado=nombre_estado, orden=orden, color=color)
    db.session.add(estado)
    db.session.commit()
    return estado

def obtener_estado_por_id(idestado):
    return Estado.query.get(idestado)

def listar_estados():
    return Estado.query.all()

def actualizar_estado(idestado, datos):
    estado = Estado.query.get(idestado)
    if not estado:
        return None
    for clave, valor in datos.items():
        setattr(estado, clave, valor)
    db.session.commit()
    return estado

def eliminar_estado(idestado):
    estado = Estado.query.get(idestado)
    if estado:
        db.session.delete(estado)
        db.session.commit()
        return True
    return False
