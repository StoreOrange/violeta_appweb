# app/crud/tipo_tarea_crud.py
from app import db
from app.models import TipoTarea

def crear_tipo_tarea(nombre_tipo, descripcion=None):
    tipo = TipoTarea(nombre_tipo=nombre_tipo, descripcion=descripcion)
    db.session.add(tipo)
    db.session.commit()
    return tipo

def obtener_tipo_tarea_por_id(idtipo_tarea):
    return TipoTarea.query.get(idtipo_tarea)

def listar_tipos_tarea():
    return TipoTarea.query.all()

def actualizar_tipo_tarea(idtipo_tarea, datos):
    tipo = TipoTarea.query.get(idtipo_tarea)
    if not tipo:
        return None
    for clave, valor in datos.items():
        setattr(tipo, clave, valor)
    db.session.commit()
    return tipo

def eliminar_tipo_tarea(idtipo_tarea):
    tipo = TipoTarea.query.get(idtipo_tarea)
    if tipo:
        db.session.delete(tipo)
        db.session.commit()
        return True
    return False
