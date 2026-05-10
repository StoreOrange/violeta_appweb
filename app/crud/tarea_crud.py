# app/crud/tarea_crud.py
from app import db
from app.models import Estado, Tarea

def crear_tarea(titulo, descripcion, idproyecto, idusuario_asignado, fecha_creacion, fecha_limite, idtipo_tarea, idprioridad, idestado, idadjunto, creada_por, equipo_desarrollo=False):
    tarea = Tarea(
        titulo=titulo,
        descripcion=descripcion,
        idproyecto=idproyecto,
        idusuario_asignado=idusuario_asignado,
        equipo_desarrollo=equipo_desarrollo,
        fecha_creacion=fecha_creacion,
        fecha_limite=fecha_limite,
        idtipo_tarea=idtipo_tarea,
        idprioridad=idprioridad,
        idestado=idestado,
        idadjunto=idadjunto,
        creada_por=creada_por
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea

def obtener_tarea_por_id(idtarea):
    return Tarea.query.get(idtarea)

def listar_tareas(idproyecto=None):
    if idproyecto is not None:
        return Tarea.query.filter_by(idproyecto=idproyecto).all()
    return Tarea.query.all()

def actualizar_tarea(idtarea, datos):
    tarea = Tarea.query.get(idtarea)
    if not tarea:
        return None
    for clave, valor in datos.items():
        setattr(tarea, clave, valor)
    db.session.commit()
    return tarea

def eliminar_tarea(idtarea):
    tarea = Tarea.query.get(idtarea)
    if tarea:
        db.session.delete(tarea)
        db.session.commit()
        return True
    return False


def listar_tareas_pendientes():
    # Aquí filtramos todas las tareas cuyo estado NO sea 'Completada'
    return Tarea.query.join(Estado).filter(Estado.nombre_estado != 'Completada').all()



