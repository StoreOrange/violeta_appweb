# app/crud/prioridad_crud.py
from app import db
from app.models import Prioridad

def crear_prioridad(nombre_prioridad, color=None):
    prioridad = Prioridad(nombre_prioridad=nombre_prioridad, color=color)
    db.session.add(prioridad)
    db.session.commit()
    return prioridad

def obtener_prioridad_por_id(idprioridad):
    return Prioridad.query.get(idprioridad)

def listar_prioridades():
    return Prioridad.query.all()

def actualizar_prioridad(idprioridad, datos):
    prioridad = Prioridad.query.get(idprioridad)
    if not prioridad:
        return None
    for clave, valor in datos.items():
        setattr(prioridad, clave, valor)
    db.session.commit()
    return prioridad

def eliminar_prioridad(idprioridad):
    prioridad = Prioridad.query.get(idprioridad)
    if prioridad:
        db.session.delete(prioridad)
        db.session.commit()
        return True
    return False
