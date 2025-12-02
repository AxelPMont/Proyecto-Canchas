-- =========================================
-- LIMPIAR TODO (BORRAR TABLAS SI EXISTEN)
-- =========================================
DROP TABLE IF EXISTS transmisiones CASCADE;
DROP TABLE IF EXISTS partidos CASCADE;
DROP TABLE IF EXISTS torneo_equipos CASCADE;
DROP TABLE IF EXISTS grupos CASCADE;
DROP TABLE IF EXISTS canchas CASCADE;
DROP TABLE IF EXISTS torneos CASCADE;
DROP TABLE IF EXISTS equipos CASCADE;
DROP TABLE IF EXISTS divisiones CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- =========================================
-- 1. DIVISIONES (Segunda, Tercera, etc.)
-- =========================================
CREATE TABLE divisiones (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL UNIQUE  -- 'Segunda', 'Tercera'
);

-- =========================================
-- 2. TORNEOS
-- =========================================
CREATE TABLE torneos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,       -- "Copa Distrital 2025"
    temporada    VARCHAR(20)  NOT NULL,       -- '2025', '2025-2026'
    division_id  INTEGER      NOT NULL REFERENCES divisiones(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    estado       VARCHAR(20) DEFAULT 'activo' -- activo, finalizado, suspendido
);

CREATE INDEX idx_torneos_division
    ON torneos (division_id);

-- =========================================
-- 3. GRUPOS (A, B, C, etc. dentro de un torneo)
-- =========================================
CREATE TABLE grupos (
    id          SERIAL PRIMARY KEY,
    torneo_id   INTEGER NOT NULL REFERENCES torneos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    nombre      VARCHAR(50) NOT NULL,   -- 'Grupo A', 'Grupo B'
    codigo      VARCHAR(10) NOT NULL    -- 'A','B','C' para mostrar en pantalla
);

CREATE UNIQUE INDEX uq_grupos_torneo_codigo
    ON grupos (torneo_id, codigo);

-- =========================================
-- 4. EQUIPOS
-- =========================================
CREATE TABLE equipos (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    categoria   VARCHAR(50)      -- opcional
);

-- =========================================
-- 5. EQUIPOS POR TORNEO Y GRUPO
--    (asigna cada equipo a un torneo y grupo)
-- =========================================
CREATE TABLE torneo_equipos (
    id          SERIAL PRIMARY KEY,
    torneo_id   INTEGER NOT NULL REFERENCES torneos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    equipo_id   INTEGER NOT NULL REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    grupo_id    INTEGER REFERENCES grupos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- un equipo no puede repetirse dos veces en el mismo torneo
CREATE UNIQUE INDEX uq_torneo_equipo
    ON torneo_equipos (torneo_id, equipo_id);

-- =========================================
-- 6. CANCHAS
-- =========================================
CREATE TABLE canchas (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    ubicacion   VARCHAR(200),
    capacidad   INTEGER
);

-- =========================================
-- 7. PARTIDOS (calendario)
--    Soporta: grupos, marcador, estado, info para vivo
-- =========================================
CREATE TABLE partidos (
    id                   SERIAL PRIMARY KEY,
    torneo_id            INTEGER NOT NULL REFERENCES torneos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    grupo_id             INTEGER REFERENCES grupos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    cancha_id            INTEGER NOT NULL REFERENCES canchas(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    equipo_local_id      INTEGER NOT NULL REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    equipo_visitante_id  INTEGER NOT NULL REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    fecha_hora           TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    jornada              INTEGER,               -- Fecha 1, 2, 3, etc.
    estado               VARCHAR(20) DEFAULT 'programado',
        -- programado, en_juego, finalizado, suspendido

    goles_local          INTEGER DEFAULT 0,
    goles_visitante      INTEGER DEFAULT 0,
    minuto_actual        INTEGER,          -- para pantalla en vivo (ej. 65)
    es_destacado         BOOLEAN DEFAULT FALSE, -- resaltar partido en portada

    -- Restricción: no pueden ser el mismo equipo
    CONSTRAINT chk_equipos_distintos 
        CHECK (equipo_local_id <> equipo_visitante_id)
);

ALTER TABLE partidos
ADD COLUMN fase VARCHAR(30) DEFAULT 'grupos';

ALTER TABLE partidos
ALTER COLUMN cancha_id DROP NOT NULL;

-- 3. Índice por fase (para filtrar rápido por fase de grupos / finales, etc.)
CREATE INDEX IF NOT EXISTS idx_partidos_fase
    ON partidos (fase);
CREATE INDEX idx_partidos_torneo
    ON partidos (torneo_id);

CREATE INDEX idx_partidos_fecha
    ON partidos (fecha_hora);

CREATE INDEX idx_partidos_estado
    ON partidos (estado);

-- =========================================
-- 8. TRANSMISIONES (partidos en vivo)
--    Un partido puede tener una transmisión asociada
-- =========================================
CREATE TABLE transmisiones (
    id              SERIAL PRIMARY KEY,
    partido_id      INTEGER NOT NULL UNIQUE REFERENCES partidos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    plataforma      VARCHAR(50),           -- YouTube, Facebook, etc.
    url_publica     VARCHAR(255) NOT NULL, -- link que verá el ciudadano
    url_panel       VARCHAR(255),          -- opcional: link para el admin
    clave_stream    VARCHAR(100),          -- opcional: clave RTMP
    estado          VARCHAR(20) DEFAULT 'programada',
        -- programada, en_vivo, finalizada
    fecha_inicio    TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    fecha_fin       TIMESTAMP WITHOUT TIME ZONE
);

-- =========================================
-- 9. USUARIOS (Panel Admin / Operador)
-- =========================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             VARCHAR(20) NOT NULL DEFAULT 'OPERADOR'
        -- 'ADMIN', 'OPERADOR'
);

CREATE INDEX idx_usuarios_rol
    ON usuarios (rol);


-- =========================================
-- 10. PUBLICACIONES (Noticias)
-- =========================================
CREATE TABLE publicaciones (
    id          SERIAL PRIMARY KEY,
    titulo      VARCHAR(200) NOT NULL,
    categoria   VARCHAR(50),
    contenido   TEXT,
    imagen_url  VARCHAR(255),
    estado      VARCHAR(20) DEFAULT 'borrador', -- borrador, publicado, programado
    fecha_pub   TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- =========================================
-- 11. FORMACIONES (por equipo)
-- =========================================
CREATE TABLE formaciones (
    id              SERIAL PRIMARY KEY,
    equipo_id       INTEGER NOT NULL REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    nombre          VARCHAR(100) NOT NULL,  -- Ej: "4-3-3 vs Atlético"
    esquema         VARCHAR(20),            -- 4-4-2, 4-3-3, etc.
    datos_json      TEXT,                   -- posiciones en JSON (opcional)
    fecha_registro  TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

ALTER TABLE equipos
    ADD COLUMN logo_url VARCHAR(255);

CREATE TABLE posiciones (
    id SERIAL PRIMARY KEY,
    partido_id INT REFERENCES partidos(id) ON DELETE CASCADE,
    equipo_id INT REFERENCES equipos(id),
    goles_favor INT DEFAULT 0,
    goles_contra INT DEFAULT 0,
    puntos INT DEFAULT 0
);


ALTER TABLE partidos 
ALTER COLUMN equipo_local_id DROP NOT NULL;
ALTER TABLE partidos
ALTER COLUMN equipo_visitante_id DROP NOT NULL;

CREATE TABLE IF NOT EXISTS comentarios_partido (
    id SERIAL PRIMARY KEY,
    partido_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    texto TEXT NOT NULL,
    creado_en TIMESTAMP DEFAULT NOW()
);
