from conexionBD import Conexion
from datetime import date, time, datetime

class ReservasModel:

    def _serializar(self, registro):
        resultado = {}
        for key, value in registro.items():
            if isinstance(value, (date, datetime)):
                resultado[key] = value.isoformat()
            elif isinstance(value, time):
                resultado[key] = value.strftime('%H:%M:%S')
            else:
                resultado[key] = value
        return resultado

    def listar_todas(self, fecha=None, cancha_id=None, estado=None):
        try:
            con = Conexion().open
            cur = con.cursor()

            query = """
                SELECT r.id, r.fecha, r.hora_inicio, r.hora_fin,
                       r.cliente_nombre, r.cliente_telefono, r.cliente_email,
                       r.estado, r.notas, r.precio, r.fecha_creacion,
                       c.id AS cancha_id, c.nombre AS cancha_nombre
                FROM reservas r
                JOIN canchas c ON r.cancha_id = c.id
                WHERE 1=1
            """
            params = []

            if fecha:
                query += " AND r.fecha = %s"
                params.append(fecha)

            if cancha_id:
                query += " AND r.cancha_id = %s"
                params.append(cancha_id)

            if estado:
                query += " AND r.estado = %s"
                params.append(estado)

            query += " ORDER BY r.fecha DESC, r.hora_inicio ASC"

            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [self._serializar(dict(zip(cols, r))) for r in rows]
        except Exception as e:
            print("Error ReservasModel.listar_todas:", e)
            return []

    def listar_por_cancha(self, cancha_id, fecha):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT id, hora_inicio, hora_fin, cliente_nombre, estado
                FROM reservas
                WHERE cancha_id = %s AND fecha = %s AND estado != 'cancelada'
                ORDER BY hora_inicio
            """, (cancha_id, fecha))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            con.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            print("Error ReservasModel.listar_por_cancha:", e)
            return []

    def obtener(self, reserva_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT r.id, r.fecha, r.hora_inicio, r.hora_fin,
                       r.cliente_nombre, r.cliente_telefono, r.cliente_email,
                       r.estado, r.notas, r.precio, r.fecha_creacion,
                       c.id AS cancha_id, c.nombre AS cancha_nombre
                FROM reservas r
                JOIN canchas c ON r.cancha_id = c.id
                WHERE r.id = %s
            """, (reserva_id,))
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
            print("Error ReservasModel.obtener:", e)
            return None

    def verificar_disponibilidad(self, cancha_id, fecha, hora_inicio, hora_fin, excluir_id=None):
        """
        Verifica si existe conflicto de horarios.
        Retorna True si está disponible, False si hay conflicto.
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            query = """
                SELECT COUNT(*) FROM reservas
                WHERE cancha_id = %s
                  AND fecha = %s
                  AND estado NOT IN ('cancelada')
                  AND (
                      (hora_inicio < %s AND hora_fin > %s)
                      OR (hora_inicio < %s AND hora_fin > %s)
                      OR (hora_inicio >= %s AND hora_fin <= %s)
                  )
            """
            params = [cancha_id, fecha, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin]

            if excluir_id:
                query += " AND id != %s"
                params.append(excluir_id)

            cur.execute(query, params)
            count = cur.fetchone()[0]
            cur.close()
            con.close()
            return count == 0
        except Exception as e:
            print("Error ReservasModel.verificar_disponibilidad:", e)
            return False

    def crear(self, cancha_id, fecha, hora_inicio, hora_fin, cliente_nombre,
              cliente_telefono, cliente_email=None, notas=None, precio=None):
        if not self.verificar_disponibilidad(cancha_id, fecha, hora_inicio, hora_fin):
            return None, "El horario seleccionado no está disponible"

        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO reservas
                (cancha_id, fecha, hora_inicio, hora_fin, cliente_nombre,
                 cliente_telefono, cliente_email, notas, precio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (cancha_id, fecha, hora_inicio, hora_fin, cliente_nombre,
                  cliente_telefono, cliente_email, notas, precio))
            reserva_id = cur.fetchone()[0]
            con.commit()
            cur.close()
            con.close()
            return reserva_id, None
        except Exception as e:
            print("Error ReservasModel.crear:", e)
            return None, str(e)

    def actualizar_estado(self, reserva_id, estado):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                UPDATE reservas SET estado = %s WHERE id = %s
            """, (estado, reserva_id))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error ReservasModel.actualizar_estado:", e)
            return False

    def eliminar(self, reserva_id):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error ReservasModel.eliminar:", e)
            return False

    def obtener_horarios_ocupados(self, cancha_id, fecha):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT hora_inicio, hora_fin
                FROM reservas
                WHERE cancha_id = %s AND fecha = %s AND estado NOT IN ('cancelada')
                ORDER BY hora_inicio
            """, (cancha_id, fecha))
            rows = cur.fetchall()
            cur.close()
            con.close()
            return [{"hora_inicio": r[0].strftime('%H:%M'), "hora_fin": r[1].strftime('%H:%M')} for r in rows]
        except Exception as e:
            print("Error ReservasModel.obtener_horarios_ocupados:", e)
            return []

    def contar_por_estado(self):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT estado, COUNT(*) as total
                FROM reservas
                GROUP BY estado
            """)
            rows = cur.fetchall()
            cur.close()
            con.close()
            return {r[0]: r[1] for r in rows}
        except Exception as e:
            print("Error ReservasModel.contar_por_estado:", e)
            return {}
