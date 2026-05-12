import urllib.request
import urllib.parse
import json
import sqlite3
from datetime import date, timedelta
import pandas as pd

# ---------------------------------------------------------------------------
# Configuración de ubicaciones
# ---------------------------------------------------------------------------
UBICACIONES = [
    {"ciudad": "Madrid",       "latitud": 40.4168, "longitud": -3.7038},
    {"ciudad": "Torrelodones", "latitud": 40.5785, "longitud": -3.9284},
    {"ciudad": "Guadarrama",   "latitud": 40.6772, "longitud": -4.1101},
]

# Rango de fechas: semana actual (hoy a 7 días)
hoy    = date.today()
inicio = hoy 
fin    = inicio + timedelta(days=6)

BASE_URL  = "https://api.open-meteo.com/v1/forecast"
DB_PATH   = "weather.db"
TABLA     = "prevision_semanal"

VARIABLES_DAILY = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "weathercode",
    "uv_index_max",
    "sunrise",
    "sunset",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
WMO_TABLA = {
    0:  "Despejado",
    1:  "Principalmente despejado",
    2:  "Parcialmente nublado",
    3:  "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia intensa",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada intensa",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve intensos",
    95: "Tormenta",
    96: "Tormenta con granizo leve",
    99: "Tormenta con granizo intenso",
}

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves",
           "Viernes", "Sábado", "Domingo"]


def descripcion_wmo(code: int) -> str:
    return WMO_TABLA.get(int(code), f"Código {int(code)}")


def nivel_uv(uv: float) -> str:
    if uv < 3:  return "Bajo"
    if uv < 6:  return "Moderado"
    if uv < 8:  return "Alto"
    if uv < 11: return "Muy alto"
    return "Extremo"


def hora_local(iso_str: str) -> str:
    return iso_str[11:16] if iso_str else "—"


# ---------------------------------------------------------------------------
# Llamada a la API
# ---------------------------------------------------------------------------
def obtener_prevision(latitud: float, longitud: float) -> dict:
    params = {
        "latitude":           latitud,
        "longitude":          longitud,
        "daily":              ",".join(VARIABLES_DAILY),
        "start_date":         inicio.isoformat(),
        "end_date":           fin.isoformat(),
        "timezone":           "Europe/Madrid",
        "wind_speed_unit":    "kmh",
        "precipitation_unit": "mm",
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"  [ERROR red] {e.reason}")
        return {}
    except json.JSONDecodeError:
        print("  [ERROR] Respuesta JSON no válida.")
        return {}


# ---------------------------------------------------------------------------
# Construcción del DataFrame para una ubicación
# ---------------------------------------------------------------------------
def datos_a_dataframe(datos: dict, ciudad: str,
                      latitud: float, longitud: float) -> pd.DataFrame:
    daily = datos.get("daily", {})
    if not daily:
        return pd.DataFrame()

    df = pd.DataFrame({
        "ciudad":           ciudad,
        "latitud":          latitud,
        "longitud":         longitud,
        "fecha":            daily.get("time", []),
        "temp_max_c":       daily.get("temperature_2m_max", []),
        "temp_min_c":       daily.get("temperature_2m_min", []),
        "precipitacion_mm": daily.get("precipitation_sum", []),
        "prob_lluvia_pct":  daily.get("precipitation_probability_max", []),
        "viento_max_kmh":   daily.get("windspeed_10m_max", []),
        "rachas_max_kmh":   daily.get("windgusts_10m_max", []),
        "weathercode":      daily.get("weathercode", []),
        "uv_index_max":     daily.get("uv_index_max", []),
        "amanecer":         daily.get("sunrise", []),
        "atardecer":        daily.get("sunset", []),
    })

    # Columnas derivadas legibles
    df["estado"]      = df["weathercode"].apply(descripcion_wmo)
    df["nivel_uv"]    = df["uv_index_max"].apply(nivel_uv)
    df["amanecer"]    = df["amanecer"].apply(hora_local)
    df["atardecer"]   = df["atardecer"].apply(hora_local)
    df["dia_semana"]  = (pd.to_datetime(df["fecha"])
                         .dt.weekday
                         .apply(lambda d: DIAS_ES[d]))
    df["fecha_carga"] = date.today().isoformat()

    return df


# ---------------------------------------------------------------------------
# Persistencia en SQLite
# ---------------------------------------------------------------------------
def guardar_en_sqlite(df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    """
    Guarda el DataFrame en SQLite.
    Usa INSERT OR REPLACE para evitar duplicados por (ciudad, fecha).
    """
    if df.empty:
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLA} (
            ciudad               TEXT NOT NULL,
            latitud              REAL,
            longitud             REAL,
            fecha                TEXT NOT NULL,
            dia_semana           TEXT,
            temp_max_c           REAL,
            temp_min_c           REAL,
            precipitacion_mm     REAL,
            prob_lluvia_pct      REAL,
            viento_max_kmh       REAL,
            rachas_max_kmh       REAL,
            weathercode          INTEGER,
            estado               TEXT,
            uv_index_max         REAL,
            nivel_uv             TEXT,
            amanecer             TEXT,
            atardecer            TEXT,
            fecha_carga          TEXT,
            PRIMARY KEY (ciudad, fecha)
        )
    """)

    columnas = [
        "ciudad", "latitud", "longitud", "fecha", "dia_semana",
        "temp_max_c", "temp_min_c", "precipitacion_mm", "prob_lluvia_pct",
        "viento_max_kmh", "rachas_max_kmh", "weathercode", "estado",
        "uv_index_max", "nivel_uv", "amanecer", "atardecer", "fecha_carga",
    ]

    filas = [tuple(row) for row in df[columnas].itertuples(index=False)]
    placeholders = ", ".join(["?"] * len(columnas))
    cur.executemany(
        f"INSERT OR REPLACE INTO {TABLA} "
        f"({', '.join(columnas)}) VALUES ({placeholders})",
        filas,
    )

    con.commit()
    con.close()
    print(f"  SQLite → {len(filas)} filas guardadas en '{db_path}' "
          f"(tabla: {TABLA})")


# ---------------------------------------------------------------------------
# Presentación en consola
# ---------------------------------------------------------------------------
def mostrar_prevision(df: pd.DataFrame) -> None:
    ciudad = df["ciudad"].iloc[0]
    sep    = "─" * 56

    print(f"\n{'─'*56}")
    print(f"  Previsión — {ciudad}")
    print(f"  {inicio.strftime('%d/%m/%Y')} al {fin.strftime('%d/%m/%Y')}")
    print(f"{'─'*56}\n")

    for _, row in df.iterrows():
        hoy_marker = " ◀ HOY" if row["fecha"] == hoy.isoformat() else ""
        fecha_fmt  = date.fromisoformat(row["fecha"]).strftime("%d/%m/%Y")

        print(f"  {row['dia_semana']:10s}  {fecha_fmt}{hoy_marker}")
        print(f"  {sep[:48]}")
        print(f"  {'Estado:':<22} {row['estado']}")
        print(f"  {'Temperatura:':<22} {row['temp_min_c']:.1f}°C "
              f"— {row['temp_max_c']:.1f}°C")
        print(f"  {'Precipitación:':<22} {row['precipitacion_mm']:.1f} mm  "
              f"(prob.: {int(row['prob_lluvia_pct'])}%)")
        print(f"  {'Viento máx./rachas:':<22} {row['viento_max_kmh']:.0f} km/h"
              f"  /  {row['rachas_max_kmh']:.0f} km/h")
        print(f"  {'Índice UV:':<22} {row['uv_index_max']:.1f}  "
              f"({row['nivel_uv']})")
        print(f"  {'Amanecer / Atardecer:':<22} "
              f"{row['amanecer']}  /  {row['atardecer']}")
        print()

# ---------------------------------------------------------------------------
# Recuperar datos de la bbdd
# ---------------------------------------------------------------------------
def obtener_datos_clima(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Se conecta a la base de datos local y devuelve un DataFrame 
    con las ciudades y sus temperaturas.
    """
    
    try:
        # Conectamos a la base de datos
        with sqlite3.connect(db_path) as conn:
            # Query para extraer los datos (ajusta 'nombre_tabla' a la tuya)
            query = "SELECT ciudad, fecha, dia_semana, temp_max_c, temp_min_c, precipitacion_mm, prob_lluvia_pct, estado, fecha_carga  FROM prevision_semanal"


            # Pandas lee el SQL y crea el DataFrame automáticamente
            df = pd.read_sql_query(query, conn)
            return df
            
    except Exception as e:
        print(f"Error al leer la base de datos: {e}")
        return pd.DataFrame() # Devuelve un DF vacío si hay error
    
# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    frames = []

    for ubic in UBICACIONES:
        ciudad   = ubic["ciudad"]
        latitud  = ubic["latitud"]
        longitud = ubic["longitud"]

        print(f"\n>>> Consultando API para: {ciudad} "
              f"({latitud}, {longitud})")

        datos = obtener_prevision(latitud, longitud)
        if not datos:
            print(f"  Sin datos para {ciudad}, se omite.")
            continue

        df_ciudad = datos_a_dataframe(datos, ciudad, latitud, longitud)
        mostrar_prevision(df_ciudad)
        guardar_en_sqlite(df_ciudad)
        frames.append(df_ciudad)
        #nuevo = obtener_datos_clima(DB_PATH)



    # DataFrame consolidado con todas las ubicaciones
    if frames:
        df_total = pd.concat(frames, ignore_index=True)

        print("\n" + "=" * 56)
        print("  DataFrame consolidado (todas las ubicaciones)")
        print("=" * 56)
        cols_vista = [
            "ciudad", "fecha", "dia_semana",
            "temp_min_c", "temp_max_c",
            "precipitacion_mm", "prob_lluvia_pct",
            "viento_max_kmh", "estado",
        ]
        print(df_total[cols_vista]
              .sort_values(["fecha", "ciudad"])
              .to_string(index=False))
        print(f"\n  Total de registros : {len(df_total)}")
        print(f"  Ciudades           : "
              f"{', '.join(df_total['ciudad'].unique())}")
        print(f"  Base de datos      : {DB_PATH}\n")
