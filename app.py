from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import (
    get_kpis,
    get_serie_temporal,
    get_comparativo_anual,
    get_zonas,
    get_estaciones,
    get_promedios_temporales,
    get_alertas,
    verificar_usuario,
    registrar_usuario,
    get_resumen_ejecutivo,
    get_analisis_tiempo,
    get_analisis_ubicacion,
    get_dispositivos_sensores,
    get_detalle_mediciones,
)
from keep_alive import start
start()

app = Flask(__name__)
app.secret_key = "clave_super_secreta_simmar_iot"


# =========================================
#   PÁGINA PRINCIPAL
# =========================================

@app.route("/")
def index():
    return render_template("index.html", usuario=session.get("usuario"))


# =========================================
#   SOBRE NOSOTROS
# =========================================

@app.route("/mvo")
def mvo():
    return render_template("mvo.html")


# =========================================
#   LOGIN
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("username")
        password = request.form.get("password")
        print(f"DEBUG - Email: {email}, Password: {password}")
        try:
            usuario = verificar_usuario(email, password)
            print(f"DEBUG - Usuario encontrado: {usuario}")
            if usuario:
                session["usuario"]  = usuario["nombre"] + " " + usuario["apellido"]
                session["rol"]      = usuario["rol"]
                session["id"]       = usuario["id"]
                return redirect(url_for("dashboard"))
            else:
                print("DEBUG - Credenciales incorrectas")
                return render_template("index.html",
                                       usuario=None,
                                       error="Credenciales incorrectas")
        except Exception as e:
            print(f"DEBUG - Error: {str(e)}")
            return render_template("index.html",
                                   usuario=None,
                                   error=f"Error: {str(e)}")
    return redirect(url_for("index"))


# =========================================
#   REGISTRO
# =========================================

@app.route("/registro", methods=["POST"])
def registro():
    nombre    = request.form.get("nombre")
    apellido  = request.form.get("apellido")
    email     = request.form.get("email")
    password  = request.form.get("password")
    confirmar = request.form.get("confirmar")

    print(f"DEBUG REGISTRO - nombre:{nombre} apellido:{apellido} email:{email}")

    if not all([nombre, apellido, email, password, confirmar]):
        return render_template("index.html",
                               usuario=None,
                               error_registro="Todos los campos son obligatorios",
                               mostrar_registro=True)

    if password != confirmar:
        return render_template("index.html",
                               usuario=None,
                               error_registro="Las contraseñas no coinciden",
                               mostrar_registro=True)

    if len(password) < 6:
        return render_template("index.html",
                               usuario=None,
                               error_registro="La contraseña debe tener mínimo 6 caracteres",
                               mostrar_registro=True)

    resultado = registrar_usuario(nombre, apellido, email, password)
    print(f"DEBUG REGISTRO - Resultado: {resultado}")

    if resultado["ok"]:
        return render_template("index.html",
                               usuario=None,
                               exito_registro="✅ Usuario registrado correctamente. Ya puedes iniciar sesión.")
    else:
        if "UNIQUE" in str(resultado["error"]) or "duplicate" in str(resultado["error"]).lower():
            error_msg = "Ese correo ya está registrado."
        else:
            error_msg = f"Error al registrar: {resultado['error']}"
        return render_template("index.html",
                               usuario=None,
                               error_registro=error_msg,
                               mostrar_registro=True)


# =========================================
#   DASHBOARD
# =========================================

@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("index"))
    try:
        kpis       = get_kpis()
        estaciones = get_estaciones()
        zonas      = get_zonas()
    except Exception as e:
        kpis = {
            "total_lecturas":   0,
            "nivel_promedio":   0,
            "nivel_max":        0,
            "estacion_max":     "-",
            "fecha_max":        "-",
            "sensores_activos": 0,
        }
        estaciones = []
        zonas      = []

    return render_template("dashboard.html",
                           kpis=kpis,
                           estaciones=estaciones,
                           zonas=zonas,
                           usuario=session.get("usuario"),
                           rol=session.get("rol"))


# =========================================
#   APIs JSON PARA GRÁFICOS
# =========================================

@app.route("/api/serie-temporal")
def api_serie_temporal():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_serie_temporal())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/comparativo-anual")
def api_comparativo_anual():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_comparativo_anual())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/zonas")
def api_zonas():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_zonas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/promedios-temporales")
def api_promedios_temporales():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_promedios_temporales())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alertas")
def api_alertas():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_alertas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/estaciones")
def api_estaciones():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_estaciones())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resumen-ejecutivo")
def api_resumen_ejecutivo():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_resumen_ejecutivo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analisis-tiempo")
def api_analisis_tiempo():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_analisis_tiempo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analisis-ubicacion")
def api_analisis_ubicacion():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_analisis_ubicacion())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dispositivos-sensores")
def api_dispositivos_sensores():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_dispositivos_sensores())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/detalle-mediciones")
def api_detalle_mediciones():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401
    try:
        return jsonify(get_detalle_mediciones())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================
#   LOGOUT
# =========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =========================================
#   MAIN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)