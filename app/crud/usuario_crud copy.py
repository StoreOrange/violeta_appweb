# app/crud/usuario_crud.py
from app import db
from app.models import Usuario
from werkzeug.security import generate_password_hash

def crear_usuario(nombre, correo, password, idroll, activo=True):
    usuario = Usuario(
        nombre=nombre,
        correo=correo,
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
    return Usuario.query.filter_by(correo=correo).first()

def listar_usuarios():
    return Usuario.query.all()

def actualizar_usuario(idusuario, datos):
    usuario = Usuario.query.get(idusuario)
    if not usuario:
        return None
    for clave, valor in datos.items():
        if clave == "password":
            valor = generate_password_hash(valor)
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
