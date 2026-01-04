from app import db
from sqlalchemy.orm import relationship

class Roll(db.Model):
    __tablename__ = 'roll'
    idroll = db.Column(db.Integer, primary_key=True)
    nombre_roll = db.Column(db.Text, nullable=False, unique=True)
    usuarios = relationship('Usuario', back_populates='rol')

class Usuario(db.Model):
    __tablename__ = 'usuario'
    idusuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    correo = db.Column(db.Text, nullable=False, unique=True)
    idroll = db.Column(db.Integer, db.ForeignKey('roll.idroll'))
    activo = db.Column(db.Boolean, nullable=False, default=True)

    # Relaciones
    rol = relationship('Roll', back_populates='usuarios')
    proyectos = relationship('Proyecto', back_populates='usuario')
    tareas_asignadas = relationship('Tarea', back_populates='usuario_asignado', foreign_keys='Tarea.idusuario_asignado')
    tareas_creadas = relationship('Tarea', back_populates='creador', foreign_keys='Tarea.creada_por')
    comentarios = relationship('Comentario', back_populates='usuario')
    adjuntos = relationship('Adjunto', back_populates='usuario')
    historial = relationship('Historial', back_populates='usuario')
    notificaciones = relationship('Notificacion', back_populates='usuario')
    usuario_proyectos = relationship('UsuarioProyecto', back_populates='usuario')
    agendas = relationship('Agenda', back_populates='usuario')

class Proyecto(db.Model):
    __tablename__ = 'proyecto'
    idproyecto = db.Column(db.Integer, primary_key=True)
    nombre_proyecto = db.Column(db.Text, nullable=False)
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    fecha_creacion = db.Column(db.Date, nullable=False)
    logoproyecto = db.Column(db.LargeBinary)

    usuario = relationship('Usuario', back_populates='proyectos')
    tareas = relationship('Tarea', back_populates='proyecto')
    usuario_proyectos = relationship('UsuarioProyecto', back_populates='proyecto')
    agendas = relationship('Agenda', back_populates='proyecto')
    sprints = relationship('Sprint', back_populates='proyecto')

class UsuarioProyecto(db.Model):
    __tablename__ = 'usuario_proyecto'
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'), primary_key=True)
    idproyecto = db.Column(db.Integer, db.ForeignKey('proyecto.idproyecto'), primary_key=True)
    rol = db.Column(db.Text)
    usuario = relationship('Usuario', back_populates='usuario_proyectos')
    proyecto = relationship('Proyecto', back_populates='usuario_proyectos')

class Prioridad(db.Model):
    __tablename__ = 'prioridad'
    idprioridad = db.Column(db.Integer, primary_key=True)
    nombre_prioridad = db.Column(db.Text, nullable=False)
    color = db.Column(db.Text)
    tareas = relationship('Tarea', back_populates='prioridad')

class Estado(db.Model):
    __tablename__ = 'estado'
    idestado = db.Column(db.Integer, primary_key=True)
    nombre_estado = db.Column(db.String(120), nullable=False)
    orden = db.Column(db.Integer)
    color = db.Column(db.String(32))

    historial_anterior = relationship(
        'Historial',
        back_populates='estado_anterior_ref',
        foreign_keys='Historial.estado_anterior'
    )
    historial_nuevo = relationship(
        'Historial',
        back_populates='estado_nuevo_ref',
        foreign_keys='Historial.estado_nuevo'
    )
    tareas = relationship('Tarea', back_populates='estado')

class TipoTarea(db.Model):
    __tablename__ = 'tipo_tarea'
    idtipo_tarea = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    tareas = relationship('Tarea', back_populates='tipo_tarea')

class Adjunto(db.Model):
    __tablename__ = 'adjunto'
    idadjunto = db.Column(db.Integer, primary_key=True)
    ruta_archivo = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime)
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    descripcion = db.Column(db.Text)
    tareas = relationship('Tarea', back_populates='adjunto')
    comentarios = relationship('Comentario', back_populates='adjunto')
    historial = relationship('Historial', back_populates='adjunto')
    usuario = relationship('Usuario', back_populates='adjuntos')

class Tarea(db.Model):
    __tablename__ = 'tarea'
    idtarea = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    idproyecto = db.Column(db.Integer, db.ForeignKey('proyecto.idproyecto'))
    idusuario_asignado = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    fecha_creacion = db.Column(db.DateTime)
    fecha_limite = db.Column(db.Date)
    idtipo_tarea = db.Column(db.Integer, db.ForeignKey('tipo_tarea.idtipo_tarea'))
    idprioridad = db.Column(db.Integer, db.ForeignKey('prioridad.idprioridad'))
    idestado = db.Column(db.Integer, db.ForeignKey('estado.idestado'))
    idadjunto = db.Column(db.Integer, db.ForeignKey('adjunto.idadjunto'))
    creada_por = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    idsprint = db.Column(db.Integer, db.ForeignKey('sprint.idsprint'))
    idsprint_grupo = db.Column(db.Integer, db.ForeignKey('sprint_grupo.idsprint_grupo'))
    story_points = db.Column(db.Integer)
    prioridad_scrum = db.Column(db.Text)
    backlog_rank = db.Column(db.Integer)

    # Relaciones
    proyecto = relationship('Proyecto', back_populates='tareas')
    usuario_asignado = relationship('Usuario', back_populates='tareas_asignadas', foreign_keys=[idusuario_asignado])
    creador = relationship('Usuario', back_populates='tareas_creadas', foreign_keys=[creada_por])
    tipo_tarea = relationship('TipoTarea', back_populates='tareas')
    prioridad = relationship('Prioridad', back_populates='tareas')
    estado = relationship('Estado', back_populates='tareas')
    adjunto = relationship('Adjunto', back_populates='tareas')
    comentarios = relationship('Comentario', back_populates='tarea')
    historial = relationship('Historial', back_populates='tarea')
    notificaciones = relationship('Notificacion', back_populates='tarea')
    sprint = relationship('Sprint', back_populates='tareas')
    sprint_grupo = relationship('SprintGrupo', back_populates='tareas')
    predecesores = relationship(
        'TareaDependencia',
        foreign_keys='TareaDependencia.idtarea',
        back_populates='tarea'
    )
    sucesores = relationship(
        'TareaDependencia',
        foreign_keys='TareaDependencia.idpredecesor',
        back_populates='predecesor'
    )


class TareaDependencia(db.Model):
    __tablename__ = 'tarea_dependencia'
    iddependencia = db.Column(db.Integer, primary_key=True)
    idtarea = db.Column(db.Integer, db.ForeignKey('tarea.idtarea'), nullable=False)
    idpredecesor = db.Column(db.Integer, db.ForeignKey('tarea.idtarea'), nullable=False)
    tipo = db.Column(db.String(2), nullable=False, default='FS')
    lag_dias = db.Column(db.Integer, nullable=False, default=0)

    tarea = relationship('Tarea', foreign_keys=[idtarea], back_populates='predecesores')
    predecesor = relationship('Tarea', foreign_keys=[idpredecesor], back_populates='sucesores')

class Comentario(db.Model):
    __tablename__ = 'comentario'
    idcomentario = db.Column(db.Integer, primary_key=True)
    idtarea = db.Column(db.Integer, db.ForeignKey('tarea.idtarea'))
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime)
    idadjunto = db.Column(db.Integer, db.ForeignKey('adjunto.idadjunto'))
    idestado = db.Column(db.Integer, db.ForeignKey('estado.idestado'))

    tarea = relationship('Tarea', back_populates='comentarios')
    usuario = relationship('Usuario', back_populates='comentarios')
    adjunto = relationship('Adjunto', back_populates='comentarios')
    estado = relationship('Estado')  # <-- NUEVO

class Historial(db.Model):
    __tablename__ = 'historial'
    idhistorial = db.Column(db.Integer, primary_key=True)
    idtarea = db.Column(db.Integer, db.ForeignKey('tarea.idtarea'))
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    fecha = db.Column(db.DateTime)
    descripcion = db.Column(db.Text)
    estado_anterior = db.Column(db.Integer, db.ForeignKey('estado.idestado'))
    estado_nuevo = db.Column(db.Integer, db.ForeignKey('estado.idestado'))
    idadjunto = db.Column(db.Integer, db.ForeignKey('adjunto.idadjunto'))

    tarea = relationship('Tarea', back_populates='historial')
    usuario = relationship('Usuario', back_populates='historial')
    adjunto = relationship('Adjunto', back_populates='historial')
    estado_anterior_ref = relationship('Estado', foreign_keys=[estado_anterior], back_populates='historial_anterior')
    estado_nuevo_ref = relationship('Estado', foreign_keys=[estado_nuevo], back_populates='historial_nuevo')

class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    idnotificacion = db.Column(db.Integer, primary_key=True)
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    idtarea = db.Column(db.Integer, db.ForeignKey('tarea.idtarea'))
    mensaje = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime)
    tipo = db.Column(db.Text)
    leida = db.Column(db.Boolean, default=False)
    destinatarios = db.Column(db.Text)

    usuario = relationship('Usuario', back_populates='notificaciones')
    tarea = relationship('Tarea', back_populates='notificaciones')

class Agenda(db.Model):
    __tablename__ = 'agenda'
    idagenda = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text, nullable=False, default='Reunion')
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime)
    ubicacion = db.Column(db.Text)
    cliente = db.Column(db.Text)
    contacto = db.Column(db.Text)
    notas = db.Column(db.Text)
    estado = db.Column(db.Text, default='Pendiente')
    recordatorio_enviado = db.Column(db.Boolean, default=False)
    recordatorio_enviado_en = db.Column(db.DateTime)
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    idproyecto = db.Column(db.Integer, db.ForeignKey('proyecto.idproyecto'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

    usuario = relationship('Usuario', back_populates='agendas')
    proyecto = relationship('Proyecto', back_populates='agendas')


class Sprint(db.Model):
    __tablename__ = 'sprint'
    idsprint = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    objetivo = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    capacidad = db.Column(db.Integer)
    estado = db.Column(db.Text, default='Planeado')
    goal = db.Column(db.Text)
    definicion_done = db.Column(db.Text)
    idproyecto = db.Column(db.Integer, db.ForeignKey('proyecto.idproyecto'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

    proyecto = relationship('Proyecto', back_populates='sprints')
    tareas = relationship('Tarea', back_populates='sprint')
    grupos = relationship('SprintGrupo', back_populates='sprint')


class SprintGrupo(db.Model):
    __tablename__ = 'sprint_grupo'
    idsprint_grupo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    orden = db.Column(db.Integer)
    idsprint = db.Column(db.Integer, db.ForeignKey('sprint.idsprint'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

    sprint = relationship('Sprint', back_populates='grupos')
    tareas = relationship('Tarea', back_populates='sprint_grupo')


class SprintRol(db.Model):
    __tablename__ = 'sprint_rol'
    idsprint_rol = db.Column(db.Integer, primary_key=True)
    idsprint = db.Column(db.Integer, db.ForeignKey('sprint.idsprint'))
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    rol = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

    sprint = relationship('Sprint')
    usuario = relationship('Usuario')


class SprintRetro(db.Model):
    __tablename__ = 'sprint_retro'
    idsprint_retro = db.Column(db.Integer, primary_key=True)
    idsprint = db.Column(db.Integer, db.ForeignKey('sprint.idsprint'))
    notas = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

    sprint = relationship('Sprint')


class SprintBurndown(db.Model):
    __tablename__ = 'sprint_burndown'
    idsprint_burndown = db.Column(db.Integer, primary_key=True)
    idsprint = db.Column(db.Integer, db.ForeignKey('sprint.idsprint'))
    fecha = db.Column(db.Date, nullable=False)
    restante = db.Column(db.Integer, nullable=False, default=0)

    sprint = relationship('Sprint')


class CorreosDestino(db.Model):
    __tablename__ = 'correos_destinos'
    iddestino = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.Text, nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, server_default=db.func.now())
