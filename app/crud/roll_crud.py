# app/crud/roll_crud.py
from app import db
from app.models import Roll

def crear_roll(nombre_roll):
    roll = Roll(nombre_roll=nombre_roll)
    db.session.add(roll)
    db.session.commit()
    return roll

def obtener_roll_por_id(idroll):
    return Roll.query.get(idroll)

def listar_rolls():
    return Roll.query.all()

def actualizar_roll(idroll, nombre_roll):
    roll = Roll.query.get(idroll)
    if not roll:
        return None
    roll.nombre_roll = nombre_roll
    db.session.commit()
    return roll

def eliminar_roll(idroll):
    roll = Roll.query.get(idroll)
    if roll:
        db.session.delete(roll)
        db.session.commit()
        return True
    return False
 