from conexionBD import Conexion

class PublicacionesModel:

    def listar(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, titulo, categoria, estado, fecha_pub
                FROM publicaciones
                ORDER BY fecha_pub DESC
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error PublicacionesModel.listar:", e)
            return []

    def crear(self, titulo, categoria, contenido, estado, imagen_url=None):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO publicaciones (titulo, categoria, contenido, estado, imagen_url)
                VALUES (%s,%s,%s,%s,%s)
            """, (titulo, categoria, contenido, estado, imagen_url))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error PublicacionesModel.crear:", e)
            return False
