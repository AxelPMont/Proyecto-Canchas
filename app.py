from flask import Flask, render_template, redirect, url_for
from routes.partidos import ws_partidos
from routes.area import ws_area
from routes.dashboard import ws_dashboard   
from routes.admin import ws_admin  
from routes.equipos import ws_equipos
from routes.reservas import ws_reservas

import os

app = Flask(__name__)
# 🔐 CLAVE SECRETA PARA FLASH Y SESSION
# puedes poner cualquier cadena larga; si quieres algo más seguro usa os.urandom(24)
app.config["SECRET_KEY"] = "clave-super-secreta-jayanca-2025"

app.register_blueprint(ws_partidos)
app.register_blueprint(ws_area)
app.register_blueprint(ws_dashboard)  
app.register_blueprint(ws_admin)
app.register_blueprint(ws_equipos)
app.register_blueprint(ws_reservas)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "img")
# =======================
# PANTALLA PRINCIPAL
# =======================
@app.route('/')
def home():
    return redirect(url_for('ws_partidos.pantalla_publica_partidos'))


# =======================
# PANTALLA ADMIN
# =======================
@app.route('/principal')
def principal():
    # redirige al dashboard admin
    return redirect(url_for('ws_admin.panel_principal'))





if __name__ == '__main__':
    app.run(port=3007, debug=True, host='0.0.0.0')
