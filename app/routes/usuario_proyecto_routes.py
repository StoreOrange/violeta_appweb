from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.usuario_proyecto_crud import *

usuario_proyecto_bp = Blueprint('usuario_proyecto', __name__, url_prefix='/usuario-proyecto')

@usuario_proyecto_bp.route('/')
def vista_usuario_proyecto():
    usuario_proyectos = listar_usuario_proyectos()
    return render_template('usuario_proyecto/usuario_proyecto_view.html', usuario_proyectos=usuario_proyectos)

@usuario_proyecto_bp.route('/nuevo', methods=['POST'])
def nuevo_usuario_proyecto():
    crear_usuario_proyecto(**request.form.to_dict())
    return redirect(url_for('usuario_proyecto.vista_usuario_proyecto'))

@usuario_proyecto_bp.route('/editar', methods=['POST'])
def editar_usuario_proyecto():
    datos = request.form.to_dict()
    actualizar_usuario_proyecto(datos['idusuario'], datos['idproyecto'], datos)
    return redirect(url_for('usuario_proyecto.vista_usuario_proyecto'))

@usuario_proyecto_bp.route('/eliminar', methods=['POST'])
def eliminar_usuario_proyecto_view():
    idusuario = request.form['idusuario']
    idproyecto = request.form['idproyecto']
    eliminar_usuario_proyecto(idusuario, idproyecto)
    return redirect(url_for('usuario_proyecto.vista_usuario_proyecto'))

@usuario_proyecto_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([up.as_dict() for up in listar_usuario_proyectos()])
