import streamlit as st
import pandas as pd
import requests
import sqlite3
import os
from ydata_profiling import ProfileReport
from streamlit_ydata_profiling import st_profile_report

# =====================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================
st.set_page_config(
    page_title="Universidades del Mundo",
    page_icon="🌎",
    layout="wide"
)

st.title("🌎 Análisis de Universidades del Mundo")
st.write(
    "Consumo de API, almacenamiento en SQLite, "
    "análisis exploratorio y exportación de reportes HTML."
)

# =====================================
# LISTA DE PAÍSES
# =====================================
paises = [
    "Ecuador", "Argentina", "Brazil", "Chile", "Colombia",
    "Peru", "Mexico", "United States", "Canada", "Spain",
    "France", "Germany", "Italy", "Japan", "China",
    "India", "Australia", "United Kingdom"
]

pais = st.selectbox(
    "🌍 Seleccione un país:",
    paises
)

# =====================================
# FUNCIÓN PARA OBTENER DATOS
# =====================================
@st.cache_data
def obtener_datos(pais):

    url = f"http://universities.hipolabs.com/search?country={pais}"

    respuesta = requests.get(url, timeout=30)
    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos:
        return pd.DataFrame()

    df = pd.DataFrame(datos)

    # Seleccionar columnas
    df = df[
        [
            "name",
            "country",
            "state-province",
            "domains",
            "web_pages"
        ]
    ]

    # Renombrar
    df.columns = [
        "Universidad",
        "País",
        "Provincia",
        "Dominio",
        "Página Web"
    ]

    # Convertir listas a texto
    df["Dominio"] = df["Dominio"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else ""
    )

    df["Página Web"] = df["Página Web"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else ""
    )

    return df


# =====================================
# CONSULTAR UNIVERSIDADES
# =====================================
if st.button("🔍 Consultar universidades"):

    try:
        df = obtener_datos(pais)

        if df.empty:
            st.warning("No se encontraron universidades.")
        else:
            st.session_state["df"] = df
            st.session_state["pais"] = pais

    except requests.exceptions.RequestException as e:
        st.error(f"Error al conectarse con la API:\n{e}")

    except Exception as e:
        st.error(f"Ocurrió un error inesperado:\n{e}")


# =====================================
# MOSTRAR INFORMACIÓN
# =====================================
if "df" in st.session_state:

    df = st.session_state["df"]
    pais_actual = st.session_state["pais"]

    # ---------------------------------
    # DATOS DE LA API
    # ---------------------------------
    st.subheader("📋 Datos obtenidos desde la API")

    st.dataframe(
        df,
        use_container_width=True
    )

    # ---------------------------------
    # MÉTRICAS
    # ---------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total universidades",
        len(df)
    )

    col2.metric(
        "Provincias diferentes",
        df["Provincia"]
        .fillna("Sin información")
        .nunique()
    )

    col3.metric(
        "Páginas web",
        df["Página Web"]
        .ne("")
        .sum()
    )

    # ---------------------------------
    # SQLITE
    # ---------------------------------
    with sqlite3.connect("universidades.db") as conexion:

        df.to_sql(
            "universidades",
            conexion,
            if_exists="replace",
            index=False
        )

        consulta = pd.read_sql_query(
            "SELECT * FROM universidades",
            conexion
        )

    st.success("Datos almacenados correctamente en SQLite.")

    st.subheader("💾 Datos recuperados desde SQLite")

    st.dataframe(
        consulta,
        use_container_width=True
    )

    # ---------------------------------
    # GRÁFICO
    # ---------------------------------
    st.subheader("📊 Top 10 provincias con más universidades")

    provincias = (
        df["Provincia"]
        .fillna("Sin información")
        .value_counts()
        .head(10)
    )

    st.bar_chart(provincias)

    # ---------------------------------
    # PÁGINAS WEB
    # ---------------------------------
    st.subheader("🔗 Sitios web oficiales")

    for _, fila in df.head(10).iterrows():

        pagina = fila["Página Web"]

        if pagina != "":
            st.markdown(
                f"**{fila['Universidad']}**  \n"
                f"{pagina}"
            )

    # ---------------------------------
    # EXPORTAR CSV
    # ---------------------------------
    st.subheader("⬇ Exportar CSV")

    csv = df.to_csv(
        index=False,
        sep=";",
        encoding="utf-8"
    ).encode("utf-8")

    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"universidades_{pais_actual}.csv",
        mime="text/csv"
    )

    # ---------------------------------
    # REPORTE EXPLORATORIO
    # ---------------------------------
    st.subheader("🔍 Reporte Exploratorio Automático")

    if st.button("Generar reporte HTML"):

        with st.spinner(
            "Generando reporte, espere unos segundos..."
        ):

            profile = ProfileReport(
                df,
                title=f"Reporte Universidades - {pais_actual}",
                explorative=True
            )

            # Mostrar reporte en Streamlit
            st_profile_report(profile)

            # Guardar HTML
            nombre_html = (
                f"reporte_universidades_{pais_actual}.html"
            )

            profile.to_file(nombre_html)

            st.success(
                f"Reporte generado correctamente: {nombre_html}"
            )

            # Descargar HTML
            with open(nombre_html, "rb") as archivo:

                st.download_button(
                    label="⬇ Descargar Reporte HTML",
                    data=archivo,
                    file_name=nombre_html,
                    mime="text/html"
                )

            # Mostrar ubicación del archivo
            st.info(
                f"El archivo también se guardó en:\n"
                f"{os.path.abspath(nombre_html)}"
            )

