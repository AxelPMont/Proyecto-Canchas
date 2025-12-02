# models/equipos.py
from conexionBD import Conexion

class EquiposModel:

    def listar_equipos(self):
        
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, categoria, logo_url
                FROM equipos
                ORDER BY id;
            """)
            rows = cur.fetchall()
            columnas = [desc[0] for desc in cur.description]
            equipos = [dict(zip(columnas, r)) for r in rows]
         
            cur.close()
            con.close()
      
            return equipos
        except Exception as e:
            print("❌ Error en listar_equipos:", e)
            return []

    def crear_equipo(self, nombre, categoria=None, logo_url=None):
       
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO equipos (nombre, categoria, logo_url)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (nombre, categoria, logo_url))
            nuevo_id = cur.fetchone()[0]
            con.commit()
            cur.close()
            con.close()

            return nuevo_id
        except Exception as e:
            print("❌ Error al crear equipo:", e)
            from traceback import print_exc
            print_exc()
            return None

    def eliminar_equipo(self, equipo_id):
        print(f"\n[EquiposModel.eliminar_equipo] Eliminando equipo_id={equipo_id}")
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
            con.commit()
            cur.close()
            con.close()
            print("[EquiposModel.eliminar_equipo] OK\n")
        except Exception as e:
            print("❌ Error al eliminar equipo:", e)


    def obtener_equipo(self, equipo_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, categoria, logo_url
                FROM equipos
                WHERE id = %s
            """, (equipo_id,))
            row = cur.fetchone()
            if not row:
                cur.close()
                con.close()
                return None
            cols = [c[0] for c in cur.description]
            equipo = dict(zip(cols, row))
            cur.close()
            con.close()
            return equipo
        except Exception as e:
            print("Error al obtener equipo:", e)
            return None

    def actualizar_equipo(self, equipo_id, nombre, categoria=None, logo_url=None):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                UPDATE equipos
                SET nombre = %s,
                    categoria = %s,
                    logo_url = %s
                WHERE id = %s
            """, (nombre, categoria, logo_url, equipo_id))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error al actualizar equipo:", e)
            return False

