from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.crud.proyecto_crud import *
from app.crud.usuario_crud import listar_usuarios
from datetime import datetime


proyecto_bp = Blueprint('proyecto', __name__, url_prefix='/proyectos')

@proyecto_bp.route('/')
def vista_proyectos():
    proyectos = listar_proyectos()
    usuarios = listar_usuarios()
    return render_template('proyectos/proyectos_view.html', proyectos=proyectos, usuarios=usuarios)

@proyecto_bp.route('/nuevo', methods=['POST'])
def nuevo_proyecto():
    nombre = request.form['nombre_proyecto']
    idusuario = request.form['idusuario']
    fecha_str = request.form['fecha_creacion']   
    fecha_creacion = datetime.strptime(fecha_str, '%Y-%m-%d')  
    crear_proyecto(nombre, idusuario, fecha_creacion)
    return redirect(url_for('proyecto.vista_proyectos'))


@proyecto_bp.route('/eliminar/<int:idproyecto>', methods=['POST'])
def eliminar_proyecto_view(idproyecto):
    eliminar_proyecto(idproyecto)
    return redirect(url_for('proyecto.vista_proyectos'))

@proyecto_bp.route('/api', methods=['GET'])
def api_listar():
    return jsonify([p.as_dict() for p in listar_proyectos()])


@proyecto_bp.route('/editar/<int:idproyecto>', methods=['POST'])
def editar_proyecto_view(idproyecto):
    nombre = request.form['nombre_proyecto']
    idusuario = request.form['idusuario']
    fecha_str = request.form['fecha_creacion']
    fecha_creacion = datetime.strptime(fecha_str, '%Y-%m-%d')
    datos = {
        "nombre_proyecto": nombre,
        "idusuario": idusuario,
        "fecha_creacion": fecha_creacion,
    }
    actualizar_proyecto(idproyecto, datos)
    return redirect(url_for('proyecto.vista_proyectos'))

