# models/canchas.py
from conexionBD import Conexion

class CanchasModel:

    def listar(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, ubicacion, capacidad
                FROM canchas
                ORDER BY nombre
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error CanchasModel.listar:", e)
            return []

    def crear(self, nombre, ubicacion=None, capacidad=None):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute(
                "INSERT INTO canchas (nombre, ubicacion, capacidad) VALUES (%s,%s,%s)",
                (nombre, ubicacion, capacidad)
            )
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error CanchasModel.crear:", e)
            return False

    def actualizar(self, id_, nombre, ubicacion=None, capacidad=None):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute(
                "UPDATE canchas SET nombre=%s, ubicacion=%s, capacidad=%s WHERE id=%s",
                (nombre, ubicacion, capacidad, id_)
            )
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error CanchasModel.actualizar:", e)
            return False

    def eliminar(self, id_):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("DELETE FROM canchas WHERE id=%s", (id_,))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error CanchasModel.eliminar:", e)
            return False
