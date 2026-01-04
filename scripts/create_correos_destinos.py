from sqlalchemy import text
from app import create_app, db

DEFAULT_EMAIL = 'oddgarcia.samuel@gmail.com'

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS correos_destinos (
    iddestino SERIAL PRIMARY KEY,
    correo TEXT UNIQUE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def main():
    app = create_app()
    with app.app_context():
        db.session.execute(text(CREATE_TABLE_SQL))
        db.session.execute(
            text("""
                INSERT INTO correos_destinos (correo, activo)
                VALUES (:correo, TRUE)
                ON CONFLICT (correo) DO NOTHING
            """),
            {"correo": DEFAULT_EMAIL}
        )
        db.session.commit()
        print("Tabla correos_destinos lista.")


if __name__ == '__main__':
    main()
