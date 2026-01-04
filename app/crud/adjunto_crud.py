# app/crud/adjunto_crud.py
from app import db
from app.models import Adjunto

def crear_adjunto(ruta_archivo, tipo, idusuario, descripcion=None, fecha_subida=None):
    adjunto = Adjunto(
        ruta_archivo=ruta_archivo,
        tipo=tipo,
        idusuario=idusuario,
        descripcion=descripcion,
        fecha_subida=fecha_subida
    )
    db.session.add(adjunto)
    db.session.commit()
    return adjunto

def obtener_adjunto_por_id(idadjunto):
    return Adjunto.query.get(idadjunto)

def listar_adjuntos():
    return Adjunto.query.all()

def actualizar_adjunto(idadjunto, datos):
    adjunto = Adjunto.query.get(idadjunto)
    if not adjunto:
        return None
    for clave, valor in datos.items():
        setattr(adjunto, clave, valor)
    db.session.commit()
    return adjunto

def eliminar_adjunto(idadjunto):
    adjunto = Adjunto.query.get(idadjunto)
    if adjunto:
        db.session.delete(adjunto)
        db.session.commit()
        return True
    return False
