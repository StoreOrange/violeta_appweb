# app/crud/historial_crud.py
from app import db
from app.models import Historial

def crear_historial(idtarea, idusuario, fecha, descripcion, estado_anterior, estado_nuevo, idadjunto):
    hist = Historial(
        idtarea=idtarea,
        idusuario=idusuario,
        fecha=fecha,
        descripcion=descripcion,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        idadjunto=idadjunto
    )
    db.session.add(hist)
    db.session.commit()
    return hist

def obtener_historial_por_id(idhistorial):
    return Historial.query.get(idhistorial)

def listar_historiales():
    return Historial.query.all()

def actualizar_historial(idhistorial, datos):
    hist = Historial.query.get(idhistorial)
    if not hist:
        return None
    for clave, valor in datos.items():
        setattr(hist, clave, valor)
    db.session.commit()
    return hist

def eliminar_historial(idhistorial):
    hist = Historial.query.get(idhistorial)
    if hist:
        db.session.delete(hist)
        db.session.commit()
        return True
    return False
