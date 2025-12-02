from conexionBD import Conexion

class FormacionesModel:

    def listar_por_equipo(self, equipo_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, esquema, datos_json, fecha_registro
                FROM formaciones
                WHERE equipo_id = %s
                ORDER BY fecha_registro DESC
            """, (equipo_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error FormacionesModel.listar_por_equipo:", e)
            return []
