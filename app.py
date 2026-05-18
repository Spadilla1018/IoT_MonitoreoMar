from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_super_secreta"  # necesaria para usar sesion


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mvo")
def mvo():
    return render_template("mvo.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Usuario de prueba (En producción, esto debería ser una consulta a una base de datos)
        if username == "admin" and password == "1234":
            session["usuario"] = username
            return redirect(url_for("dashboard"))
        else:
            # Por ahora, si falla, vuelve al inicio
            return redirect(url_for("index"))
    else:
        # Si alguien entra por GET a /login, puedes mostrar una página o redirigir
        return redirect(url_for("index"))  # usamos el modal del index, así que no necesitamos login.html


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)


