from .usuario_routes import usuario_bp
from .roll_routes import roll_bp
from .proyecto_routes import proyecto_bp
from .tarea_routes import tarea_bp
from .estado_routes import estado_bp
from .prioridad_routes import prioridad_bp
from .notificacion_routes import notificacion_bp
from .historial_routes import historial_bp
from .comentario_routes import comentario_bp
from .main_routes import main_bp
from .agenda_routes import agenda_bp
from .repositorios_routes import repositorios_bp
from .seguimiento_routes import seguimiento_bp

# Si usas factory pattern:
def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(roll_bp)
    app.register_blueprint(proyecto_bp)
    app.register_blueprint(tarea_bp)
    app.register_blueprint(estado_bp)
    app.register_blueprint(prioridad_bp)
    app.register_blueprint(notificacion_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(comentario_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(repositorios_bp)
    app.register_blueprint(seguimiento_bp)
