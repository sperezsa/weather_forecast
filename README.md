# weather_forecast

Consulta de previsión meteorológica semanal para múltiples ubicaciones usando la API pública de [Open-Meteo](https://open-meteo.com). Los resultados se almacenan en un DataFrame de pandas y se persisten en una base de datos SQLite local.

---

## Características

- Consulta la previsión diaria para una semana desde el día de hoy 
- Soporte para múltiples ubicaciones configurables en un bucle
- Variables meteorológicas: temperatura, precipitación, viento, índice UV, amanecer y atardecer
- Decodificación de códigos WMO a descripciones en español
- Resultados consolidados en un DataFrame de pandas ordenado por fecha y ciudad
- Persistencia en SQLite (`weather.db`) con clave primaria `(ciudad, fecha)` para evitar duplicados
- Cuadro de mandos interactivo en Streamlit
- Dependencias externas `pandas` para uso de dataframes y `plotly` y `streamlit` para la aplicación interactiva 

No requiere API key. Documentación: https://open-meteo.com/en/docs

---

## Requisitos

- Python 3.10 o superior
- [pandas](https://pandas.pydata.org/) 
- [plotly](https://plotly.com/) y [streamlit](https://streamlit.io)

El resto de módulos utilizados (`urllib`, `json`, `sqlite3`, `datetime`) forman parte de la biblioteca estándar de Python.

---

## Instalación

### Con uv (recomendado)

```bash
git clone https://github.com/sperezsa/weather_forecast.git
cd weather_forecast
uv sync
```

### Con pip + venv

```bash
git clone https://github.com/sperezsa/weather_forecast.git
cd weather_forecast
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows
pip install pandas
```

---

## Uso

```bash
# Con uv
uv run main.py

# Con venv activo
python main.py
```

La salida por consola muestra la previsión detallada de cada ciudad y, al final, un resumen consolidado con todas las ubicaciones ordenado por fecha:

```
>>> Consultando API para: Madrid (40.4168, -3.7038)

────────────────────────────────────────────────────────
  Previsión — Madrid
  12/05/2025 al 18/05/2025
────────────────────────────────────────────────────────

  Lunes       12/05/2025 ◀ HOY
  ────────────────────────────────────────────────────
  Estado:                Parcialmente nublado
  Temperatura:           11.2°C — 22.5°C
  Precipitación:         0.0 mm  (prob.: 10%)
  Viento máx./rachas:    18 km/h  /  32 km/h
  Índice UV:             6.2  (Alto)
  Amanecer / Atardecer:  06:47  /  21:08
  ...

========================================================
  DataFrame consolidado (todas las ubicaciones)
========================================================
  ciudad        fecha       dia_semana  temp_min_c  temp_max_c  ...
  Guadarrama    2025-05-12  Lunes             8.1        19.3  ...
  Madrid        2025-05-12  Lunes            11.2        22.5  ...
  ...
```

---

## Configuración de ubicaciones

Las ciudades consultadas se definen en la lista `UBICACIONES` al inicio del script:

```python
UBICACIONES = [
    {"ciudad": "Madrid",       "latitud": 40.4168, "longitud": -3.7038},
    {"ciudad": "Guadarrama",   "latitud": 40.6772, "longitud": -4.1101},
    {"ciudad": "Torrelodones", "latitud": 40.5785, "longitud": -3.9284},
]
```

Para añadir una nueva ubicación basta con añadir un diccionario más a la lista con el nombre y las coordenadas geográficas.

---

## Base de datos

Los datos se guardan en `weather.db` (SQLite), en la tabla `prevision_semanal`.

| Campo | Tipo | Descripción |
|---|---|---|
| `ciudad` | TEXT | Nombre de la ciudad |
| `latitud` | REAL | Latitud geográfica |
| `longitud` | REAL | Longitud geográfica |
| `fecha` | TEXT | Fecha en formato `YYYY-MM-DD` |
| `dia_semana` | TEXT | Nombre del día en español |
| `temp_max_c` | REAL | Temperatura máxima (°C) |
| `temp_min_c` | REAL | Temperatura mínima (°C) |
| `precipitacion_mm` | REAL | Precipitación acumulada (mm) |
| `prob_lluvia_pct` | REAL | Probabilidad de lluvia (%) |
| `viento_max_kmh` | REAL | Velocidad máxima del viento (km/h) |
| `rachas_max_kmh` | REAL | Rachas máximas de viento (km/h) |
| `weathercode` | INTEGER | Código WMO del estado del tiempo |
| `estado` | TEXT | Descripción del estado (español) |
| `uv_index_max` | REAL | Índice UV máximo |
| `nivel_uv` | TEXT | Nivel UV (Bajo / Moderado / Alto / Muy alto / Extremo) |
| `amanecer` | TEXT | Hora de amanecer (HH:MM) |
| `atardecer` | TEXT | Hora de atardecer (HH:MM) |
| `fecha_carga` | TEXT | Fecha de ejecución del script |

La clave primaria es `(ciudad, fecha)`, por lo que cada ejecución actualiza los registros existentes sin generar duplicados.

---

## Cuadro de mandos interactivo

El fichero `app.py` lanza un dashboard interactivo con [Streamlit](https://streamlit.io) que permite explorar visualmente los datos almacenados en `weather.db`.

### Ejecución

```bash
# Con uv
uv run streamlit run app.py

# Con venv activo
streamlit run app.py
```

Se abrirá automáticamente en el navegador en `http://localhost:8501`.

### Dependencia adicional

```bash
# Con uv
uv add streamlit, plotly

# Con pip
pip install streamlit, plotly
```

### Contenido del dashboard

- **Gráficos de temperatura** — evolución de las temperaturas máxima y mínima a lo largo de la semana para cada ubicación.
- **Tabla de datos** — visualización del DataFrame completo con todos los campos de la previsión, filtrable y ordenable directamente desde la interfaz.

---

## Fuente de datos

[Open-Meteo](https://open-meteo.com) es una API meteorológica de código abierto que no requiere registro ni API key para uso no comercial. Utiliza modelos numéricos de predicción como ECMWF, GFS e ICON.

Documentación de la API: https://open-meteo.com/en/docs

---

## Licencia

MIT
