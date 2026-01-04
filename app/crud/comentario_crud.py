# app/crud/comentario_crud.py
from app import db
from app.models import Comentario

def crear_comentario(idtarea, idusuario, comentario, fecha=None, idadjunto=None, idestado=None):
    coment = Comentario(
        idtarea=idtarea,
        idusuario=idusuario,
        comentario=comentario,
        fecha=fecha,
        idadjunto=idadjunto,
        idestado=idestado
    )
    db.session.add(coment)
    db.session.commit()
    return coment

def obtener_comentario_por_id(idcomentario):
    return Comentario.query.get(idcomentario)

def listar_comentarios():
    return Comentario.query.all()

def actualizar_comentario(idcomentario, datos):
    coment = Comentario.query.get(idcomentario)
    if not coment:
        return None
    for clave, valor in datos.items():
        setattr(coment, clave, valor)
    db.session.commit()
    return coment

def eliminar_comentario(idcomentario):
    coment = Comentario.query.get(idcomentario)
    if coment:
        db.session.delete(coment)
        db.session.commit()
        return True
    return False
