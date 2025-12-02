# routes/admin.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from traceback import print_exc
from datetime import datetime, date, time, timedelta

from werkzeug.utils import secure_filename
import os
import random
import string
import datetime
from models.dashboard import DashboardModel
from models.equipos import EquiposModel
from models.canchas import CanchasModel
from models.torneos import TorneosModel
from models.transmisiones import TransmisionesModel
from models.partidos import PartidosModel
from models.grupos import GruposModel
from models.publicaciones import PublicacionesModel
from models.reservas import ReservasModel
from conexionBD import Conexion
from flask import abort, render_template, request, redirect, url_for, flash

ws_admin = Blueprint("ws_admin", __name__, url_prefix="/admin")

dashboard_model = DashboardModel()
equipos_model = EquiposModel()
canchas_model = CanchasModel()
torneos_model = TorneosModel()
transmisiones_model = TransmisionesModel()
partidos_model = PartidosModel()
grupos_model = GruposModel()
publicaciones_model = PublicacionesModel()
reservas_model = ReservasModel()

# =======================
# PANEL PRINCIPAL
# =======================
@ws_admin.route("/", methods=["GET"])
def panel_principal():
    resumen = dashboard_model.obtener_resumen()
    proximos = dashboard_model.proximos_partidos(limite=5)
    transmisiones = dashboard_model.transmisiones_activas()
    partidos = partidos_model.listar_todos_para_transmision()

    equipos = equipos_model.listar_equipos()
    canchas = canchas_model.listar()
    torneos = torneos_model.listar()

    torneo_id_activo = None
    grupos = []
    partidos_calendario = []
    tabla_posiciones = {}
    fase_grupos_completa = False

    llaves_cuartos = []
    semifinales = []
    final = {}

    if torneos:
        torneo_id_activo = torneos[0]["id"]
        grupos = grupos_model.listar_por_torneo(torneo_id_activo)
        tabla_posiciones = {g["codigo"]: [] for g in grupos}

        try:
            con = Conexion().open
            cur = con.cursor()

            # ==================================================
            # 1) LISTAR PARTIDOS FASE DE GRUPOS
            # ==================================================
            cur.execute("""
                SELECT 
                    p.id,
                    p.fecha_hora,
                    p.jornada,
                    g.codigo AS grupo_codigo,
                    el.nombre AS equipo_local,
                    ev.nombre AS equipo_visitante,
                    c.nombre AS cancha,
                    p.estado,
                    COALESCE(p.goles_local,0),
                    COALESCE(p.goles_visitante,0)
                FROM partidos p
                LEFT JOIN grupos g   ON g.id = p.grupo_id
                LEFT JOIN equipos el ON el.id = p.equipo_local_id
                LEFT JOIN equipos ev ON ev.id = p.equipo_visitante_id
                LEFT JOIN canchas c  ON c.id = p.cancha_id
                WHERE p.torneo_id = %s
                  AND p.fase = 'grupos'
                ORDER BY p.fecha_hora ASC;
            """, (torneo_id_activo,))

            rows = cur.fetchall()

            total_partidos = len(rows)
            total_finalizados = 0

            for r in rows:
                partidos_calendario.append({
                    "id": r[0],
                    "fecha_hora": r[1],
                    "jornada": r[2],
                    "grupo_codigo": r[3],
                    "equipo_local": r[4],
                    "equipo_visitante": r[5],
                    "cancha": r[6],
                    "estado": r[7],
                    "goles_local": r[8],
                    "goles_visitante": r[9],
                })
                if r[7] == "finalizado":
                    total_finalizados += 1

            if total_partidos > 0 and total_finalizados == total_partidos:
                fase_grupos_completa = True

            # ==================================================
            # 2) TABLA DE POSICIONES
            # ==================================================
            cur.execute("""
                SELECT 
                    g.codigo AS grupo,
                    e.nombre AS equipo,
                    COALESCE(SUM(
                        CASE 
                            WHEN p.equipo_local_id = e.id THEN p.goles_local
                            WHEN p.equipo_visitante_id = e.id THEN p.goles_visitante
                        END
                    ),0) AS gf,
                    COALESCE(SUM(
                        CASE 
                            WHEN p.equipo_local_id = e.id THEN p.goles_visitante
                            WHEN p.equipo_visitante_id = e.id THEN p.goles_local
                        END
                    ),0) AS gc,
                    COALESCE(SUM(
                        CASE
                            WHEN p.estado='finalizado' AND p.goles_local = p.goles_visitante THEN 1
                            WHEN p.estado='finalizado' AND p.equipo_local_id = e.id AND p.goles_local > p.goles_visitante THEN 3
                            WHEN p.estado='finalizado' AND p.equipo_visitante_id = e.id AND p.goles_visitante > p.goles_local THEN 3
                            ELSE 0
                        END
                    ),0) AS puntos
                FROM grupos g
                JOIN torneo_equipos te ON te.grupo_id = g.id
                JOIN equipos e        ON e.id = te.equipo_id
                LEFT JOIN partidos p  ON p.grupo_id = g.id
                    AND (p.equipo_local_id = e.id OR p.equipo_visitante_id = e.id)
                WHERE g.torneo_id = %s
                GROUP BY g.codigo, e.nombre
                ORDER BY g.codigo, puntos DESC;
            """, (torneo_id_activo,))

            pos_rows = cur.fetchall()

            for grupo_codigo, equipo, gf, gc, puntos in pos_rows:
                tabla_posiciones[grupo_codigo].append({
                    "equipo": equipo,
                    "gf": gf,
                    "gc": gc,
                    "dg": gf - gc,
                    "puntos": puntos,
                })

            # ==================================================
            # 3) CUARTOS DE FINAL
            # ==================================================
            cur.execute("""
                SELECT 
                    p.id,
                    p.equipo_local_id,
                    p.equipo_visitante_id,
                    el.nombre,
                    ev.nombre,
                    p.fecha_hora
                FROM partidos p
                JOIN equipos el ON el.id = p.equipo_local_id
                JOIN equipos ev ON ev.id = p.equipo_visitante_id
                WHERE p.torneo_id = %s
                  AND p.fase = 'cuartos'
                ORDER BY p.fecha_hora ASC, p.id ASC;
            """, (torneo_id_activo,))

            cuartos_rows = cur.fetchall()

            seed_map = {
                0: ("1° A", "2° B", "1° A vs 2° B"),
                1: ("1° B", "2° A", "1° B vs 2° A"),
                2: ("1° C", "2° D", "1° C vs 2° D"),
                3: ("1° D", "2° C", "1° D vs 2° C"),
            }

            llaves_cuartos = []

            for idx, r in enumerate(cuartos_rows):
                seed_local, seed_visitante, desc = seed_map.get(idx, ("", "", ""))
                llaves_cuartos.append({
                    "id": r[0],
                    "local_id": r[1],
                    "visitante_id": r[2],
                    "local": r[3],
                    "visitante": r[4],
                    "fecha_hora": r[5],
                    "seed_local": seed_local,
                    "seed_visitante": seed_visitante,
                    "descripcion": desc,
                })

            # ==================================================
            # 4) SEMIFINALES
            # ==================================================
            cur.execute("""
                SELECT 
                    p.id,
                    el.nombre,
                    ev.nombre,
                    p.equipo_local_id,
                    p.equipo_visitante_id
                FROM partidos p
                LEFT JOIN equipos el ON el.id = p.equipo_local_id
                LEFT JOIN equipos ev ON ev.id = p.equipo_visitante_id
                WHERE p.torneo_id = %s
                  AND p.fase = 'semifinal'
                ORDER BY p.id ASC;
            """, (torneo_id_activo,))

            sf_rows = cur.fetchall()

            for r in sf_rows:
                semifinales.append({
                    "id": r[0],
                    "local": r[1],
                    "visitante": r[2],
                    "local_id": r[3],
                    "visitante_id": r[4],
                })

            while len(semifinales) < 2:
                semifinales.append({
                    "id": 0,
                    "local": None,
                    "visitante": None,
                    "local_id": None,
                    "visitante_id": None,
                })

            # ==================================================
            # 5) FINAL
            # ==================================================
            cur.execute("""
                SELECT 
                    p.id,
                    el.nombre,
                    ev.nombre,
                    p.equipo_local_id,
                    p.equipo_visitante_id
                FROM partidos p
                LEFT JOIN equipos el ON el.id = p.equipo_local_id
                LEFT JOIN equipos ev ON ev.id = p.equipo_visitante_id
                WHERE p.torneo_id = %s
                  AND p.fase = 'final'
                LIMIT 1;
            """, (torneo_id_activo,))

            r = cur.fetchone()

            if r:
                final = {
                    "id": r[0],
                    "local": r[1],
                    "visitante": r[2],
                    "local_id": r[3],
                    "visitante_id": r[4],
                }
            else:
                final = {
                    "id": 0,
                    "local": None,
                    "visitante": None,
                    "local_id": None,
                    "visitante_id": None,
                }

            cur.close()
            con.close()

        except Exception as e:
            print("Error obteniendo datos:", e)
            print_exc()

    publicaciones = publicaciones_model.listar()

    return render_template(
        "dashboard.html",
        resumen=resumen,
        proximos_partidos=proximos,
        transmisiones_activas=transmisiones,
        equipos=equipos,
        canchas=canchas,
        torneos=torneos,
        torneo_id_activo=torneo_id_activo,
        grupos=grupos,
        partidos_calendario=partidos_calendario,
        tabla_posiciones=tabla_posiciones,
        fase_grupos_completa=fase_grupos_completa,
        llaves_cuartos=llaves_cuartos,
        semifinales=semifinales,
        final=final,
        partidos=partidos,
        publicaciones=publicaciones,
    )



@ws_admin.route("/grupos/terminar_fase", methods=["POST"])
def terminar_fase_grupos():
    """
    Genera automáticamente:
      - Cuartos de final
      - Semifinales
      - Final
      - Enlaces entre fases (siguiente_partido_id, slot_siguiente)
    TODO completamente automático.
    """
    from datetime import timedelta

    print("\n====== INICIANDO GENERACIÓN AUTOMÁTICA DE LLAVES ======")

    torneo_id = request.form.get("torneo_id", type=int)
    print(f"→ torneo_id recibido: {torneo_id}")

    if not torneo_id:
        flash("No se recibió el torneo.", "danger")
        return redirect(url_for("ws_admin.panel_principal"))

    try:
        con = Conexion().open
        cur = con.cursor()

        # ======================================================
        # 1. Verificar si ya existen cuartos
        # ======================================================
        cur.execute("""
            SELECT COUNT(*) 
            FROM partidos 
            WHERE torneo_id=%s AND fase='cuartos';
        """, (torneo_id,))
        if cur.fetchone()[0] > 0:
            flash("Los cuartos ya están generados.", "warning")
            return redirect(url_for("ws_admin.panel_principal") + "#bracket")

        # ======================================================
        # 2. Obtener tabla de posiciones completa
        # ======================================================
        cur.execute("""
            SELECT *
            FROM (
                SELECT 
                    g.codigo AS grupo,
                    e.id     AS equipo_id,
                    e.nombre AS equipo,
                    COALESCE(SUM(
                        CASE 
                            WHEN p.equipo_local_id = e.id THEN p.goles_local
                            WHEN p.equipo_visitante_id = e.id THEN p.goles_visitante
                        END
                    ),0) AS gf,
                    COALESCE(SUM(
                        CASE 
                            WHEN p.equipo_local_id = e.id THEN p.goles_visitante
                            WHEN p.equipo_visitante_id = e.id THEN p.goles_local
                        END
                    ),0) AS gc,
                    COALESCE(SUM(
                        CASE
                            WHEN p.estado='finalizado' AND p.goles_local = p.goles_visitante THEN 1
                            WHEN p.estado='finalizado' AND p.equipo_local_id = e.id AND p.goles_local > p.goles_visitante THEN 3
                            WHEN p.estado='finalizado' AND p.equipo_visitante_id = e.id AND p.goles_visitante > p.goles_local THEN 3
                            ELSE 0
                        END
                    ),0) AS puntos
                FROM grupos g
                JOIN torneo_equipos te ON te.grupo_id = g.id
                JOIN equipos e        ON e.id = te.equipo_id
                LEFT JOIN partidos p  ON p.grupo_id = g.id
                    AND (p.equipo_local_id = e.id OR p.equipo_visitante_id = e.id)
                WHERE g.torneo_id = %s
                GROUP BY g.codigo, e.id, e.nombre
            ) tabla
            ORDER BY grupo ASC, puntos DESC, (gf - gc) DESC, gf DESC;
        """, (torneo_id,))
        posiciones = cur.fetchall()

        # Agrupar equipos por grupo
        grupos = {}
        for row in posiciones:
            grupos.setdefault(row[0], []).append(row)

        # Top 2 por grupo
        clasificados = []
        for g, lista in grupos.items():
            clasificados.append((g, lista[0][1], "1"))  # 1° puesto
            clasificados.append((g, lista[1][1], "2"))  # 2° puesto

        def get_equipo(grupo, pos):
            for gg, eid, pp in clasificados:
                if gg == grupo and pp == pos:
                    return eid
            return None

        # ======================================================
        # 3. Fechas automáticas
        # ======================================================
        cur.execute("""
            SELECT MAX(fecha_hora)
            FROM partidos
            WHERE torneo_id=%s AND fase='grupos';
        """, (torneo_id,))
        last_date = cur.fetchone()[0]

        fecha_cuartos = last_date + timedelta(days=1)
        fecha_semis   = fecha_cuartos + timedelta(days=1)
        fecha_final   = fecha_semis + timedelta(days=1)

        # ======================================================
        # 4. Crear semifinales y final
        # ======================================================
        cur.execute("""
            INSERT INTO partidos(torneo_id, fase, fecha_hora, estado)
            VALUES (%s,'semifinal',%s,'programado')
            RETURNING id;
        """, (torneo_id, fecha_semis))
        sf1_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO partidos(torneo_id, fase, fecha_hora, estado)
            VALUES (%s,'semifinal',%s,'programado')
            RETURNING id;
        """, (torneo_id, fecha_semis))
        sf2_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO partidos(torneo_id, fase, fecha_hora, estado)
            VALUES (%s,'final',%s,'programado')
            RETURNING id;
        """, (torneo_id, fecha_final))
        final_id = cur.fetchone()[0]

        # ENLACE SEMIS → FINAL
        cur.execute("""
            UPDATE partidos SET siguiente_partido_id=%s, slot_siguiente=1 WHERE id=%s
        """, (final_id, sf1_id))
        cur.execute("""
            UPDATE partidos SET siguiente_partido_id=%s, slot_siguiente=2 WHERE id=%s
        """, (final_id, sf2_id))

        # ======================================================
        # 5. Crear CUARTOS con enlaces a semifinales correctos
        # ======================================================
        llaves = [
            ("A","1","B","2", sf1_id, 1),  # QF1 → SF1 (local)
            ("B","1","A","2", sf1_id, 2),  # QF2 → SF1 (visitante)
            ("C","1","D","2", sf2_id, 1),  # QF3 → SF2 (local)
            ("D","1","C","2", sf2_id, 2),  # QF4 → SF2 (visitante)
        ]

        for g1, p1, g2, p2, next_id, slot in llaves:
            e1 = get_equipo(g1, p1)
            e2 = get_equipo(g2, p2)

            cur.execute("""
                INSERT INTO partidos(
                    torneo_id, fase, equipo_local_id, equipo_visitante_id,
                    fecha_hora, estado, siguiente_partido_id, slot_siguiente
                )
                VALUES (%s,'cuartos',%s,%s,%s,'programado',%s,%s)
            """, (torneo_id, e1, e2, fecha_cuartos, next_id, slot))

        con.commit()
        cur.close()
        con.close()

        flash("Llaves generadas correctamente.", "success")

    except Exception as e:
        print("❌ Error en terminar_fase_grupos:", e)
        flash("Error generando eliminatorias.", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#bracket")

# ====================================
#   REGISTRAR GANADOR DEL BRACKET
# ====================================
@ws_admin.route("/bracket/ganador", methods=["POST"])
def registrar_ganador_bracket():
    """
    Registra ganador y lo pasa al partido siguiente según slot_siguiente.
    slot 1 = local
    slot 2 = visitante
    """
    data = request.get_json() or {}
    partido_id = data.get("partido_id")
    ganador_id = data.get("ganador_id")

    print("\n=== registrar_ganador_bracket ===")
    print("partido_id:", partido_id, "ganador_id:", ganador_id)

    if not partido_id or not ganador_id:
        return {"ok": False, "error": "Datos incompletos"}, 400

    try:
        con = Conexion().open
        cur = con.cursor()

        # Obtener el partido y su siguiente enlace
        cur.execute("""
            UPDATE partidos
            SET ganador_id = %s, estado = 'finalizado'
            WHERE id = %s
            RETURNING siguiente_partido_id, slot_siguiente;
        """, (ganador_id, partido_id))

        row = cur.fetchone()
        siguiente_id, slot = row

        print("siguiente_partido_id:", siguiente_id, "slot_siguiente:", slot)

        # Si tiene partido siguiente, asignarlo
        if siguiente_id:
            if slot == 1:  
                cur.execute("""
                    UPDATE partidos
                    SET equipo_local_id = %s
                    WHERE id = %s;
                """, (ganador_id, siguiente_id))

            elif slot == 2:
                cur.execute("""
                    UPDATE partidos
                    SET equipo_visitante_id = %s
                    WHERE id = %s;
                """, (ganador_id, siguiente_id))

            else:
                print(f"⚠ slot inválido: {slot}")

        con.commit()
        cur.close()
        con.close()

        print("✔ Ganador registrado y propagado correctamente")
        return {"ok": True}

    except Exception as e:
        print("❌ Error en registrar_ganador_bracket:", e)
        from traceback import print_exc
        print_exc()
        return {"ok": False, "error": "Error interno"}, 500


# ====================================
#   GUARDAR RESULTADO DE PARTIDO
# ====================================
@ws_admin.route("/partidos/resultado", methods=["POST"])
def guardar_resultado():
    partido_id = request.form.get("partido_id", type=int)
    goles_local = request.form.get("goles_local", type=int)
    goles_visitante = request.form.get("goles_visitante", type=int)

    try:
        con = Conexion().open
        cur = con.cursor()

        cur.execute("""
            UPDATE partidos
            SET goles_local=%s,
                goles_visitante=%s,
                estado='finalizado'
            WHERE id=%s
        """, (goles_local, goles_visitante, partido_id))

        con.commit()
        cur.close()
        con.close()

        flash("Resultado guardado correctamente.", "success")

    except Exception as e:
        print("Error guardando resultado:", e)
        flash("Error guardando resultado", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#groups")

# =======================
# CRUD EQUIPOS
# =======================
@ws_admin.route("/equipos/crear", methods=["POST"])
def crear_equipo():
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    logo = request.files.get("logo")

    logo_url = None

    if logo and logo.filename:
        filename = secure_filename(logo.filename)
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        if not os.path.isdir(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        save_path = os.path.join(upload_folder, filename)
        logo.save(save_path)
        # ruta pública para usar en <img src="...">
        logo_url = f"/static/img/{filename}"

    if nombre:
        equipos_model.crear_equipo(nombre, categoria, logo_url)

    return redirect(url_for("ws_admin.panel_principal") + "#teams")


@ws_admin.route("/equipos/<int:equipo_id>/eliminar", methods=["POST"])
def eliminar_equipo(equipo_id):
    equipos_model.eliminar_equipo(equipo_id)
    return redirect(url_for("ws_admin.panel_principal") + "#teams")


# ==========================
# GENERAR GRUPOS CON TODOS LOS EQUIPOS
# ==========================
@ws_admin.route("/grupos/generar", methods=["POST"])
def generar_grupos():
    from conexionBD import Conexion
    import string
    import random

    torneo_id = request.form.get("torneo_id", type=int)
    num_grupos = request.form.get("num_grupos", type=int) or 4
    equipos_por_grupo = request.form.get("equipos_por_grupo", type=int) or 4

    if not torneo_id:
        flash("Debes seleccionar un torneo.", "warning")
        return redirect(url_for("ws_admin.panel_principal") + "#groups")

    try:
        con = Conexion().open
        cur = con.cursor()

        # =========================
        # 1. Tomar TODOS los equipos registrados
        # =========================
        cur.execute("""
            SELECT id, nombre
            FROM equipos
            ORDER BY nombre
        """)
        equipos = cur.fetchall()

        if not equipos:
            flash("No hay equipos registrados en la tabla 'equipos'.", "warning")
            cur.close()
            con.close()
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        equipo_ids = [row[0] for row in equipos]

        # (Opcional) capacidad total
        capacidad_total = num_grupos * equipos_por_grupo
        if len(equipo_ids) < capacidad_total:
            # No es error, solo aviso: algunos grupos quedarán vacíos/parciales
            print(f"Solo hay {len(equipo_ids)} equipos para una capacidad de {capacidad_total}")

        # =========================
        # 2. Limpiar asignaciones anteriores de ese torneo
        # =========================
        cur.execute("DELETE FROM torneo_equipos WHERE torneo_id = %s", (torneo_id,))
        cur.execute("DELETE FROM grupos WHERE torneo_id = %s", (torneo_id,))

        # =========================
        # 3. Crear grupos A, B, C...
        # =========================
        grupos_ids = []
        for i in range(num_grupos):
            codigo = string.ascii_uppercase[i]  # A, B, C, ...
            nombre_grupo = f"Grupo {codigo}"

            cur.execute("""
                INSERT INTO grupos (torneo_id, nombre, codigo)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (torneo_id, nombre_grupo, codigo))

            grupo_id = cur.fetchone()[0]
            grupos_ids.append(grupo_id)

        print("Grupos creados:", grupos_ids)

        # =========================
        # 4. Mezclar equipos aleatoriamente
        # =========================
        random.shuffle(equipo_ids)

        # =========================
        # 5. Insertar en torneo_equipos y asignar grupo
        # =========================
        for idx, equipo_id in enumerate(equipo_ids):
            grupo_index = idx // equipos_por_grupo
            if grupo_index >= len(grupos_ids):
                # si hay más equipos que capacidad, se ignoran de momento
                break
            grupo_id = grupos_ids[grupo_index]

            cur.execute("""
                INSERT INTO torneo_equipos (torneo_id, equipo_id, grupo_id)
                VALUES (%s, %s, %s)
            """, (torneo_id, equipo_id, grupo_id))

        con.commit()
        cur.close()
        con.close()

        flash("Grupos generados y guardados correctamente.", "success")
        print("✔ Grupos generados para torneo", torneo_id)

    except Exception as e:
        print("Error al generar grupos:", e)
        flash("Ocurrió un error al generar los grupos.", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#groups")

# ==========================
# GENERAR CALENDARIO DE PARTIDOS DE GRUPOS
#  - Usa los grupos ya generados
#  - Hace todos contra todos dentro de cada grupo
#  - Reparte los partidos en días (3 por día por defecto)
#  - Inserta en la tabla partidos
# ==========================
# ==========================
# GENERAR CALENDARIO FASE DE GRUPOS
# ==========================
@ws_admin.route("/grupos/generar_calendario", methods=["POST"])
def generar_calendario_grupos():
    print("\n================ GENERAR CALENDARIO GRUPOS ================")
    try:
        torneo_id = request.form.get("torneo_id", type=int)
        fecha_inicio_str = request.form.get("fecha_inicio")
        print("[1] torneo_id recibido:", torneo_id)
        print("[2] fecha_inicio_str:", fecha_inicio_str)

        if not torneo_id:
            flash("No se recibió el torneo para generar el calendario.", "warning")
            print("[ERROR] torneo_id vacío")
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        # --------------------------------------------
        # 1. Parsear fecha de inicio (HTML = YYYY-MM-DD)
        # --------------------------------------------
        try:
            fecha_base = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            print("[3] fecha_base parseada:", fecha_base)
        except Exception as e:
            print("[ERROR] al parsear la fecha:", e)
            print_exc()
            flash("Fecha de inicio inválida. Selecciona una fecha válida.", "danger")
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        # Mover la fecha al próximo sábado o domingo
        while fecha_base.weekday() not in (5, 6):  # 5=sábado, 6=domingo
            fecha_base += timedelta(days=1)
        print("[4] primera fecha de juego (sab/dom):", fecha_base)

        # --------------------------------------------
        # 2. Horarios fijos del día (3 partidos de 2h)
        # --------------------------------------------
        HORAS_DIA = [
            time(10, 0),  # 10:00 - 12:00
            time(12, 0),  # 12:00 - 14:00
            time(14, 0),  # 14:00 - 16:00
        ]
        print("[5] HORAS_DIA:", HORAS_DIA)

        # --------------------------------------------
        # 3. Conexión y datos base
        # --------------------------------------------
        print("[6] Abriendo conexión a BD...")
        con = Conexion().open
        cur = con.cursor()
        print("[7] Conexión abierta OK")

        # 3.1 Grupos del torneo
        cur.execute(
            """
            SELECT id, codigo, nombre
            FROM grupos
            WHERE torneo_id = %s
            ORDER BY codigo
            """,
            (torneo_id,),
        )
        grupos = cur.fetchall()
        print("[8] Grupos encontrados:", grupos)

        if not grupos:
            flash("No hay grupos generados para este torneo.", "warning")
            print("[WARN] Sin grupos")
            cur.close()
            con.close()
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        # 3.2 Canchas
        cur.execute("SELECT id, nombre FROM canchas ORDER BY id;")
        canchas_rows = cur.fetchall()
        canchas = [row[0] for row in canchas_rows]
        print("[9] Canchas encontradas:", canchas_rows)

        if not canchas:
            flash("No hay canchas registradas para programar partidos.", "warning")
            print("[WARN] Sin canchas")
            cur.close()
            con.close()
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        # --------------------------------------------
        # 4. Borrar partidos anteriores del torneo
        # --------------------------------------------
        print("[10] Eliminando partidos anteriores del torneo:", torneo_id)
        cur.execute(
            "DELETE FROM partidos WHERE torneo_id = %s;",
            (torneo_id,),
        )

        # --------------------------------------------
        # 5. Generar todos los partidos (round robin)
        # --------------------------------------------
        partidos_a_insertar = []

        for (grupo_id, codigo, nombre_grupo) in grupos:
            print(f"[11] Procesando grupo_id={grupo_id}, codigo={codigo}, nombre={nombre_grupo}")

            cur.execute(
                """
                SELECT e.id, e.nombre
                FROM torneo_equipos te
                JOIN equipos e ON e.id = te.equipo_id
                WHERE te.torneo_id = %s AND te.grupo_id = %s
                ORDER BY e.nombre
                """,
                (torneo_id, grupo_id),
            )
            equipos_rows = cur.fetchall()
            equipos = [row[0] for row in equipos_rows]
            print(f"[12] Equipos en grupo {grupo_id}:", equipos_rows)

            n = len(equipos)
            if n < 2:
                print(f"[WARN] Grupo {grupo_id} tiene menos de 2 equipos, se salta.")
                continue

            # Algoritmo round-robin
            lista = equipos[:]
            if len(lista) % 2 != 0:
                lista.append(None)

            mitad = len(lista) // 2
            num_jornadas = len(lista) - 1
            print(f"[13] Grupo {grupo_id} -> num_jornadas={num_jornadas}, mitad={mitad}")

            for jornada in range(1, num_jornadas + 1):
                for i in range(mitad):
                    eq_local = lista[i]
                    eq_visita = lista[-(i + 1)]
                    if eq_local and eq_visita:
                        partidos_a_insertar.append(
                            {
                                "torneo_id": torneo_id,
                                "grupo_id": grupo_id,
                                "equipo_local_id": eq_local,
                                "equipo_visitante_id": eq_visita,
                                "jornada": jornada,
                            }
                        )
                # rotar para la siguiente jornada
                lista = [lista[0]] + [lista[-1]] + lista[1:-1]

        print("[14] TOTAL partidos_a_insertar:", len(partidos_a_insertar))

        if not partidos_a_insertar:
            flash("No se generaron partidos. Verifica que los grupos tengan equipos.", "warning")
            print("[ERROR] partidos_a_insertar está vacío")
            cur.close()
            con.close()
            return redirect(url_for("ws_admin.panel_principal") + "#groups")

        # --------------------------------------------
        # 6. Asignar fechas, horarios y canchas
        # --------------------------------------------
        fecha_actual = fecha_base
        contador_slots_dia = 0
        idx_cancha = 0
        insertados = 0

        for partido in partidos_a_insertar:

            if contador_slots_dia >= 3:
                fecha_actual += timedelta(days=1)
                while fecha_actual.weekday() not in (5, 6):
                    fecha_actual += timedelta(days=1)
                contador_slots_dia = 0

            hora = HORAS_DIA[contador_slots_dia]
            fecha_hora = datetime.datetime.combine(fecha_actual, hora)

            cancha_id = canchas[idx_cancha % len(canchas)]
            idx_cancha += 1

            print(
                f"[15] INSERT partido -> grupo_id={partido['grupo_id']}, "
                f"cancha_id={cancha_id}, fecha_hora={fecha_hora}, "
                f"local={partido['equipo_local_id']}, visita={partido['equipo_visitante_id']}, "
                f"jornada={partido['jornada']}"
            )

            cur.execute(
                """
                INSERT INTO partidos (
                    torneo_id,
                    grupo_id,
                    cancha_id,
                    equipo_local_id,
                    equipo_visitante_id,
                    fecha_hora,
                    jornada,
                    estado,
                    fase
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,'programado','grupos')
                """,
                (
                    partido["torneo_id"],
                    partido["grupo_id"],
                    cancha_id,
                    partido["equipo_local_id"],
                    partido["equipo_visitante_id"],
                    fecha_hora,
                    partido["jornada"],
                ),
            )

            contador_slots_dia += 1
            insertados += 1

        con.commit()
        cur.close()
        con.close()
        print("[16] PARTIDOS INSERTADOS EN BD:", insertados)
        flash("Calendario de fase de grupos generado correctamente.", "success")

    except Exception as e:
        print("===== ERROR EN generar_calendario_grupos =====")
        print(e)
        print_exc()
        flash("Ocurrió un error al generar el calendario.", "danger")

    print("=============== FIN generar_calendario_grupos ===============\n")
    return redirect(url_for("ws_admin.panel_principal") + "#groups")
# =======================
# CRUD CANCHAS
# =======================
@ws_admin.route("/canchas/crear", methods=["POST"])
def crear_cancha():
    nombre = request.form.get("nombre")
    ubicacion = request.form.get("ubicacion")
    capacidad = request.form.get("capacidad")
    capacidad = int(capacidad) if capacidad else None
    if nombre:
        canchas_model.crear(nombre, ubicacion, capacidad)
    return redirect(url_for("ws_admin.panel_principal") + "#fields")


@ws_admin.route("/canchas/<int:cancha_id>/eliminar", methods=["POST"])
def eliminar_cancha(cancha_id):
    canchas_model.eliminar(cancha_id)
    return redirect(url_for("ws_admin.panel_principal") + "#fields")


# =======================
# CREAR PARTIDO
# =======================
@ws_admin.route("/partidos/crear", methods=["POST"])
def crear_partido():
    torneo_id = request.form.get("torneo_id")
    cancha_id = request.form.get("cancha_id")
    equipo_local_id = request.form.get("equipo_local_id")
    equipo_visitante_id = request.form.get("equipo_visitante_id")
    fecha_hora = request.form.get("fecha_hora")
    estado = request.form.get("estado", "programado")

    try:
        con = Conexion().open
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO partidos
            (torneo_id, cancha_id, equipo_local_id, equipo_visitante_id, fecha_hora, estado)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,
            (torneo_id, cancha_id, equipo_local_id, equipo_visitante_id, fecha_hora, estado),
        )
        con.commit()
        cur.close()
        con.close()
    except Exception as e:
        print("Error crear_partido:", e)

    return redirect(url_for("ws_admin.panel_principal") + "#matches")


# =======================
# GUARDAR TRANSMISIÓN
# =======================
@ws_admin.route("/transmisiones/guardar", methods=["POST"])
def guardar_transmision():
    partido_id = request.form.get("partido_id")
    plataforma = request.form.get("plataforma")
    url_publica = request.form.get("url_publica")
    estado = request.form.get("estado_transmision")

    if partido_id and url_publica:
        transmisiones_model.guardar_o_actualizar(
            partido_id=int(partido_id),
            plataforma=plataforma,
            url_publica=url_publica,
            estado=estado,
        )

    return redirect(url_for("ws_admin.panel_principal") + "#transmissions")





@ws_admin.route("/eliminatorias/avanzar", methods=["POST"])
def avanzar_eliminatoria():
    data = request.json
    partido_id = data.get("partido_id")
    ganador_id = data.get("equipo_id")

    try:
        con = Conexion().open
        cur = con.cursor()

        # 1) Guardar ganador en este partido
        cur.execute("""
            UPDATE partidos
            SET ganador_id=%s, estado='finalizado'
            WHERE id=%s
        """, (ganador_id, partido_id))

        # 2) Buscar a qué partido sigue
        cur.execute("""
            SELECT siguiente_partido_id, slot_siguiente
            FROM partidos
            WHERE id=%s
        """, (partido_id,))
        next_data = cur.fetchone()

        if next_data and next_data[0]:
            next_match_id = next_data[0]
            slot = next_data[1]  # 0=local, 1=visitante

            if slot == 0:
                cur.execute("""
                    UPDATE partidos
                    SET equipo_local_id=%s
                    WHERE id=%s
                """, (ganador_id, next_match_id))
            else:
                cur.execute("""
                    UPDATE partidos
                    SET equipo_visitante_id=%s
                    WHERE id=%s
                """, (ganador_id, next_match_id))

        con.commit()
        cur.close()
        con.close()

        return {"ok": True}

    except Exception as e:
        print("ERROR avanzar:", e)
        return {"ok": False, "error": str(e)}, 500
    
# ============================
# ADMINISTRAR TRANSMISIÓN (OVERLAY)
# ============================
@ws_admin.route("/transmision/<int:partido_id>/admin", methods=["GET"])
def transmision_admin(partido_id):
    partido = partidos_model.obtener_partido(partido_id)
    if not partido:
        abort(404)

    # Obtener canal de Twitch (si aplica)
    plataforma = getattr(partido, "plataforma", None)
    if plataforma is None and isinstance(partido, dict):
        plataforma = partido.get("plataforma")

    url_publica = getattr(partido, "url_publica", None)
    if url_publica is None and isinstance(partido, dict):
        url_publica = partido.get("url_publica")

    twitch_channel = None
    if plataforma == "Twitch" and url_publica:
        url = url_publica
        for prefix in ("https://www.twitch.tv/", "https://twitch.tv/"):
            if url.startswith(prefix):
                url = url[len(prefix):]
        twitch_channel = url.split("/")[0]

    return render_template(
        "transmision_admin.html",
        partido=partido,
        twitch_channel=twitch_channel
    )

# =======================
# CRUD PUBLICACIONES
# =======================
@ws_admin.route("/publicaciones/crear", methods=["POST"])
def crear_publicacion():
    """Crear una nueva publicación (noticia) desde el admin"""
    try:
        titulo = request.form.get("titulo")
        categoria = request.form.get("categoria")
        contenido = request.form.get("contenido")
        estado = request.form.get("estado", "borrador")
        imagen = request.files.get("imagen")

        if not titulo or not categoria or not contenido:
            flash("Título, categoría y contenido son obligatorios", "danger")
            return redirect(url_for("ws_admin.panel_principal") + "#publications")

        imagen_url = None

        # Procesar imagen si se envía
        if imagen and imagen.filename:
            filename = secure_filename(imagen.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            if not os.path.isdir(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, filename)
            imagen.save(save_path)
            imagen_url = f"/static/img/{filename}"

        # Crear publicación
        pub_id = publicaciones_model.crear(titulo, categoria, contenido, estado, imagen_url)

        if pub_id:
            flash("Publicación creada correctamente", "success")
        else:
            flash("Error al crear la publicación", "danger")

    except Exception as e:
        print("Error crear_publicacion:", e)
        flash("Error al crear la publicación", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#publications")


@ws_admin.route("/publicaciones/<int:pub_id>/eliminar", methods=["POST"])
def eliminar_publicacion(pub_id):
    """Eliminar una publicación"""
    try:
        if publicaciones_model.eliminar(pub_id):
            flash("Publicación eliminada correctamente", "success")
        else:
            flash("Error al eliminar la publicación", "danger")
    except Exception as e:
        print("Error eliminar_publicacion:", e)
        flash("Error al eliminar la publicación", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#publications")


@ws_admin.route("/publicaciones/<int:pub_id>/editar", methods=["POST"])
def editar_publicacion(pub_id):
    """Editar una publicación existente"""
    try:
        titulo = request.form.get("titulo")
        categoria = request.form.get("categoria")
        contenido = request.form.get("contenido")
        estado = request.form.get("estado", "borrador")
        imagen = request.files.get("imagen")

        if not titulo or not categoria or not contenido:
            flash("Título, categoría y contenido son obligatorios", "danger")
            return redirect(url_for("ws_admin.panel_principal") + "#publications")

        # Obtener publicación actual para conservar imagen si no se sube una nueva
        pub = publicaciones_model.obtener(pub_id)
        imagen_url = pub.get("imagen_url") if pub else None

        # Procesar nueva imagen si se envía
        if imagen and imagen.filename:
            filename = secure_filename(imagen.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            if not os.path.isdir(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, filename)
            imagen.save(save_path)
            imagen_url = f"/static/img/{filename}"

        # Actualizar publicación
        if publicaciones_model.actualizar(pub_id, titulo, categoria, contenido, estado, imagen_url):
            flash("Publicación actualizada correctamente", "success")
        else:
            flash("Error al actualizar la publicación", "danger")

    except Exception as e:
        print("Error editar_publicacion:", e)
        flash("Error al actualizar la publicación", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#publications")


@ws_admin.route("/publicaciones/listar", methods=["GET"])
def listar_publicaciones():
    """API: listar todas las publicaciones en JSON"""
    publicaciones = publicaciones_model.listar()
    return {"publicaciones": publicaciones}, 200


# =======================
# RESERVAS
# =======================
@ws_admin.route("/reservas/listar", methods=["GET"])
def listar_reservas():
    fecha = request.args.get("fecha")
    cancha_id = request.args.get("cancha_id", type=int)
    estado = request.args.get("estado")

    reservas = reservas_model.listar_todas(fecha, cancha_id, estado)
    return {"reservas": reservas}, 200


@ws_admin.route("/reservas/estado", methods=["POST"])
def cambiar_estado_reserva():
    reserva_id = request.form.get("reserva_id", type=int)
    nuevo_estado = request.form.get("estado")

    if not reserva_id or not nuevo_estado:
        flash("Datos incompletos", "danger")
        return redirect(url_for("ws_admin.panel_principal") + "#reservas")

    if nuevo_estado not in ["pendiente", "confirmada", "cancelada", "completada"]:
        flash("Estado no válido", "danger")
        return redirect(url_for("ws_admin.panel_principal") + "#reservas")

    if reservas_model.actualizar_estado(reserva_id, nuevo_estado):
        flash(f"Reserva #{reserva_id} actualizada a '{nuevo_estado}'", "success")
    else:
        flash("Error al actualizar la reserva", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#reservas")


@ws_admin.route("/reservas/eliminar/<int:reserva_id>", methods=["POST"])
def eliminar_reserva(reserva_id):
    if reservas_model.eliminar(reserva_id):
        flash(f"Reserva #{reserva_id} eliminada", "success")
    else:
        flash("Error al eliminar la reserva", "danger")

    return redirect(url_for("ws_admin.panel_principal") + "#reservas")