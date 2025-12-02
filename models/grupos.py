# models/grupos.py
from conexionBD import Conexion

class GruposModel:

    def listar_por_torneo(self, torneo_id: int):
        """
        Devuelve una lista de grupos con sus equipos para el torneo dado.
        Ejemplo de salida:
        [
          {
            "id": 1,
            "nombre": "Grupo A",
            "codigo": "A",
            "equipos": [
                {"id": 10, "nombre": "Equipo 1"},
                {"id": 11, "nombre": "Equipo 2"},
                ...
            ]
          },
          ...
        ]
        """
        if not torneo_id:
            return []

        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                SELECT 
                    g.id,
                    g.nombre,
                    g.codigo,
                    e.id   AS equipo_id,
                    e.nombre AS equipo_nombre
                FROM grupos g
                LEFT JOIN torneo_equipos te ON te.grupo_id = g.id
                LEFT JOIN equipos e        ON e.id = te.equipo_id
                WHERE g.torneo_id = %s
                ORDER BY g.codigo, e.nombre;
            """, (torneo_id,))

            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            data = [dict(zip(cols, r)) for r in rows]

            cur.close()
            con.close()

            grupos_dict = {}
            for row in data:
                gid = row["id"]
                if gid not in grupos_dict:
                    grupos_dict[gid] = {
                        "id": gid,
                        "nombre": row["nombre"],
                        "codigo": row["codigo"],
                        "equipos": []
                    }

                if row["equipo_id"] is not None:
                    grupos_dict[gid]["equipos"].append({
                        "id": row["equipo_id"],
                        "nombre": row["equipo_nombre"]
                    })

            return list(grupos_dict.values())

        except Exception as e:
            print("Error al listar grupos por torneo:", e)
            return []

    def crear(self, torneo_id, nombre, codigo):
        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO grupos (torneo_id, nombre, codigo)
                VALUES (%s,%s,%s)
            """, (torneo_id, nombre, codigo))
            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error GruposModel.crear:", e)
            return False

    # Generación automática (ejemplo simple)
    def generar_grupos(self, torneo_id, num_grupos, equipos_por_grupo):
        """
        Lógica básica:
        - Crea grupos A, B, C...
        - (Luego se puede ampliar para asignar equipos)
        """
        try:
            con = Conexion().open
            cur = con.cursor()

            # Crear grupos A,B,C...
            for i in range(num_grupos):
                codigo = chr(ord('A') + i)
                nombre = f"Grupo {codigo}"
                cur.execute("""
                    INSERT INTO grupos (torneo_id, nombre, codigo)
                    VALUES (%s,%s,%s)
                """, (torneo_id, nombre, codigo))

            con.commit()
            cur.close()
            con.close()
            return True
        except Exception as e:
            print("Error GruposModel.generar_grupos:", e)
            return False

    def generar_grupos_aleatorios(self, torneo_id, equipos_ids, equipos_por_grupo=4):
        """
        torneo_id: id del torneo donde se armarán los grupos
        equipos_ids: lista de IDs de equipos (ej. 16 equipos)
        equipos_por_grupo: normalmente 4
        """
        if not equipos_ids:
            print("No se recibieron equipos para generar grupos")
            return False

        # Mezclar aleatoriamente
        random.shuffle(equipos_ids)

        # Verificar múltiplo de equipos_por_grupo
        if len(equipos_ids) % equipos_por_grupo != 0:
            print("La cantidad de equipos no es múltiplo de equipos_por_grupo")
            return False

        try:
            con = Conexion().open
            cur = con.cursor()

            # 1. Crear grupos (A, B, C, D, ... según cantidad)
            num_grupos = len(equipos_ids) // equipos_por_grupo
            codigos = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

            grupos_creados = []  # (grupo_id, codigo)

            for i in range(num_grupos):
                codigo = codigos[i]
                nombre = f"Grupo {codigo}"
                cur.execute("""
                    INSERT INTO grupos (torneo_id, nombre, codigo)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (torneo_id, nombre, codigo))
                grupo_id = cur.fetchone()[0]
                grupos_creados.append((grupo_id, codigo))

            # 2. Asignar equipos a grupos creando/actualizando torneo_equipos
            idx_equipo = 0
            for grupo_id, codigo in grupos_creados:
                for _ in range(equipos_por_grupo):
                    equipo_id = equipos_ids[idx_equipo]
                    idx_equipo += 1

                    # Si ya existe el registro en torneo_equipos, solo actualizar grupo_id;
                    # si no existe, lo creamos.
                    cur.execute("""
                        SELECT id FROM torneo_equipos
                        WHERE torneo_id = %s AND equipo_id = %s
                    """, (torneo_id, equipo_id))
                    row = cur.fetchone()

                    if row:
                        cur.execute("""
                            UPDATE torneo_equipos
                            SET grupo_id = %s
                            WHERE id = %s
                        """, (grupo_id, row[0]))
                    else:
                        cur.execute("""
                            INSERT INTO torneo_equipos (torneo_id, equipo_id, grupo_id)
                            VALUES (%s, %s, %s)
                        """, (torneo_id, equipo_id, grupo_id))

            con.commit()
            cur.close()
            con.close()
            return True

        except Exception as e:
            print("Error al generar grupos aleatorios:", e)
            return False