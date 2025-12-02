from conexionBD import Conexion
from argon2 import PasswordHasher

class Area:
    def __init__(self):
              #Instanciar la clase Password
        self.ph = PasswordHasher()

    # models/producto.py

    def ListarArea(self):
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = """
                SELECT id_area, nombre_area
                FROM areas
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()

            columnas = [desc[0] for desc in cursor.description]
            areas = [dict(zip(columnas, fila)) for fila in resultados]

            cursor.close()
            con.close()

            return areas
        except Exception as e:
            print("Error al listar areas:", e)
            return None

    def ExisteArea(self, nombre_area):
        """Verificar si un área ya existe por nombre"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "SELECT COUNT(*) FROM areas WHERE LOWER(nombre_area) = LOWER(%s)"
            cursor.execute(sql, (nombre_area,))
            count = cursor.fetchone()[0]
            
            cursor.close()
            con.close()
            
            return count > 0
        except Exception as e:
            print(f"Error al verificar existencia de área: {e}")
            return False

    def ExisteAreaById(self, id_area):
        """Verificar si un área existe por ID"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "SELECT COUNT(*) FROM areas WHERE id_area = %s"
            cursor.execute(sql, (id_area,))
            count = cursor.fetchone()[0]
            
            cursor.close()
            con.close()
            
            return count > 0
        except Exception as e:
            print(f"Error al verificar existencia de área por ID: {e}")
            return False

    def ExisteAreaExceptoId(self, nombre_area, id_area):
        """Verificar si existe otra área con el mismo nombre (excluyendo el ID actual)"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "SELECT COUNT(*) FROM areas WHERE LOWER(nombre_area) = LOWER(%s) AND id_area != %s"
            cursor.execute(sql, (nombre_area, id_area))
            count = cursor.fetchone()[0]
            
            cursor.close()
            con.close()
            
            return count > 0
        except Exception as e:
            print(f"Error al verificar existencia de área excepto ID: {e}")
            return False

    def CrearArea(self, nombre_area):
        """Crear una nueva área"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "INSERT INTO areas (nombre_area) VALUES (%s) RETURNING id_area"
            cursor.execute(sql, (nombre_area,))
            
            id_area = cursor.fetchone()[0]
            con.commit()
            cursor.close()
            con.close()

            return id_area
        except Exception as e:
            print(f"Error al crear área: {e}")
            return None

    def EditarArea(self, id_area, nombre_area):
        """Editar un área existente"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "UPDATE areas SET nombre_area = %s WHERE id_area = %s"
            cursor.execute(sql, (nombre_area, id_area))
            
            rowcount = cursor.rowcount
            con.commit()
            cursor.close()
            con.close()
            
            return rowcount > 0
        except Exception as e:
            print(f"Error al editar área: {e}")
            return False

    def EliminarArea(self, id_area):
        """Eliminar un área"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "DELETE FROM areas WHERE id_area = %s"
            cursor.execute(sql, (id_area,))
            
            rowcount = cursor.rowcount
            con.commit()
            cursor.close()
            con.close()
            
            return rowcount > 0
        except Exception as e:
            print(f"Error al eliminar área: {e}")
            return False

    def TieneSalidasAsociadas(self, id_area):
        """Verificar si el área tiene salidas asociadas"""
        try:
            con = Conexion().open
            cursor = con.cursor()

            sql = "SELECT COUNT(*) FROM salidas WHERE id_area = %s"
            cursor.execute(sql, (id_area,))
            count = cursor.fetchone()[0]
            
            cursor.close()
            con.close()
            
            return count > 0
        except Exception as e:
            print(f"Error al verificar salidas asociadas: {e}")
            return False