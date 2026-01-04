import secrets
import time

from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify, flash
from sqlalchemy import func, desc
from app import db
from app.models import Proyecto, Comentario, Tarea, Estado
from app.crud.usuario_crud import *
from app.crud.roll_crud import listar_rolls
from werkzeug.security import check_password_hash, generate_password_hash
from app.utils.email import send_password_change_code_email

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuarios')

def _require_login():
    if not session.get('user_id'):
        flash('Debes iniciar sesion para continuar.')
        return redirect(url_for('usuario.login'))
    return None

# --- Vista de usuarios (ADMIN) ---
@usuario_bp.route('/')
def vista_usuarios():
    guard = _require_login()
    if guard:
        return guard
    usuarios = listar_usuarios()
    roles = listar_rolls()
    return render_template('usuario/usuarios_view.html', usuarios=usuarios, roles=roles)

# --- Nuevo usuario desde formulario (ADMIN) ---
@usuario_bp.route('/nuevo', methods=['POST'])
def nuevo_usuario():
    guard = _require_login()
    if guard:
        return guard
    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    idroll = request.form['idroll']
    crear_usuario(nombre, correo, password, idroll)
    return redirect(url_for('usuario.vista_usuarios'))

# --- Editar usuario desde formulario (ADMIN) ---
@usuario_bp.route('/editar/<int:idusuario>', methods=['POST'])
def editar_usuario(idusuario):
    guard = _require_login()
    if guard:
        return guard
    datos = request.form.to_dict()
    codigo_confirmacion = datos.pop('codigo_confirmacion', '').strip()
    # Si hay password, exigir codigo de confirmacion
    if 'password' in datos and datos['password']:
        pending_codes = session.get('password_change_codes', {})
        entry = pending_codes.get(str(idusuario))
        ahora = time.time()
        if not entry or entry.get('expires_at', 0) < ahora:
            flash('El codigo de confirmacion expiro o no existe. Solicita uno nuevo.')
            return redirect(url_for('usuario.vista_usuarios'))
        if not codigo_confirmacion:
            flash('Debes ingresar el codigo de confirmacion enviado al correo.')
            return redirect(url_for('usuario.vista_usuarios'))
        if not check_password_hash(entry.get('code_hash', ''), codigo_confirmacion):
            flash('Codigo de confirmacion incorrecto.')
            return redirect(url_for('usuario.vista_usuarios'))
    elif 'password' in datos:
        datos.pop('password')  # No actualizar si está vacía
    actualizar_usuario(idusuario, datos)
    if codigo_confirmacion and 'password' in request.form and request.form['password']:
        pending_codes.pop(str(idusuario), None)
        session['password_change_codes'] = pending_codes
    return redirect(url_for('usuario.vista_usuarios'))

# --- Eliminar usuario (ADMIN) ---
@usuario_bp.route('/eliminar/<int:idusuario>', methods=['POST'])
def eliminar_usuario_view(idusuario):
    guard = _require_login()
    if guard:
        return guard
    eliminar_usuario(idusuario)
    return redirect(url_for('usuario.vista_usuarios'))

# --- REST API: lista usuarios JSON ---
@usuario_bp.route('/api', methods=['GET'])
def api_listar():
    guard = _require_login()
    if guard:
        return guard
    return jsonify([u.as_dict() for u in listar_usuarios()])

# =====================
#      LOGIN USUARIO
# =====================
@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        identificador = request.form.get('identificador') or request.form.get('correo')
        password = request.form['password']
        usuario = obtener_usuario_por_identificador(identificador)
        if usuario and not usuario.activo:
            error = "Usuario inactivo"
        elif usuario and check_password_hash(usuario.password, password):
            session['user_id'] = usuario.idusuario
            session['user_nombre'] = usuario.nombre
            session['user_rol'] = usuario.idroll
            return redirect(url_for('usuario.dashboard'))  # Cambia esto por tu menú o dashboard principal
        else:
            if error is None:
                error = "Credenciales incorrectas"
    return render_template('usuario/login.html', error=error)

# --- Logout sencillo ---
@usuario_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('usuario.login'))

@usuario_bp.route('/dashboard')
def dashboard():
    guard = _require_login()
    if guard:
        return guard
    ultimo_proyecto = Proyecto.query.order_by(Proyecto.fecha_creacion.desc()).first()
    ultimo_comentario = Comentario.query.order_by(Comentario.fecha.desc()).first()

    total_proyectos = Proyecto.query.count()
    total_tareas = Tarea.query.count()
    total_comentarios = Comentario.query.count()

    tareas_mas_comentarios_rows = (
        db.session.query(Tarea, func.count(Comentario.idcomentario).label('total'))
        .outerjoin(Comentario, Comentario.idtarea == Tarea.idtarea)
        .group_by(Tarea.idtarea)
        .order_by(desc('total'), Tarea.idtarea.desc())
        .limit(5)
        .all()
    )
    tareas_mas_comentarios = [
        {"tarea": tarea, "total": total}
        for tarea, total in tareas_mas_comentarios_rows
    ]
    hay_comentarios = any(item["total"] > 0 for item in tareas_mas_comentarios)

    estados = Estado.query.all()
    tareas = Tarea.query.all()
    estado_map = {estado.idestado: {"estado": estado, "tareas": []} for estado in estados}
    sin_estado = {"nombre": "Sin Estado", "color": "#cdd5ea", "tareas": []}

    for tarea in tareas:
        if tarea.idestado in estado_map:
            estado_map[tarea.idestado]["tareas"].append(tarea)
        else:
            sin_estado["tareas"].append(tarea)

    tareas_por_estado = []
    for estado in estados:
        data = estado_map[estado.idestado]
        tareas_por_estado.append(
            {
                "nombre": estado.nombre_estado,
                "color": estado.color or "#cdd5ea",
                "tareas": data["tareas"],
                "total": len(data["tareas"]),
            }
        )
    if sin_estado["tareas"]:
        tareas_por_estado.append(
            {
                "nombre": sin_estado["nombre"],
                "color": sin_estado["color"],
                "tareas": sin_estado["tareas"],
                "total": len(sin_estado["tareas"]),
            }
        )

    return render_template(
        'usuario/dashboard.html',
        ultimo_proyecto=ultimo_proyecto,
        ultimo_comentario=ultimo_comentario,
        total_proyectos=total_proyectos,
        total_tareas=total_tareas,
        total_comentarios=total_comentarios,
        tareas_mas_comentarios=tareas_mas_comentarios,
        hay_comentarios=hay_comentarios,
        tareas_por_estado=tareas_por_estado
    )


@usuario_bp.route('/enviar-codigo/<int:idusuario>', methods=['POST'])
def enviar_codigo_cambio(idusuario):
    guard = _require_login()
    if guard:
        return guard
    usuario = obtener_usuario_por_id(idusuario)
    if not usuario or not usuario.correo:
        flash('No se encontro el correo del usuario.')
        return redirect(url_for('usuario.vista_usuarios'))

    codigo = f"{secrets.randbelow(1000000):06d}"
    pending_codes = session.get('password_change_codes', {})
    pending_codes[str(idusuario)] = {
        'code_hash': generate_password_hash(codigo),
        'expires_at': time.time() + 600,
    }
    session['password_change_codes'] = pending_codes

    ok, error = send_password_change_code_email(usuario, codigo)
    if not ok:
        flash(f'No se pudo enviar el codigo: {error}')
    else:
        flash('Codigo de confirmacion enviado al correo del usuario.')
    return redirect(url_for('usuario.vista_usuarios'))
