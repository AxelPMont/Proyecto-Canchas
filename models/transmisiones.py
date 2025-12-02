# models/transmisiones.py
from conexionBD import Conexion

class TransmisionesModel:

    def listar(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT tr.id, tr.plataforma, tr.url_publica, tr.estado,
                       p.id AS partido_id,
                       el.nombre AS equipo_local,
                       ev.nombre AS equipo_visitante
                FROM transmisiones tr
                JOIN partidos p ON tr.partido_id = p.id
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                ORDER BY p.fecha_hora DESC
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error TransmisionesModel.listar:", e)
            return []

    def guardar_o_actualizar(self, partido_id, plataforma, url_publica, estado):
        """
        Si ya existe transmisión para ese partido: se actualiza.
        Si no, se crea.
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            cur.execute("SELECT id FROM transmisiones WHERE partido_id = %s", (partido_id,))
            row = cur.fetchone()

            if row:
                cur.execute("""
                    UPDATE transmisiones
                    SET plataforma=%s, url_publica=%s, estado=%s
                    WHERE partido_id=%s
                """, (plataforma, url_publica, estado, partido_id))
            else:
                cur.execute("""
                    INSERT INTO transmisiones (partido_id, plataforma, url_publica, estado)
                    VALUES (%s,%s,%s,%s)
                """, (partido_id, plataforma, url_publica, estado))

            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error TransmisionesModel.guardar_o_actualizar:", e)
            return False

    def eliminar(self, id_):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("DELETE FROM transmisiones WHERE id=%s", (id_,))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error TransmisionesModel.eliminar:", e)
            return False
