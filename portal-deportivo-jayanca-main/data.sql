-- =========================================
-- INSERTS BASE
-- =========================================

-- 1. DIVISIONES
INSERT INTO divisiones (nombre)
VALUES 
('Primera'),
('Segunda'),
('Tercera');

-- 2. TORNEO
INSERT INTO torneos (nombre, temporada, division_id)
VALUES 
('Copa Distrital Jayanca', '2025', 1);

-- 3. GRUPOS
INSERT INTO grupos (torneo_id, nombre, codigo)
VALUES
(1, 'Grupo A', 'A'),
(1, 'Grupo B', 'B');

-- 4. EQUIPOS
INSERT INTO equipos (nombre) VALUES
('Sport Jayanca'),
('Real Jayanca'),
('Atlético Pueblo'),
('Santa Rosa FC'),
('Juventud Unión'),
('Los Pinos FC'),
('Talleres FC'),
('Independiente Norte');

-- 5. ASIGNAR EQUIPOS A TORNEO Y GRUPO
INSERT INTO torneo_equipos (torneo_id, equipo_id, grupo_id) VALUES
(1, 1, 1),  -- Sport Jayanca - Grupo A
(1, 2, 1),  -- Real Jayanca - Grupo A
(1, 3, 1),  -- Atlético Pueblo - Grupo A
(1, 4, 1),  -- Santa Rosa FC - Grupo A

(1, 5, 2),  -- Juventud Unión - Grupo B
(1, 6, 2),  -- Los Pinos FC - Grupo B
(1, 7, 2),  -- Talleres FC - Grupo B
(1, 8, 2);  -- Independiente Norte - Grupo B


-- 6. CANCHAS
INSERT INTO canchas (nombre, ubicacion, capacidad) VALUES
('Estadio Municipal de Jayanca', 'Av. Principal S/N', 3000),
('Campo San Martín', 'Sector San Martín', 1200);


-- =========================================
-- PARTIDOS DEL TORNEO
-- =========================================

-- GRUPO A - JORNADA 1
INSERT INTO partidos (
    torneo_id, grupo_id, cancha_id,
    equipo_local_id, equipo_visitante_id,
    fecha_hora, jornada, estado
) VALUES
(1, 1, 1, 1, 2, '2025-02-15 15:30:00', 1, 'programado'), -- Sport vs Real
(1, 1, 2, 3, 4, '2025-02-15 17:30:00', 1, 'programado'); -- Atletico vs Santa Rosa


-- GRUPO A – JORNADA 2
INSERT INTO partidos (
    torneo_id, grupo_id, cancha_id,
    equipo_local_id, equipo_visitante_id,
    fecha_hora, jornada, estado
) VALUES
(1, 1, 1, 1, 3, '2025-02-22 15:30:00', 2, 'programado'), -- Sport vs Atletico
(1, 1, 2, 2, 4, '2025-02-22 17:30:00', 2, 'programado'); -- Real vs Santa Rosa


-- GRUPO B – JORNADA 1
INSERT INTO partidos (
    torneo_id, grupo_id, cancha_id,
    equipo_local_id, equipo_visitante_id,
    fecha_hora, jornada, estado
) VALUES
(1, 2, 1, 5, 6, '2025-02-16 16:00:00', 1, 'programado'), -- Juventud vs Los Pinos
(1, 2, 2, 7, 8, '2025-02-16 18:00:00', 1, 'programado'); -- Talleres vs Independiente


-- GRUPO B – JORNADA 2
INSERT INTO partidos (
    torneo_id, grupo_id, cancha_id,
    equipo_local_id, equipo_visitante_id,
    fecha_hora, jornada, estado
) VALUES
(1, 2, 1, 5, 7, '2025-02-23 16:00:00', 2, 'programado'), -- Juventud vs Talleres
(1, 2, 2, 6, 8, '2025-02-23 18:00:00', 2, 'programado'); -- Pinos vs Independiente


-- =========================================
-- TRANSMISIONES
-- =========================================

-- Partido 1 será destacado en portada y tendrá transmisión
UPDATE partidos
SET es_destacado = TRUE
WHERE id = 1;

INSERT INTO transmisiones (
    partido_id, plataforma, url_publica, estado
) VALUES
(1, 'YouTube', 'https://youtube.com/live/ejemplo123', 'programada');

-- Partido 3 también tendrá transmisión
INSERT INTO transmisiones (
    partido_id, plataforma, url_publica, estado
) VALUES
(3, 'Facebook', 'https://facebook.com/live/xyz', 'programada');
