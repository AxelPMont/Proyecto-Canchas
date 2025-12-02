# models/torneos.py
from conexionBD import Conexion

class TorneosModel:

    def listar(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT t.id, t.nombre, t.temporada, t.estado,
                       d.id AS division_id, d.nombre AS division
                FROM torneos t
                JOIN divisiones d ON t.division_id = d.id
                ORDER BY t.id DESC
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error TorneosModel.listar:", e)
            return []

    def listar_divisiones(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM divisiones ORDER BY id")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error TorneosModel.listar_divisiones:", e)
            return []

    def crear(self, nombre, temporada, division_id, estado='activo'):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO torneos (nombre, temporada, division_id, estado)
                VALUES (%s,%s,%s,%s)
            """, (nombre, temporada, division_id, estado))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error TorneosModel.crear:", e)
            return False
