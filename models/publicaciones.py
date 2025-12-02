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
                RETURNING id;
            """, (titulo, categoria, contenido, estado, imagen_url))
            pub_id = cur.fetchone()[0]
            con.commit()
            cur.close()
            con.close()
            return pub_id
        except Exception as e:
            print("Error PublicacionesModel.crear:", e)
            return None

    def obtener(self, pub_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, titulo, categoria, contenido, estado, imagen_url, fecha_pub
                FROM publicaciones
                WHERE id = %s
            """, (pub_id,))
            row = cur.fetchone()
            if not row:
                cur.close()
                con.close()
                return None
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return dict(zip(cols, row))
        except Exception as e:
            print("Error PublicacionesModel.obtener:", e)
            return None

    def eliminar(self, pub_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("DELETE FROM publicaciones WHERE id = %s", (pub_id,))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error PublicacionesModel.eliminar:", e)
            return False

    def actualizar(self, pub_id, titulo, categoria, contenido, estado, imagen_url=None):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                UPDATE publicaciones
                SET titulo=%s, categoria=%s, contenido=%s, estado=%s, imagen_url=%s
                WHERE id=%s
            """, (titulo, categoria, contenido, estado, imagen_url, pub_id))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error PublicacionesModel.actualizar:", e)
            return False

    def listar_publicadas(self, limite=10):
        """Listar solo publicaciones con estado='publicado' para la página principal"""
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, titulo, categoria, contenido, estado, imagen_url, fecha_pub
                FROM publicaciones
                WHERE estado = 'publicado'
                ORDER BY fecha_pub DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error PublicacionesModel.listar_publicadas:", e)
            return []

    def listar_por_categoria(self, categoria, limite=10):
        """Listar publicaciones por categoría, solo las publicadas"""
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, titulo, categoria, contenido, estado, imagen_url, fecha_pub
                FROM publicaciones
                WHERE estado = 'publicado' AND categoria = %s
                ORDER BY fecha_pub DESC
                LIMIT %s
            """, (categoria, limite))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error PublicacionesModel.listar_por_categoria:", e)
            return []