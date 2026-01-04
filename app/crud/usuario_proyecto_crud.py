# app/crud/usuario_proyecto_crud.py
from app import db
from app.models import UsuarioProyecto

def crear_usuario_proyecto(idusuario, idproyecto, rol=None):
    up = UsuarioProyecto(idusuario=idusuario, idproyecto=idproyecto, rol=rol)
    db.session.add(up)
    db.session.commit()
    return up

def obtener_usuario_proyecto(idusuario, idproyecto):
    return UsuarioProyecto.query.get((idusuario, idproyecto))

def listar_usuario_proyectos():
    return UsuarioProyecto.query.all()

def actualizar_usuario_proyecto(idusuario, idproyecto, rol):
    up = UsuarioProyecto.query.get((idusuario, idproyecto))
    if not up:
        return None
    up.rol = rol
    db.session.commit()
    return up

def eliminar_usuario_proyecto(idusuario, idproyecto):
    up = UsuarioProyecto.query.get((idusuario, idproyecto))
    if up:
        db.session.delete(up)
        db.session.commit()
        return True
    return False
