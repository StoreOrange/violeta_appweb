from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.tipo_tarea_crud import *

tipo_tarea_bp = Blueprint('tipo_tarea', __name__, url_prefix='/tipos-tarea')

@tipo_tarea_bp.route('/')
def vista_tipos_tarea():
    tipos = listar_tipos_tarea()
    return render_template('tipos_tarea/tipos_tarea_view.html', tipos=tipos)

@tipo_tarea_bp.route('/nuevo', methods=['POST'])
def nuevo_tipo_tarea():
    crear_tipo_tarea(**request.form.to_dict())
    return redirect(url_for('tipo_tarea.vista_tipos_tarea'))

@tipo_tarea_bp.route('/editar/<int:idtipo_tarea>', methods=['POST'])
def editar_tipo_tarea(idtipo_tarea):
    datos = request.form.to_dict()
    actualizar_tipo_tarea(idtipo_tarea, datos)
    return redirect(url_for('tipo_tarea.vista_tipos_tarea'))

@tipo_tarea_bp.route('/eliminar/<int:idtipo_tarea>', methods=['POST'])
def eliminar_tipo_tarea_view(idtipo_tarea):
    eliminar_tipo_tarea(idtipo_tarea)
    return redirect(url_for('tipo_tarea.vista_tipos_tarea'))

@tipo_tarea_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([t.as_dict() for t in listar_tipos_tarea()])
