# models/partidos.py
from conexionBD import Conexion

class PartidosModel:

    def listar_partidos(self, filtro_tiempo="proximos", division_id=None):
        try:
            con = Conexion().open
            cursor = con.cursor()

            query = """
                SELECT 
                    p.id,
                    p.fecha_hora,
                    p.jornada,
                    p.estado,
                    p.goles_local,
                    p.goles_visitante,
                    t.nombre      AS torneo,
                    d.nombre      AS division,
                    g.codigo      AS grupo,
                    c.nombre      AS cancha,
                    el.nombre     AS equipo_local,
                    ev.nombre     AS equipo_visitante,
                    tr.plataforma,
                    tr.url_publica,
                    tr.estado     AS estado_transmision,
                    p.es_destacado
                FROM partidos p
                JOIN torneos    t  ON p.torneo_id = t.id
                JOIN divisiones d  ON t.division_id = d.id
                LEFT JOIN grupos g ON p.grupo_id = g.id
                JOIN canchas   c   ON p.cancha_id = c.id
                JOIN equipos   el  ON p.equipo_local_id = el.id
                JOIN equipos   ev  ON p.equipo_visitante_id = ev.id
                LEFT JOIN transmisiones tr ON tr.partido_id = p.id
                WHERE 1=1
            """

            params = []

            # ----------------------------
            # FILTRO DE TIEMPO
            # ----------------------------
            if filtro_tiempo == "proximos":
                query += " AND p.fecha_hora >= NOW()"
                order = " ORDER BY p.fecha_hora ASC"

            elif filtro_tiempo == "anteriores":
                query += " AND p.fecha_hora < NOW()"
                order = " ORDER BY p.fecha_hora DESC"

            else:  # todos
                order = " ORDER BY p.fecha_hora DESC"

            # ----------------------------
            # FILTRO POR DIVISIÓN
            # ----------------------------
            if division_id:
                query += " AND d.id = %s"
                params.append(division_id)

            query += order

            cursor.execute(query, params)
            registros = cursor.fetchall()

            columnas = [desc[0] for desc in cursor.description]
            partidos = [dict(zip(columnas, row)) for row in registros]

            cursor.close()
            con.close()

            return partidos

        except Exception as e:
            print("Error al listar partidos:", e)
            return []
        
    def obtener_partido(self, partido_id: int):
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = """
                SELECT 
                    p.id,
                    p.fecha_hora,
                    p.jornada,
                    p.estado,
                    p.goles_local,
                    p.goles_visitante,
                    t.nombre      AS torneo,
                    d.nombre      AS division,
                    g.codigo      AS grupo,
                    c.nombre      AS cancha,
                    el.nombre     AS equipo_local,
                    ev.nombre     AS equipo_visitante,
                    tr.plataforma,
                    tr.url_publica,
                    tr.estado     AS estado_transmision
                FROM partidos p
                JOIN torneos    t  ON p.torneo_id = t.id
                JOIN divisiones d  ON t.division_id = d.id
                LEFT JOIN grupos g ON p.grupo_id = g.id
                JOIN canchas   c   ON p.cancha_id = c.id
                JOIN equipos   el  ON p.equipo_local_id = el.id
                JOIN equipos   ev  ON p.equipo_visitante_id = ev.id
                LEFT JOIN transmisiones tr ON tr.partido_id = p.id
                WHERE p.id = %s
            """
            cursor.execute(sql, (partido_id,))
            row = cursor.fetchone()

            if not row:
                cursor.close()
                con.close()
                return None

            columnas = [desc[0] for desc in cursor.description]
            partido = dict(zip(columnas, row))

            cursor.close()
            con.close()
            return partido

        except Exception as e:
            print("Error al obtener partido:", e)
            return None
        
    def listar_todos_para_transmision(self):
        """
        Lista TODOS los partidos (grupos, cuartos, semifinal, final)
        ordenados por fase y fecha, para el panel de transmisiones.
        """
        try:
            con = Conexion().open
            cursor = con.cursor()

            cursor.execute("""
                SELECT 
                    p.id,
                    p.fase,
                    p.fecha_hora,
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante
                FROM partidos p
                JOIN equipos el ON el.id = p.equipo_local_id
                JOIN equipos ev ON ev.id = p.equipo_visitante_id
                ORDER BY 
                    CASE 
                        WHEN p.fase='grupos' THEN 1
                        WHEN p.fase='cuartos' THEN 2
                        WHEN p.fase='semifinal' THEN 3
                        WHEN p.fase='final' THEN 4
                        ELSE 5
                    END,
                    p.fecha_hora ASC;
            """)

            rows = cursor.fetchall()
            partidos = [
                {
                    "id": r[0],
                    "fase": r[1],
                    "fecha_hora": r[2],
                    "equipo_local": r[3],
                    "equipo_visitante": r[4]
                }
                for r in rows
            ]

            cursor.close()
            con.close()
            return partidos

        except Exception as e:
            print("Error en listar_todos_para_transmision:", e)
            return []

