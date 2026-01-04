# app/crud/proyecto_crud.py
from app import db
from app.models import Proyecto

def crear_proyecto(nombre_proyecto, idusuario, fecha_creacion, logoproyecto=None):
    proyecto = Proyecto(
        nombre_proyecto=nombre_proyecto,
        idusuario=idusuario,
        fecha_creacion=fecha_creacion,
        logoproyecto=logoproyecto
    )
    db.session.add(proyecto)
    db.session.commit()
    return proyecto

def obtener_proyecto_por_id(idproyecto):
    return Proyecto.query.get(idproyecto)

def listar_proyectos():
    return Proyecto.query.all()

def actualizar_proyecto(idproyecto, datos):
    proyecto = Proyecto.query.get(idproyecto)
    if not proyecto:
        return None
    for clave, valor in datos.items():
        setattr(proyecto, clave, valor)
    db.session.commit()
    return proyecto

def eliminar_proyecto(idproyecto):
    proyecto = Proyecto.query.get(idproyecto)
    if proyecto:
        db.session.delete(proyecto)
        db.session.commit()
        return True
    return False
