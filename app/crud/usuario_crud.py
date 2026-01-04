# app/crud/usuario_crud.py
from sqlalchemy import func, or_

from app import db
from app.models import Usuario
from werkzeug.security import generate_password_hash


def _normalize_email(correo):
    if correo is None:
        return None
    return correo.strip().lower()

def crear_usuario(nombre, correo, password, idroll, activo=True):
    usuario = Usuario(
        nombre=nombre,
        correo=_normalize_email(correo),
        password=generate_password_hash(password),
        idroll=idroll,
        activo=activo
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario

def obtener_usuario_por_id(idusuario):
    return Usuario.query.get(idusuario)

def obtener_usuario_por_correo(correo):
    correo_normalizado = _normalize_email(correo)
    if not correo_normalizado:
        return None
    return Usuario.query.filter(func.lower(Usuario.correo) == correo_normalizado).first()

def obtener_usuario_por_identificador(identificador):
    identificador_normalizado = (identificador or '').strip().lower()
    if not identificador_normalizado:
        return None
    return Usuario.query.filter(
        or_(
            func.lower(Usuario.correo) == identificador_normalizado,
            func.lower(Usuario.nombre) == identificador_normalizado,
        )
    ).first()

def listar_usuarios():
    return Usuario.query.all()

def actualizar_usuario(idusuario, datos):
    usuario = Usuario.query.get(idusuario)
    if not usuario:
        return None
    for clave, valor in datos.items():
        if clave == "password":
            valor = generate_password_hash(valor)
        if clave == "correo":
            valor = _normalize_email(valor)
        setattr(usuario, clave, valor)
    db.session.commit()
    return usuario

def eliminar_usuario(idusuario):
    usuario = Usuario.query.get(idusuario)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        return True
    return False
