# routes/equipos.py
# routes/equipos.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os
from models.equipos import EquiposModel
from models.grupos import GruposModel

ws_equipos = Blueprint('ws_equipos', __name__, url_prefix="/admin")

equipos_model = EquiposModel()
grupos_model = GruposModel()

# ====== PANEL PRINCIPAL (Dashboard) con equipos ======
@ws_equipos.route("/panel", methods=["GET"])
def panel_admin():
    equipos = equipos_model.listar_equipos()
    return render_template("dashboard.html", equipos=equipos)

# ====== CREAR EQUIPO ======
@ws_equipos.route("/equipos/crear", methods=["POST"])
def crear_equipo():
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    logo_url = request.form.get("logo_url")  # o manejar subida de archivos

    if not nombre:
        flash("El nombre del equipo es obligatorio", "error")
        return redirect(url_for("ws_equipos.panel_admin"))

    equipos_model.crear_equipo(nombre, categoria, logo_url)
    flash("Equipo creado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== EDITAR EQUIPO ======
@ws_equipos.route("/equipos/<int:equipo_id>/editar", methods=["POST"])
def editar_equipo(equipo_id):
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    logo_url = request.form.get("logo_url")

    if not nombre:
        flash("El nombre del equipo es obligatorio", "error")
        return redirect(url_for("ws_equipos.panel_admin"))

    equipos_model.actualizar_equipo(equipo_id, nombre, categoria, logo_url)
    flash("Equipo actualizado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== ELIMINAR EQUIPO ======
@ws_equipos.route("/equipos/<int:equipo_id>/eliminar", methods=["POST"])
def eliminar_equipo(equipo_id):
    equipos_model.eliminar_equipo(equipo_id)
    flash("Equipo eliminado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== GENERAR GRUPOS ALEATORIOS ======
@ws_equipos.route("/grupos/generar", methods=["POST"])
def generar_grupos():
    torneo_id = request.form.get("torneo_id", type=int)

    # Aquí puedes decidir si tomas TODOS los equipos
    # o solo los equipos seleccionados en el formulario.
    # Ejemplo simple: usar todos los equipos registrados
    equipos = equipos_model.listar_equipos()
    equipos_ids = [e["id"] for e in equipos]

    ok = grupos_model.generar_grupos_aleatorios(
        torneo_id=torneo_id,
        equipos_ids=equipos_ids,
        equipos_por_grupo=4
    )

    if ok:
        flash("Grupos generados correctamente", "success")
    else:
        flash("Error al generar los grupos", "error")

    return redirect(url_for("ws_equipos.panel_admin"))
# routes/equipos.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.equipos import EquiposModel
from models.grupos import GruposModel

ws_equipos = Blueprint('ws_equipos', __name__, url_prefix="/admin")

equipos_model = EquiposModel()
grupos_model = GruposModel()

# ====== PANEL PRINCIPAL (Dashboard) con equipos ======
@ws_equipos.route("/panel", methods=["GET"])
def panel_admin():
    equipos = equipos_model.listar_equipos()
    return render_template("dashboard.html", equipos=equipos)

# ====== CREAR EQUIPO ======
@ws_equipos.route("/equipos/crear", methods=["POST"])
def crear_equipo():
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    logo_file = request.files.get("logo")  # 👈 viene del input name="logo"

    if not nombre:
        flash("El nombre del equipo es obligatorio", "error")
        return redirect(url_for("ws_equipos.panel_admin"))

    filename = None
    if logo_file and logo_file.filename:
        filename = secure_filename(logo_file.filename)
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        logo_file.save(os.path.join(upload_folder, filename))

    # Guarda solo el nombre del archivo en la BD
    equipos_model.crear_equipo(nombre, categoria, filename)

    flash("Equipo creado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== EDITAR EQUIPO ======
@ws_equipos.route("/equipos/<int:equipo_id>/editar", methods=["POST"])
def editar_equipo(equipo_id):
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    logo_url = request.form.get("logo_url")

    if not nombre:
        flash("El nombre del equipo es obligatorio", "error")
        return redirect(url_for("ws_equipos.panel_admin"))

    equipos_model.actualizar_equipo(equipo_id, nombre, categoria, logo_url)
    flash("Equipo actualizado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== ELIMINAR EQUIPO ======
@ws_equipos.route("/equipos/<int:equipo_id>/eliminar", methods=["POST"])
def eliminar_equipo(equipo_id):
    equipos_model.eliminar_equipo(equipo_id)
    flash("Equipo eliminado correctamente", "success")
    return redirect(url_for("ws_equipos.panel_admin"))

# ====== GENERAR GRUPOS ALEATORIOS ======
@ws_equipos.route("/grupos/generar", methods=["POST"])
def generar_grupos():
    torneo_id = request.form.get("torneo_id", type=int)

    # Aquí puedes decidir si tomas TODOS los equipos
    # o solo los equipos seleccionados en el formulario.
    # Ejemplo simple: usar todos los equipos registrados
    equipos = equipos_model.listar_equipos()
    equipos_ids = [e["id"] for e in equipos]

    ok = grupos_model.generar_grupos_aleatorios(
        torneo_id=torneo_id,
        equipos_ids=equipos_ids,
        equipos_por_grupo=4
    )

    if ok:
        flash("Grupos generados correctamente", "success")
    else:
        flash("Error al generar los grupos", "error")

    return redirect(url_for("ws_equipos.panel_admin"))
