# routes/dashboard.py
from flask import Blueprint, render_template
from models.dashboard import DashboardModel

ws_dashboard = Blueprint('ws_dashboard', __name__)
modelo_dashboard = DashboardModel()


@ws_dashboard.route("/admin", methods=["GET"])
def pantalla_dashboard():
    # Resumen de tarjetas
    resumen = modelo_dashboard.obtener_resumen()

    # Próximos partidos
    proximos_partidos = modelo_dashboard.listar_proximos_partidos(limite=10)

    # Transmisiones activas
    transmisiones_activas = modelo_dashboard.listar_transmisiones_activas()

    return render_template(
        "dashboard.html",
        # métricas
        torneos_activos=resumen.get("torneos_activos", 0),
        equipos_registrados=resumen.get("equipos_registrados", 0),
        partidos_programados=resumen.get("partidos_programados", 0),
        transmisiones_hoy=resumen.get("transmisiones_hoy", 0),
        # listas
        proximos_partidos=proximos_partidos,
        transmisiones_activas=transmisiones_activas,
    )
