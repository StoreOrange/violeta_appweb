# app/__init__.py

from flask import Flask, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import RequestEntityTooLarge


db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # <-- ¡ASÍ ESTÁ CORRECTO!
    db.init_app(app)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(_error):
        flash('El archivo supera el limite permitido de 25 MB.')
        return redirect(request.referrer or '/')

    from app.routes.main_routes import main_bp
    from app.routes.usuario_routes import usuario_bp
    from app.routes.proyecto_routes import proyecto_bp
    from app.routes.tipo_tarea_routes import tipo_tarea_bp
    from app.routes.prioridad_routes import prioridad_bp
    from app.routes.estado_routes import estado_bp
    from app.routes.tarea_routes import tarea_bp
    from app.routes.notificacion_routes import notificacion_bp
    from app.routes.comentario_routes import comentario_bp
    from app.routes.adjunto_routes import adjunto_bp
    from app.routes.reports import reports_bp
    from app.routes.agenda_routes import agenda_bp
    from app.routes.repositorios_routes import repositorios_bp
    from app.routes.seguimiento_routes import seguimiento_bp
    

    app.register_blueprint(main_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(proyecto_bp)
    app.register_blueprint(tipo_tarea_bp)
    app.register_blueprint(prioridad_bp)
    app.register_blueprint(estado_bp)
    app.register_blueprint(tarea_bp)
    app.register_blueprint(notificacion_bp)
    app.register_blueprint(comentario_bp)
    app.register_blueprint(adjunto_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(repositorios_bp)
    app.register_blueprint(seguimiento_bp)

    return app





