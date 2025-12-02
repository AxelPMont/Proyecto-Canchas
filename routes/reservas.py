from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from models.reservas import ReservasModel
from models.canchas import CanchasModel
from datetime import datetime, date, timedelta

ws_reservas = Blueprint('ws_reservas', __name__)
reservas_model = ReservasModel()
canchas_model = CanchasModel()

HORA_APERTURA = 6
HORA_CIERRE = 22
DURACION_MINIMA = 1
DURACION_MAXIMA = 3


@ws_reservas.route("/reservas", methods=["GET"])
def pagina_reservas():
    canchas = canchas_model.listar()
    fecha_seleccionada = request.args.get("fecha", date.today().isoformat())
    cancha_id = request.args.get("cancha_id", type=int)

    if canchas and not cancha_id:
        cancha_id = canchas[0]["id"]

    horarios_ocupados = []
    if cancha_id and fecha_seleccionada:
        horarios_ocupados = reservas_model.obtener_horarios_ocupados(cancha_id, fecha_seleccionada)

    return render_template(
        "reservas.html",
        canchas=canchas,
        cancha_id=cancha_id,
        fecha_seleccionada=fecha_seleccionada,
        horarios_ocupados=horarios_ocupados,
        hora_apertura=HORA_APERTURA,
        hora_cierre=HORA_CIERRE,
        fecha_minima=date.today().isoformat(),
        fecha_maxima=(date.today() + timedelta(days=30)).isoformat()
    )


@ws_reservas.route("/reservas/disponibilidad", methods=["GET"])
def api_disponibilidad():
    cancha_id = request.args.get("cancha_id", type=int)
    fecha = request.args.get("fecha")

    if not cancha_id or not fecha:
        return jsonify({"ok": False, "error": "Parámetros requeridos"}), 400

    horarios_ocupados = reservas_model.obtener_horarios_ocupados(cancha_id, fecha)

    slots = []
    for hora in range(HORA_APERTURA, HORA_CIERRE):
        hora_inicio = f"{hora:02d}:00"
        hora_fin = f"{hora+1:02d}:00"

        ocupado = False
        for h in horarios_ocupados:
            h_inicio = h["hora_inicio"]
            h_fin = h["hora_fin"]
            if h_inicio < hora_fin and h_fin > hora_inicio:
                ocupado = True
                break

        slots.append({
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "disponible": not ocupado
        })

    return jsonify({"ok": True, "slots": slots, "fecha": fecha})


@ws_reservas.route("/reservas/nueva", methods=["POST"])
def crear_reserva():
    cancha_id = request.form.get("cancha_id", type=int)
    fecha = request.form.get("fecha")
    hora_inicio = request.form.get("hora_inicio")
    hora_fin = request.form.get("hora_fin")
    cliente_nombre = request.form.get("cliente_nombre", "").strip()
    cliente_telefono = request.form.get("cliente_telefono", "").strip()
    cliente_email = request.form.get("cliente_email", "").strip() or None
    notas = request.form.get("notas", "").strip() or None

    if not all([cancha_id, fecha, hora_inicio, hora_fin, cliente_nombre, cliente_telefono]):
        flash("Todos los campos obligatorios deben ser completados", "error")
        return redirect(url_for("ws_reservas.pagina_reservas"))

    try:
        fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()
        if fecha_reserva < date.today():
            flash("No se pueden hacer reservas en fechas pasadas", "error")
            return redirect(url_for("ws_reservas.pagina_reservas"))
    except ValueError:
        flash("Fecha inválida", "error")
        return redirect(url_for("ws_reservas.pagina_reservas"))

    try:
        h_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
        h_fin = datetime.strptime(hora_fin, "%H:%M").time()

        if h_inicio.hour < HORA_APERTURA or h_fin.hour > HORA_CIERRE:
            flash(f"El horario debe estar entre {HORA_APERTURA}:00 y {HORA_CIERRE}:00", "error")
            return redirect(url_for("ws_reservas.pagina_reservas"))

        duracion = h_fin.hour - h_inicio.hour
        if duracion < DURACION_MINIMA or duracion > DURACION_MAXIMA:
            flash(f"La duración debe ser entre {DURACION_MINIMA} y {DURACION_MAXIMA} horas", "error")
            return redirect(url_for("ws_reservas.pagina_reservas"))

    except ValueError:
        flash("Horario inválido", "error")
        return redirect(url_for("ws_reservas.pagina_reservas"))

    reserva_id, error = reservas_model.crear(
        cancha_id, fecha, hora_inicio, hora_fin,
        cliente_nombre, cliente_telefono, cliente_email, notas
    )

    if error:
        flash(error, "error")
        return redirect(url_for("ws_reservas.pagina_reservas"))

    flash("Reserva creada exitosamente. Recibirás confirmación pronto.", "success")
    return redirect(url_for("ws_reservas.confirmacion_reserva", reserva_id=reserva_id))


@ws_reservas.route("/reservas/confirmacion/<int:reserva_id>", methods=["GET"])
def confirmacion_reserva(reserva_id):
    reserva = reservas_model.obtener(reserva_id)
    if not reserva:
        flash("Reserva no encontrada", "error")
        return redirect(url_for("ws_reservas.pagina_reservas"))

    return render_template("reserva_confirmacion.html", reserva=reserva)
