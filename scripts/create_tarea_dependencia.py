from sqlalchemy import text
from app import create_app, db


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tarea_dependencia (
    iddependencia SERIAL PRIMARY KEY,
    idtarea INTEGER NOT NULL REFERENCES tarea(idtarea) ON DELETE CASCADE,
    idpredecesor INTEGER NOT NULL REFERENCES tarea(idtarea) ON DELETE CASCADE,
    tipo VARCHAR(2) NOT NULL DEFAULT 'FS',
    lag_dias INTEGER NOT NULL DEFAULT 0
);
"""


def main():
    app = create_app()
    with app.app_context():
        db.session.execute(text(CREATE_TABLE_SQL))
        db.session.commit()
        print("Tabla tarea_dependencia lista.")


if __name__ == "__main__":
    main()
