# routes/partidos.py
from flask import Blueprint, request, render_template, abort, jsonify
from models.partidos import PartidosModel
from conexionBD import Conexion
import re

ws_partidos = Blueprint('ws_partidos', __name__)
modelo = PartidosModel()


# ============================
#   HELPER: AÑADIR LOGOS A UN PARTIDO
# ============================
def adjuntar_logos_a_partido(partido: dict) -> dict:
    """
    Recibe un dict partido (de modelo.obtener_partido)
    y le agrega:
      - partido["logo_local_url"]
      - partido["logo_visitante_url"]
    buscando en la tabla equipos por nombre.
    """
    if not partido:
        return partido

    nombre_local = partido.get("equipo_local")
    nombre_visitante = partido.get("equipo_visitante")

    if not nombre_local and not nombre_visitante:
        return partido

    con = Conexion().open
    cur = con.cursor()

    # Buscamos los logos por nombre de equipo
    cur.execute("""
        SELECT nombre, logo_url
        FROM equipos
        WHERE nombre IN (%s, %s)
    """, (nombre_local, nombre_visitante))

    filas = cur.fetchall()
    cur.close()
    con.close()

    logos = {nombre: logo for (nombre, logo) in filas}

    partido["logo_local_url"] = logos.get(nombre_local)
    partido["logo_visitante_url"] = logos.get(nombre_visitante)

    return partido


# ============================
#   LISTADO PÚBLICO DE PARTIDOS
# ============================
@ws_partidos.route("/partidos", methods=["GET"])
def pantalla_publica_partidos():

    filtro_tiempo = request.args.get("tiempo", "proximos")
    division_id = request.args.get("division_id")

    partidos = modelo.listar_partidos(filtro_tiempo, division_id)

    # Obtener divisiones para los filtros
    con = Conexion().open
    cur = con.cursor()
    cur.execute("SELECT id, nombre FROM divisiones ORDER BY id")
    divisiones = cur.fetchall()
    columnas = [desc[0] for desc in cur.description]
    divisiones = [dict(zip(columnas, row)) for row in divisiones]
    cur.close()
    con.close()

    return render_template(
        "partidos_publico.html",
        partidos=partidos,
        divisiones=divisiones,
        filtro_tiempo=filtro_tiempo,
        division_id=division_id
    )


# ============================
#   VISTA PÚBLICA DE TRANSMISIÓN
# ============================
@ws_partidos.route("/transmision/<int:partido_id>", methods=["GET"])
def ver_transmision(partido_id):
    # Usamos tu modelo original
    partido = modelo.obtener_partido(partido_id)
    if not partido:
        return abort(404)

    # Le agregamos los logos
    partido = adjuntar_logos_a_partido(partido)

    # parent para Twitch
    twitch_parent = request.host.split(":")[0]

    return render_template(
        "transmision.html",
        partido=partido,
        twitch_parent=twitch_parent
    )


# ============================
#   PANEL DE CONTROL (CONTROL ROOM)
# ============================
@ws_partidos.route("/admin/transmision/<int:partido_id>", methods=["GET"])
def panel_transmision(partido_id):
    """
    Panel de control para el partido:
    marcador + eventos + vista previa (usa control_room.html).
    """
    partido = modelo.obtener_partido(partido_id)
    if not partido:
        return abort(404)

    partido = adjuntar_logos_a_partido(partido)

    # Extraer canal de Twitch si toca
    twitch_channel = None
    if partido.get("plataforma") == "Twitch" and partido.get("url_publica"):
        m = re.search(r"twitch.tv/([^/?]+)", partido["url_publica"])
        if m:
            twitch_channel = m.group(1)

    return render_template(
        "control_room.html",   # o el nombre de tu template del panel
        partido=partido,
        twitch_channel=twitch_channel
    )


# ============================
#   API: ACTUALIZAR MARCADOR
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/marcador", methods=["POST"])
def api_actualizar_marcador(partido_id):
    if not request.is_json:
        return jsonify({"ok": False, "error": "JSON requerido"}), 400

    data = request.get_json() or {}
    goles_local = int(data.get("goles_local", 0))
    goles_visitante = int(data.get("goles_visitante", 0))
    texto_estado = data.get("texto_estado") or ""
    mostrar_overlay = bool(data.get("mostrar_overlay", True))   # 👈 NUEVO

    con = Conexion().open
    cur = con.cursor()

    cur.execute("""
        UPDATE partidos
        SET goles_local = %s,
            goles_visitante = %s,
            texto_estado = %s,
            mostrar_overlay = %s
        WHERE id = %s
    """, (goles_local, goles_visitante, texto_estado, mostrar_overlay, partido_id))

    con.commit()
    cur.close()
    con.close()

    return jsonify({
        "ok": True,
        "partido_id": partido_id,
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "texto_estado": texto_estado,
        "mostrar_overlay": mostrar_overlay
    })


# ============================
#   API: OBTENER ESTADO ACTUAL
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/estado", methods=["GET"])
def api_estado_partido(partido_id):
    con = Conexion().open
    cur = con.cursor()
    cur.execute("""
        SELECT id, estado, goles_local, goles_visitante, texto_estado, mostrar_overlay
        FROM partidos
        WHERE id = %s
    """, (partido_id,))
    row = cur.fetchone()
    cur.close()
    con.close()

    if not row:
        return jsonify({"ok": False, "error": "Partido no encontrado"}), 404

    (
        _id, estado,
        goles_local, goles_visitante,
        texto_estado, mostrar_overlay
    ) = row

    return jsonify({
        "ok": True,
        "partido_id": _id,
        "estado": estado,
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "texto_estado": texto_estado,
        "mostrar_overlay": bool(mostrar_overlay)
    })


# ============================
#   API: REGISTRAR EVENTO
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/evento", methods=["POST"])
def api_registrar_evento(partido_id):
    """
    Registra un evento del partido (gol, tarjeta, cambio, etc.)
    y lo deja disponible para que la pantalla pública lo pueda leer
    y animar.
    """
    if not request.is_json:
        return jsonify(ok=False, error="Se requiere JSON"), 400

    data = request.get_json() or {}

    tipo        = data.get("tipo")          # gol, penal, offside, amarilla, roja, cambio, otro
    equipo      = data.get("equipo")        # local / visitante
    jugador1    = data.get("jugador1")
    jugador2    = data.get("jugador2")
    minuto      = data.get("minuto")
    texto_libre = data.get("texto_libre")

    # Logs en backend para depurar
    print("=== API REGISTRAR EVENTO ===")
    print("Partido:", partido_id)
    print("Payload recibido:", data)

    try:
        con = Conexion().open
        cur = con.cursor()

        cur.execute("""
            INSERT INTO eventos_partido
            (partido_id, tipo, equipo, jugador1, jugador2, minuto, texto_libre)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (partido_id, tipo, equipo, jugador1, jugador2, minuto, texto_libre))

        evento_id = cur.fetchone()[0]
        con.commit()
        cur.close()
        con.close()

        return jsonify(
            ok=True,
            evento_id=evento_id,
            partido_id=partido_id,
            tipo=tipo,
            equipo=equipo,
            jugador1=jugador1,
            jugador2=jugador2,
            minuto=minuto,
            texto_libre=texto_libre
        )

    except Exception as e:
        print("❌ Error guardando evento:", e)
        try:
            con.rollback()
        except:
            pass
        return jsonify(ok=False, error=str(e)), 500


## ============================
#   API: ÚLTIMO EVENTO + DATOS PARTIDO
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/ultimo_evento", methods=["GET"])
def api_ultimo_evento(partido_id):
    """
    Devuelve:
      - último evento registrado (si existe)
      - info del partido (marcador, estado, logos, etc.)
    """
   

    # ========= 1) INFO DEL PARTIDO (incluye logos) =========
    partido = None
    base_info = {
        "partido_id": partido_id,
        "equipo_local": None,
        "equipo_visitante": None,
        "marcador_local": 0,
        "marcador_visitante": 0,
        "estado": None,
        "estado_transmision": None,
        "logo_local_url": None,
        "logo_visitante_url": None,
    }

    try:
        partido = modelo.obtener_partido(partido_id)
      
        if partido:
            base_info.update({
                "equipo_local": partido.get("equipo_local"),
                "equipo_visitante": partido.get("equipo_visitante"),
                "marcador_local": partido.get("goles_local") or 0,
                "marcador_visitante": partido.get("goles_visitante") or 0,
                "estado": partido.get("estado"),
                "estado_transmision": partido.get("estado_transmision"),
                "logo_local_url": partido.get("logo_local_url"),
                "logo_visitante_url": partido.get("logo_visitante_url"),
            })
        else:
            print("[api_ultimo_evento] ⚠ No se encontró partido en obtener_partido()")

    except Exception as e:
        print("❌ Error obteniendo partido en api_ultimo_evento:", e)

    # ========= 2) ÚLTIMO EVENTO =========
    try:
        con = Conexion().open
        cur = con.cursor()

        
        cur.execute("""
            SELECT id,
                   tipo,
                   equipo,
                   jugador1,
                   jugador2,
                   minuto,
                   texto_libre,
                   creado_en
            FROM eventos_partido
            WHERE partido_id = %s
            ORDER BY creado_en DESC, id DESC
            LIMIT 1
        """, (partido_id,))

        row = cur.fetchone()
        cur.close()
        con.close()

        if not row:
            # 🔴 IMPORTANTE: igual devolvemos base_info para que el overlay
            # tenga logos y marcador aunque no haya eventos todavía
            resp = {
                "ok": False,
                "mensaje": "Sin eventos aún",
                "evento": None,
            }
            resp.update(base_info)
            return jsonify(resp)

        evento = {
            "evento_id":   row[0],
            "tipo":        row[1],
            "equipo":      row[2],
            "jugador1":    row[3],
            "jugador2":    row[4],
            "minuto":      row[5],
            "texto_libre": row[6],
            "creado_en":   row[7].isoformat() if row[7] else None
        }

        resp = {
            "ok": True,
            "evento": evento,
        }
        resp.update(base_info)

        return jsonify(resp)

    except Exception as e:
        print("❌ Error en api_ultimo_evento:", e)
        try:
            con.rollback()
        except:
            pass

        resp = {
            "ok": False,
            "error": str(e),
            "evento": None,
        }
        resp.update(base_info)

        return jsonify(resp), 500


# ============================
#   API: TODOS LOS EVENTOS
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/eventos", methods=["GET"])
def api_eventos_partido(partido_id):
    """
    Devuelve TODOS los eventos registrados para este partido
    en orden cronológico.
    """
    con = Conexion().open
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT
                id              AS evento_id,
                tipo,
                equipo,
                jugador1,
                jugador2,
                minuto,
                texto_libre,
                creado_en
            FROM eventos_partido
            WHERE partido_id = %s
            ORDER BY
                CASE
                    WHEN minuto ~ '^[0-9]+$' THEN CAST(minuto AS INTEGER)
                    ELSE 9999
                END,
                creado_en
        """, (partido_id,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        eventos = [dict(zip(cols, r)) for r in rows]
        return jsonify(ok=True, eventos=eventos)
    except Exception as e:
        print("❌ Error obteniendo eventos:", e)
        return jsonify(ok=False, eventos=[], error=str(e)), 500
    finally:
        cur.close()
        con.close()


# ============================
#   API: GUARDAR ESTADÍSTICAS DEL PARTIDO
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/estadisticas", methods=["POST"])
def api_guardar_estadisticas(partido_id):
    """
    Endpoint usado por transmision_admin.html para guardar estadísticas.

    De momento SOLO recibe el JSON y lo imprime en consola para que 
    no falle la pantalla. Luego puedes conectarlo a una tabla en BD.
    """
    if not request.is_json:
        return jsonify(ok=False, error="Se requiere JSON"), 400

    data = request.get_json() or {}

    print("=== API GUARDAR ESTADISTICAS ===")
    print("Partido:", partido_id)
    print("Payload recibido:", data)

    # TODO: aquí luego puedes guardar en BD si quieres:
    # con = Conexion().open
    # cur = con.cursor()
    # cur.execute("INSERT INTO ...", (...))
    # con.commit()
    # cur.close()
    # con.close()

    return jsonify(
        ok=True,
        message="Estadísticas recibidas correctamente",
        partido_id=partido_id
    ), 200
# ============================
#   API: COMENTARIOS EN VIVO
# ============================
@ws_partidos.route("/transmision/<int:partido_id>/api/comentarios", methods=["GET", "POST"])
def api_comentarios(partido_id):
    """
    GET:
        - ?last_id=NN: devuelve solo comentarios con id > last_id
        - sin last_id: devuelve los últimos 50 comentarios
    POST:
        - JSON {nombre, texto}
        - guarda comentario y lo devuelve
    """
    from flask import request, jsonify

    if request.method == "POST":
        if not request.is_json:
            return jsonify(ok=False, error="Se requiere JSON"), 400

        data = request.get_json() or {}
        nombre = (data.get("nombre") or "").strip()
        texto = (data.get("texto") or "").strip()

        if not nombre or not texto:
            return jsonify(ok=False, error="Nombre y comentario son obligatorios"), 400

        try:
            con = Conexion().open
            cur = con.cursor()
            cur.execute("""
                INSERT INTO comentarios_partido (partido_id, nombre, texto)
                VALUES (%s, %s, %s)
                RETURNING id, creado_en
            """, (partido_id, nombre, texto))
            row = cur.fetchone()
            con.commit()
            cur.close()
            con.close()

            comentario = {
                "id": row[0],
                "partido_id": partido_id,
                "nombre": nombre,
                "texto": texto,
                "creado_en": row[1].isoformat() if row[1] else None
            }

            return jsonify(ok=True, comentario=comentario)

        except Exception as e:
            print("❌ Error guardando comentario:", e)
            try:
                con.rollback()
            except:
                pass
            return jsonify(ok=False, error=str(e)), 500

    # -------- GET ----------
    last_id = request.args.get("last_id", type=int)

    try:
        con = Conexion().open
        cur = con.cursor()

        if last_id:
            cur.execute("""
                SELECT id, partido_id, nombre, texto, creado_en
                FROM comentarios_partido
                WHERE partido_id = %s AND id > %s
                ORDER BY id ASC
            """, (partido_id, last_id))
        else:
            cur.execute("""
                SELECT id, partido_id, nombre, texto, creado_en
                FROM comentarios_partido
                WHERE partido_id = %s
                ORDER BY id DESC
                LIMIT 50
            """, (partido_id,))

        rows = cur.fetchall()
        cur.close()
        con.close()

        # los más viejos primero para pintar bien
        rows = list(reversed(rows))

        comentarios = []
        for r in rows:
            comentarios.append({
                "id": r[0],
                "partido_id": r[1],
                "nombre": r[2],
                "texto": r[3],
                "creado_en": r[4].isoformat() if r[4] else None
            })

        return jsonify(ok=True, comentarios=comentarios)

    except Exception as e:
        print("❌ Error obteniendo comentarios:", e)
        return jsonify(ok=False, error=str(e), comentarios=[]), 500
