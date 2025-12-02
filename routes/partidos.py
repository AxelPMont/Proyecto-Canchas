# routes/partidos.py
from flask import Blueprint, request, render_template, abort, jsonify
from models.partidos import PartidosModel
from models.publicaciones import PublicacionesModel
from conexionBD import Conexion
from datetime import datetime

ws_partidos = Blueprint('ws_partidos', __name__)
modelo = PartidosModel()
publicaciones_model = PublicacionesModel()

@ws_partidos.route("/partidos", methods=["GET"])
def pantalla_publica_partidos():

    filtro_tiempo = request.args.get("tiempo", "proximos")
    division_id = request.args.get("division_id")

    partidos = modelo.listar_partidos(filtro_tiempo, division_id)
    
    # Obtener publicaciones para la página principal (solo publicadas)
    publicaciones = publicaciones_model.listar_publicadas(limite=10)
    
    # Obtener noticias de tendencias (últimas 3 con categoría "Resultado")
    tendencias = publicaciones_model.listar_por_categoria("Resultado", limite=3)

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
        publicaciones=publicaciones,
        tendencias=tendencias,
        divisiones=divisiones,
        filtro_tiempo=filtro_tiempo,
        division_id=division_id,
        now=datetime.now()
    )


@ws_partidos.route("/transmision/<int:partido_id>", methods=["GET"])
def ver_transmision(partido_id):
    partido = modelo.obtener_partido(partido_id)

    if not partido:
        return abort(404)

    # Obtener el dominio para Twitch
    # Ejemplos:
    # 127.0.0.1
    # localhost
    # midominio.com
    twitch_parent = request.host.split(":")[0]

    return render_template(
        "transmision.html",
        partido=partido,
        twitch_parent=twitch_parent
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

    # 🧱 OPCIÓN 1: solo guardar en BD (tabla eventos_partido)
    try:
        con = Conexion().open
        cur = con.cursor()

        # Asegúrate de tener esta tabla creada en tu BD:
        # CREATE TABLE IF NOT EXISTS eventos_partido (
        #   id SERIAL PRIMARY KEY,
        #   partido_id INTEGER NOT NULL REFERENCES partidos(id) ON DELETE CASCADE,
        #   tipo VARCHAR(30) NOT NULL,
        #   equipo VARCHAR(20),
        #   jugador1 VARCHAR(120),
        #   jugador2 VARCHAR(120),
        #   minuto VARCHAR(10),
        #   texto_libre TEXT,
        #   creado_en TIMESTAMP DEFAULT NOW()
        # );

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
    
@ws_partidos.route("/transmision/<int:partido_id>/api/ultimo_evento", methods=["GET"])
def api_ultimo_evento(partido_id):
    """
    Devuelve el último evento registrado para este partido
    (gol, amarilla, roja, cambio, penal, etc.)
    """
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
            return jsonify(ok=False, mensaje="Sin eventos aún", evento=None)

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

        return jsonify(ok=True, evento=evento)

    except Exception as e:
        print("❌ Error en api_ultimo_evento:", e)
        try:
            con.rollback()
        except:
            pass
        return jsonify(ok=False, error=str(e)), 500
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



@ws_partidos.route("/noticias", methods=["GET"])
def todas_las_noticias():
    """Página para ver todas las publicaciones"""
    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = 12
    
    con = Conexion().open
    cur = con.cursor()
    
    # Obtener total de publicaciones
    cur.execute("SELECT COUNT(*) FROM publicaciones WHERE estado = %s", ("publicado",))
    total = cur.fetchone()[0]
    
    # Obtener publicaciones paginadas
    offset = (pagina - 1) * por_pagina
    cur.execute("""
        SELECT id, titulo, categoria, contenido, imagen_url, fecha_pub, estado
        FROM publicaciones 
        WHERE estado = %s
        ORDER BY fecha_pub DESC
        LIMIT %s OFFSET %s
    """, ("publicado", por_pagina, offset))
    
    rows = cur.fetchall()
    columnas = [desc[0] for desc in cur.description]
    publicaciones = [dict(zip(columnas, row)) for row in rows]
    
    cur.close()
    con.close()
    
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return render_template(
        "noticias.html",
        publicaciones=publicaciones,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total
    )

@ws_partidos.route("/noticias/<int:noticia_id>", methods=["GET"])
def ver_noticia(noticia_id):
    """Página para ver noticia completa"""
    publicacion = publicaciones_model.obtener(noticia_id)
    
    if not publicacion or publicacion.get("estado") != "publicado":
        return abort(404)
    
    # Obtener las 3 últimas noticias (excluyendo la actual)
    con = Conexion().open
    cur = con.cursor()
    cur.execute("""
        SELECT id, titulo, categoria, contenido, imagen_url, fecha_pub
        FROM publicaciones 
        WHERE estado = %s AND id != %s
        ORDER BY fecha_pub DESC
        LIMIT 3
    """, ("publicado", noticia_id))
    
    rows = cur.fetchall()
    columnas = [desc[0] for desc in cur.description]
    relacionadas = [dict(zip(columnas, row)) for row in rows]
    
    cur.close()
    con.close()
    
    return render_template(
        "noticia_detalle.html",
        publicacion=publicacion,
        relacionadas=relacionadas
    )