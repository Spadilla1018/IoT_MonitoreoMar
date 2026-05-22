import pymssql
import bcrypt

# =========================================
#   CONFIGURACIÓN SOMEE.COM
# =========================================

DB_SERVER   = "NivelMar_DW.mssql.somee.com"
DB_USER     = "Mireya_SQLLogin_1"
DB_PASSWORD = "6u98ogjgfl"
DB_NAME     = "NivelMar_DW"


def get_connection():
    return pymssql.connect(
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# =========================================
#   KPIs GENERALES
# =========================================

def get_kpis():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Fact_NivelMar")
    total_lecturas = cursor.fetchone()[0]

    cursor.execute("SELECT ROUND(AVG(ValorObservado), 1) FROM Fact_NivelMar")
    nivel_promedio = cursor.fetchone()[0]

    cursor.execute("""
        SELECT TOP 1
            f.ValorObservado,
            e.CodigoEstacion,
            t.Fecha
        FROM Fact_NivelMar f
        JOIN Dim_Estacion e ON f.ID_Estacion = e.ID_Estacion
        JOIN Dim_Tiempo   t ON f.ID_Tiempo   = t.ID_Tiempo
        ORDER BY f.ValorObservado DESC
    """)
    row = cursor.fetchone()
    nivel_max    = row[0] if row else 0
    estacion_max = row[1] if row else "-"
    fecha_max    = row[2] if row else "-"

    cursor.execute("SELECT COUNT(DISTINCT ID_Estacion) FROM Fact_NivelMar")
    sensores_activos = cursor.fetchone()[0]

    conn.close()
    return {
        "total_lecturas":   total_lecturas,
        "nivel_promedio":   float(nivel_promedio) if nivel_promedio else 0,
        "nivel_max":        float(nivel_max),
        "estacion_max":     estacion_max,
        "fecha_max":        str(fecha_max),
        "sensores_activos": sensores_activos,
    }


# =========================================
#   SERIE TEMPORAL MENSUAL POR ESTACIÓN
# =========================================

def get_serie_temporal():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            t.Anio,
            t.Mes,
            t.NombreMes,
            e.CodigoEstacion,
            ROUND(SUM(f.ValorObservado), 2) AS TotalMes
        FROM Fact_NivelMar f
        JOIN Dim_Tiempo   t ON f.ID_Tiempo   = t.ID_Tiempo
        JOIN Dim_Estacion e ON f.ID_Estacion = e.ID_Estacion
        GROUP BY t.Anio, t.Mes, t.NombreMes, e.CodigoEstacion
        ORDER BY t.Anio, t.Mes, e.CodigoEstacion
    """)
    rows = cursor.fetchall()
    conn.close()

    data = {}
    labels = []
    seen_labels = set()

    for anio, mes, nombre_mes, codigo, total in rows:
        label = f"{nombre_mes[:3]} {str(anio)[2:]}"
        if label not in seen_labels:
            labels.append(label)
            seen_labels.add(label)
        if codigo not in data:
            data[codigo] = {}
        data[codigo][label] = float(total)

    result = {}
    for codigo, valores in data.items():
        result[str(codigo)] = [valores.get(l, 0) for l in labels]

    return {"labels": labels, "series": result}


# =========================================
#   COMPARATIVO ANUAL
# =========================================

def get_comparativo_anual():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            t.Anio,
            e.CodigoEstacion,
            ROUND(SUM(f.ValorObservado), 2) AS TotalAnio
        FROM Fact_NivelMar f
        JOIN Dim_Tiempo   t ON f.ID_Tiempo   = t.ID_Tiempo
        JOIN Dim_Estacion e ON f.ID_Estacion = e.ID_Estacion
        GROUP BY t.Anio, e.CodigoEstacion
        ORDER BY t.Anio, e.CodigoEstacion
    """)
    rows = cursor.fetchall()
    conn.close()

    anios      = sorted(set(r[0] for r in rows))
    estaciones = sorted(set(r[1] for r in rows))
    data = {}

    for est in estaciones:
        data[str(est)] = []
        for anio in anios:
            val = next((float(r[2]) for r in rows
                        if r[0] == anio and r[1] == est), 0)
            data[str(est)].append(val)

    return {"anios": [str(a) for a in anios], "series": data}


# =========================================
#   ZONAS HIDROGRÁFICAS
# =========================================

def get_zonas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.ZonaHidrografica,
            COUNT(*)                        AS TotalLecturas,
            ROUND(SUM(f.ValorObservado), 2) AS TotalValor,
            ROUND(AVG(f.ValorObservado), 2) AS PromedioValor,
            ROUND(MAX(f.ValorObservado), 2) AS MaxValor
        FROM Fact_NivelMar f
        JOIN Dim_Ubicacion u ON f.ID_Ubicacion = u.ID_Ubicacion
        GROUP BY u.ZonaHidrografica
        ORDER BY TotalValor DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "zona":     r[0],
            "lecturas": r[1],
            "total":    float(r[2]),
            "promedio": float(r[3]),
            "maximo":   float(r[4]),
        }
        for r in rows
    ]


# =========================================
#   ESTACIONES
# =========================================

def get_estaciones():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.CodigoEstacion,
            e.NombreEstacion,
            e.DescripcionSensor,
            e.UnidadMedida,
            u.ZonaHidrografica,
            u.Departamento,
            u.Municipio,
            u.Latitud,
            u.Longitud,
            ROUND(MAX(f.ValorObservado), 2) AS MaxValor,
            ROUND(AVG(f.ValorObservado), 2) AS PromedioValor,
            COUNT(*)                         AS TotalLecturas
        FROM Dim_Estacion e
        JOIN Fact_NivelMar f ON e.ID_Estacion  = f.ID_Estacion
        JOIN Dim_Ubicacion u ON f.ID_Ubicacion = u.ID_Ubicacion
        GROUP BY
            e.CodigoEstacion, e.NombreEstacion,
            e.DescripcionSensor, e.UnidadMedida,
            u.ZonaHidrografica, u.Departamento,
            u.Municipio, u.Latitud, u.Longitud
        ORDER BY MaxValor DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "codigo":       r[0],
            "nombre":       r[1],
            "sensor":       r[2],
            "unidad":       r[3],
            "zona":         r[4],
            "departamento": r[5],
            "municipio":    r[6],
            "latitud":      float(r[7]) if r[7] else None,
            "longitud":     float(r[8]) if r[8] else None,
            "max_valor":    float(r[9]),
            "promedio":     float(r[10]),
            "lecturas":     r[11],
        }
        for r in rows
    ]


# =========================================
#   PROMEDIOS TEMPORALES
# =========================================

def get_promedios_temporales():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.Anio,
            CASE WHEN t.Mes <= 6 THEN 1 ELSE 2 END AS Semestre,
            ROUND(AVG(f.ValorObservado), 2)          AS Promedio
        FROM Fact_NivelMar f
        JOIN Dim_Tiempo t ON f.ID_Tiempo = t.ID_Tiempo
        GROUP BY t.Anio, CASE WHEN t.Mes <= 6 THEN 1 ELSE 2 END
        ORDER BY t.Anio, Semestre
    """)
    semestres_raw = cursor.fetchall()

    cursor.execute("""
        SELECT
            t.Mes,
            t.NombreMes,
            ROUND(AVG(f.ValorObservado), 2)   AS Promedio,
            ROUND(STDEV(f.ValorObservado), 2) AS Variabilidad
        FROM Fact_NivelMar f
        JOIN Dim_Tiempo t ON f.ID_Tiempo = t.ID_Tiempo
        GROUP BY t.Mes, t.NombreMes
        ORDER BY t.Mes
    """)
    meses_raw = cursor.fetchall()
    conn.close()

    semestres = [
        {"label": f"S{r[1]} {r[0]}", "promedio": float(r[2])}
        for r in semestres_raw
    ]
    meses = [
        {
            "mes":          r[0],
            "nombre":       r[1],
            "promedio":     float(r[2]) if r[2] else 0,
            "variabilidad": float(r[3]) if r[3] else 0,
        }
        for r in meses_raw
    ]
    return {"semestres": semestres, "meses": meses}


# =========================================
#   ALERTAS
# =========================================

def get_alertas(umbral=120):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 20
            t.Fecha,
            e.CodigoEstacion,
            e.NombreEstacion,
            u.ZonaHidrografica,
            f.ValorObservado,
            f.Hora
        FROM Fact_NivelMar f
        JOIN Dim_Tiempo    t ON f.ID_Tiempo    = t.ID_Tiempo
        JOIN Dim_Estacion  e ON f.ID_Estacion  = e.ID_Estacion
        JOIN Dim_Ubicacion u ON f.ID_Ubicacion = u.ID_Ubicacion
        WHERE f.ValorObservado >= %d
        ORDER BY f.ValorObservado DESC
    """, umbral)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "fecha":  str(r[0]),
            "codigo": r[1],
            "nombre": r[2],
            "zona":   r[3],
            "valor":  float(r[4]),
            "hora":   r[5],
        }
        for r in rows
    ]


# =========================================
#   LOGIN — verifica contraseña cifrada
#   y también acepta contraseñas en texto
#   plano (usuarios antiguos)
# =========================================

def verificar_usuario(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ID_Usuario, Nombre, Apellido, Rol, Password
        FROM Usuarios
        WHERE Email = %s AND Activo = 1
    """, (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    id_usuario = row[0]
    nombre     = row[1]
    apellido   = row[2]
    rol        = row[3]
    pwd_stored = row[4]

    # Verificar si la contraseña está cifrada con bcrypt
    try:
        pwd_bytes = pwd_stored.encode('utf-8') if isinstance(pwd_stored, str) else pwd_stored
        es_valida = bcrypt.checkpw(password.encode('utf-8'), pwd_bytes)
    except Exception:
        # Si no es bcrypt, comparar como texto plano (usuarios antiguos)
        es_valida = (password == pwd_stored)

    if es_valida:
        return {
            "id":       id_usuario,
            "nombre":   nombre,
            "apellido": apellido,
            "rol":      rol,
        }
    return None


# =========================================
#   REGISTRO — guarda contraseña cifrada
# =========================================

def registrar_usuario(nombre, apellido, email, password):
    # Cifrar contraseña con bcrypt
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    conn = get_connection()
    conn.autocommit(True)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Usuarios (Nombre, Apellido, Email, Password, Rol, Activo)
            VALUES (%s, %s, %s, %s, 'viewer', 1)
        """, (nombre, apellido, email, password_hash))

        cursor.execute(
            "SELECT ID_Usuario, Nombre FROM Usuarios WHERE Email = %s", (email,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {"ok": True, "id": row[0]}
        else:
            return {"ok": False, "error": "Insert ejecutado pero no se encontró el registro"}

    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}