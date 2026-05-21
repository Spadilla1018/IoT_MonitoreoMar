from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_super_secreta_simmar_iot"


@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/mvo")
def mvo():
    return render_template("mvo.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Credenciales de prueba
        if username == "admin" and password == "1234":
            session["usuario"] = username
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("index"))

    # GET → redirige al modal del index
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)