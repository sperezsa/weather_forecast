import streamlit as st
import pandas as pd
import plotly.express as px
from main import obtener_datos_clima

st.set_page_config(page_title="Histórico de Temperaturas", layout="wide")

st.title("Evolución de Temperaturas por Ciudad 🌤️")

# 1. Cargar los datos (usamos la función del main y aplicamos caché)
@st.cache_data
def cargar_historico():
    return obtener_datos_clima() 

df = cargar_historico()

if not df.empty:
    # 1. calculo de temp media 
    df['temp_media'] = (df['temp_max_c'] + df['temp_min_c']) / 2

    # 2. Asegurar que la columna 'fecha' es tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # 3. Crear Filtro interactivo en la barra lateral para seleccionar ciudades
    st.sidebar.header("Filtros")
    todas_ciudades = df['ciudad'].unique()
    ciudades_seleccionadas = st.sidebar.multiselect(
        "Seleccionar Ciudades", 
        options=todas_ciudades, 
        default=todas_ciudades[:3] # Selecciona las primeras 3 por defecto
    )

    # 4. Filtrar el DataFrame según la selección
    df_filtrado = df[df['ciudad'].isin(ciudades_seleccionadas)]

    if not df_filtrado.empty:
        fig = px.line(
            df_filtrado, 
            x="fecha", 
            y="temp_media", 
            color="ciudad",
            # AQUÍ AÑADIMOS LOS CAMPOS EXTRA
            hover_data={
                "estado": True,            # Muestra el campo 'estado'
                "prob_lluvia_pct": True,   # Muestra el campo 'prob_lluvia_pct'
                "temp_max_c": ":.1f",      # Muestra temp_max con 1 decimal
                "temp_min_c": ":.1f",      # Muestra temp_min con 1 decimal
                "fecha": "|%d %b, %Y",     # Formatea la fecha en el hover
                "temp_media": False        # Podemos ocultar campos si no queremos repetirlos
            },
            title="Evolución de Temperaturas y Estado del Cielo",
            markers=True
        )

        # Si se quiere que el nombre en el recuadro sea más bonito que el nombre de la columna:
        fig.update_traces(
            hovertemplate="<br>".join([
                "<b>%{customdata[0]}</b>", # Aquí asume que 'estado' es el primero en hover_data
                "<b>%{customdata[1]:.0f}%</b>", # Aquí asume que 'prob_lluvia_pct' es el segundo en hover_data
                "Día: %{x}",
                "Media: %{y:.1f}°C",
                "Máx: %{customdata[2]}°C",
                "Mín: %{customdata[3]}°C"
            ])
        )



        # 5. Mostrar el gráfico en Streamlit
        st.plotly_chart(fig, width='stretch')

        # Mostrar tabla de datos completa si se desea
        with st.expander("Ver datos históricos"):
            st.dataframe(df_filtrado.sort_values(by="fecha", ascending=False), width='stretch')
    else:
        st.warning("Selecciona al menos una ciudad en el menú lateral.")

else:
    st.error("No se encontraron datos históricos en la base de datos.")


