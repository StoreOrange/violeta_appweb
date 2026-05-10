ALTER TABLE tarea
ADD COLUMN IF NOT EXISTS equipo_desarrollo boolean NOT NULL DEFAULT false;

ALTER TABLE sprint
ADD COLUMN IF NOT EXISTS goal text;

ALTER TABLE sprint
ADD COLUMN IF NOT EXISTS definicion_done text;

ALTER TABLE sprint
ADD COLUMN IF NOT EXISTS creado_en timestamp DEFAULT now();

ALTER TABLE sprint_grupo
ADD COLUMN IF NOT EXISTS creado_en timestamp DEFAULT now();

ALTER TABLE sprint_rol
ADD COLUMN IF NOT EXISTS idusuario integer;

ALTER TABLE sprint_rol
ADD COLUMN IF NOT EXISTS creado_en timestamp DEFAULT now();

ALTER TABLE sprint_retro
ADD COLUMN IF NOT EXISTS creado_en timestamp DEFAULT now();

ALTER TABLE tarea
ADD COLUMN IF NOT EXISTS story_points integer;

ALTER TABLE tarea
ADD COLUMN IF NOT EXISTS prioridad_scrum text;

ALTER TABLE tarea
ADD COLUMN IF NOT EXISTS backlog_rank integer;

CREATE TABLE IF NOT EXISTS tarea_dependencia (
    iddependencia serial PRIMARY KEY,
    idtarea integer NOT NULL REFERENCES tarea(idtarea),
    idpredecesor integer NOT NULL REFERENCES tarea(idtarea),
    tipo varchar(2) NOT NULL DEFAULT 'FS',
    lag_dias integer NOT NULL DEFAULT 0
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_sprint_rol_usuario'
    ) THEN
        ALTER TABLE sprint_rol
        ADD CONSTRAINT fk_sprint_rol_usuario
        FOREIGN KEY (idusuario) REFERENCES usuario(idusuario);
    END IF;
END $$;
