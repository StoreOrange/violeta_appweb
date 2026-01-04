from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.historial_crud import *

historial_bp = Blueprint('historial', __name__, url_prefix='/historial')

@historial_bp.route('/')
def vista_historial():
    historial = listar_historial()
    return render_template('historial/historial_view.html', historial=historial)

@historial_bp.route('/nuevo', methods=['POST'])
def nuevo_historial():
    crear_historial(**request.form.to_dict())
    return redirect(url_for('historial.vista_historial'))

@historial_bp.route('/editar/<int:idhistorial>', methods=['POST'])
def editar_historial(idhistorial):
    datos = request.form.to_dict()
    actualizar_historial(idhistorial, datos)
    return redirect(url_for('historial.vista_historial'))

@historial_bp.route('/eliminar/<int:idhistorial>', methods=['POST'])
def eliminar_historial_view(idhistorial):
    eliminar_historial(idhistorial)
    return redirect(url_for('historial.vista_historial'))

@historial_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([h.as_dict() for h in listar_historial()])
