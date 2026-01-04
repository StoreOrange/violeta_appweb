from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.estado_crud import *

estado_bp = Blueprint('estado', __name__, url_prefix='/estados')

@estado_bp.route('/')
def vista_estados():
    estados = listar_estados()
    return render_template('estados/estados_view.html', estados=estados)

@estado_bp.route('/nuevo', methods=['POST'])
def nuevo_estado():
    crear_estado(**request.form.to_dict())
    return redirect(url_for('estado.vista_estados'))

@estado_bp.route('/editar/<int:idestado>', methods=['POST'])
def editar_estado(idestado):
    datos = request.form.to_dict()
    actualizar_estado(idestado, datos)
    return redirect(url_for('estado.vista_estados'))

@estado_bp.route('/eliminar/<int:idestado>', methods=['POST'])
def eliminar_estado_view(idestado):
    eliminar_estado(idestado)
    return redirect(url_for('estado.vista_estados'))

@estado_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([e.as_dict() for e in listar_estados()])
