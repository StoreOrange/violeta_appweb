from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.roll_crud import *

roll_bp = Blueprint('roll', __name__, url_prefix='/roles')

@roll_bp.route('/')
def vista_rolls():
    rolls = listar_rolls()
    return render_template('roles/rolls_view.html', rolls=rolls)

@roll_bp.route('/nuevo', methods=['POST'])
def nuevo_roll():
    nombre = request.form['nombre_roll']
    crear_roll(nombre)
    return redirect(url_for('roll.vista_rolls'))

@roll_bp.route('/eliminar/<int:idroll>', methods=['POST'])
def eliminar_roll_view(idroll):
    eliminar_roll(idroll)
    return redirect(url_for('roll.vista_rolls'))

@roll_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([r.as_dict() for r in listar_rolls()])
