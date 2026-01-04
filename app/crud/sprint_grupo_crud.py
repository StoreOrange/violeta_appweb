# app/crud/sprint_grupo_crud.py
from app import db
from app.models import SprintGrupo


def crear_grupo(nombre, descripcion, orden, idsprint):
    grupo = SprintGrupo(
        nombre=nombre,
        descripcion=descripcion,
        orden=orden,
        idsprint=idsprint
    )
    db.session.add(grupo)
    db.session.commit()
    return grupo


def listar_grupos(idsprint=None):
    query = SprintGrupo.query
    if idsprint is not None:
        query = query.filter_by(idsprint=idsprint)
    return query.order_by(SprintGrupo.orden.asc().nulls_last(), SprintGrupo.idsprint_grupo.asc()).all()
