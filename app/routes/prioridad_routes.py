from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.prioridad_crud import *

prioridad_bp = Blueprint('prioridad', __name__, url_prefix='/prioridades')

@prioridad_bp.route('/')
def vista_prioridades():
    prioridades = listar_prioridades()
    return render_template('prioridades/prioridades_view.html', prioridades=prioridades)

@prioridad_bp.route('/nuevo', methods=['POST'])
def nueva_prioridad():
    crear_prioridad(**request.form.to_dict())
    return redirect(url_for('prioridad.vista_prioridades'))

@prioridad_bp.route('/editar/<int:idprioridad>', methods=['POST'])
def editar_prioridad(idprioridad):
    datos = request.form.to_dict()
    actualizar_prioridad(idprioridad, datos)
    return redirect(url_for('prioridad.vista_prioridades'))

@prioridad_bp.route('/eliminar/<int:idprioridad>', methods=['POST'])
def eliminar_prioridad_view(idprioridad):
    eliminar_prioridad(idprioridad)
    return redirect(url_for('prioridad.vista_prioridades'))

@prioridad_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([p.as_dict() for p in listar_prioridades()])
