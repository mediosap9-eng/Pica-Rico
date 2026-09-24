import streamlit as st
import pandas as pd

st.title("Inventario y Costos - Pica Rico")

# Carga de datos directa con Pandas (asegúrate de que tu Google Sheet sea público o usa tu enlace CSV)
# Si prefieres usar un enlace CSV directo, ponlo entre las comillas:
url_csv = ""  # Pega aquí el enlace CSV de tu Google Sheet si lo deseas

if url_csv:
    df = pd.read_csv(url_csv)
    st.dataframe(df)
else:
    st.info("Por favor, ingresa el enlace de tu Google Sheet en formato CSV para visualizar los datos.")
