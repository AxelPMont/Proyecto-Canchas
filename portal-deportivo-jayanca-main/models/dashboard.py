# models/dashboard.py
from conexionBD import Conexion

class DashboardModel:
    """
    Modelo para obtener datos del panel de administración
    """

    def obtener_resumen(self):
        """
        Devuelve contadores para las tarjetas de arriba del dashboard:
        - torneos_activos
        - equipos_registrados
        - partidos_programados
        - transmisiones_hoy
        """
        datos = {
            "torneos_activos": 0,
            "equipos_registrados": 0,
            "partidos_programados": 0,
            "transmisiones_hoy": 0,
        }

        try:
            con = Conexion().open
            cur = con.cursor()

            # Torneos activos
            cur.execute("SELECT COUNT(*) FROM torneos WHERE estado = 'activo'")
            datos["torneos_activos"] = cur.fetchone()[0]

            # Equipos registrados
            cur.execute("SELECT COUNT(*) FROM equipos")
            datos["equipos_registrados"] = cur.fetchone()[0]

            # Partidos programados (futuros)
            cur.execute("""
                SELECT COUNT(*)
                FROM partidos
                WHERE fecha_hora >= NOW()
                  AND estado = 'programado'
            """)
            datos["partidos_programados"] = cur.fetchone()[0]

            # Transmisiones en vivo hoy
            cur.execute("""
                SELECT COUNT(*)
                FROM transmisiones t
                JOIN partidos p ON t.partido_id = p.id
                WHERE t.estado = 'en_vivo'
                  AND DATE(p.fecha_hora) = CURRENT_DATE
            """)
            datos["transmisiones_hoy"] = cur.fetchone()[0]

            cur.close()
            con.close()
        except Exception as e:
            print("Error en DashboardModel.obtener_resumen:", e)

        return datos

    def listar_proximos_partidos(self, limite=10):
        """
        Lista los próximos partidos para la tabla 'Próximos Partidos'
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            sql = """
                SELECT 
                    p.id,
                    p.fecha_hora,
                    p.jornada,
                    p.estado,
                    c.nombre AS cancha,
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante
                FROM partidos p
                JOIN canchas c ON p.cancha_id = c.id
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                WHERE p.fecha_hora >= NOW()
                ORDER BY p.fecha_hora ASC
                LIMIT %s
            """
            cur.execute(sql, (limite,))
            registros = cur.fetchall()
            columnas = [d[0] for d in cur.description]
            partidos = [dict(zip(columnas, row)) for row in registros]

            cur.close()
            con.close()
            return partidos

        except Exception as e:
            print("Error en DashboardModel.listar_proximos_partidos:", e)
            return []

    def listar_transmisiones_activas(self):
        """
        Lista transmisiones activas para la tabla 'Transmisiones Activas'
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            sql = """
                SELECT 
                    t.id,
                    t.plataforma,
                    t.estado,
                    t.url_publica,
                    p.id AS partido_id,
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante
                FROM transmisiones t
                JOIN partidos p       ON t.partido_id = p.id
                JOIN equipos  el      ON p.equipo_local_id = el.id
                JOIN equipos  ev      ON p.equipo_visitante_id = ev.id
                WHERE t.estado = 'en_vivo'
                ORDER BY p.fecha_hora DESC
            """
            cur.execute(sql)
            registros = cur.fetchall()
            columnas = [d[0] for d in cur.description]
            transmisiones = [dict(zip(columnas, row)) for row in registros]

            cur.close()
            con.close()
            return transmisiones

        except Exception as e:
            print("Error en DashboardModel.listar_transmisiones_activas:", e)
            return []
        
    def obtener_resumen(self):
        """
        Retorna diccionario con:
        - torneos_activos
        - equipos_registrados
        - partidos_programados
        - transmisiones_hoy
        """
        data = {
            "torneos_activos": 0,
            "equipos_registrados": 0,
            "partidos_programados": 0,
            "transmisiones_hoy": 0,
        }

        try:
            con = Conexion().open
            cur = con.cursor()

            # Torneos activos
            cur.execute("SELECT COUNT(*) FROM torneos WHERE estado = 'activo'")
            data["torneos_activos"] = cur.fetchone()[0]

            # Equipos registrados
            cur.execute("SELECT COUNT(*) FROM equipos")
            data["equipos_registrados"] = cur.fetchone()[0]

            # Partidos programados
            cur.execute("SELECT COUNT(*) FROM partidos WHERE estado = 'programado'")
            data["partidos_programados"] = cur.fetchone()[0]

            # Transmisiones hoy (partido hoy + transmisión en_vivo o programada)
            cur.execute("""
                SELECT COUNT(*)
                FROM transmisiones tr
                JOIN partidos p ON tr.partido_id = p.id
                WHERE DATE(p.fecha_hora) = CURRENT_DATE
                  AND tr.estado IN ('programada','en_vivo')
            """)
            data["transmisiones_hoy"] = cur.fetchone()[0]

            cur.close()
            con.close()
        except Exception as e:
            print("Error en DashboardModel.obtener_resumen:", e)

        return data

    def proximos_partidos(self, limite=10):
        """
        Lista de próximos partidos con info básica para la tabla del dashboard
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            sql = """
                SELECT 
                    p.id,
                    p.fecha_hora,
                    c.nombre AS cancha,
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante,
                    p.estado
                FROM partidos p
                JOIN canchas c ON p.cancha_id = c.id
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                WHERE p.fecha_hora >= NOW()
                ORDER BY p.fecha_hora ASC
                LIMIT %s
            """
            cur.execute(sql, (limite,))
            registros = cur.fetchall()
            columnas = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(columnas, r)) for r in registros]
        except Exception as e:
            print("Error en DashboardModel.proximos_partidos:", e)
            return []

    def transmisiones_activas(self):
        """
        Lista de transmisiones vinculadas a partidos
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            sql = """
                SELECT 
                    tr.id,
                    tr.plataforma,
                    tr.url_publica,
                    tr.estado,
                    p.id AS partido_id,          -- 👈 SOLO AÑADIMOS ESTA COLUMNA
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante
                FROM transmisiones tr
                JOIN partidos p ON tr.partido_id = p.id
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                ORDER BY p.fecha_hora DESC
            """
            cur.execute(sql)
            registros = cur.fetchall()
            columnas = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(columnas, r)) for r in registros]
        except Exception as e:
            print("Error en DashboardModel.transmisiones_activas:", e)
            return []
