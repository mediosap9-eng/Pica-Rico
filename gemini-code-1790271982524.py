import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Título de tu aplicación de inventario
st.title("Inventario y Costos - Pica Rico")

# Crear la conexión y leer los datos de Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Hoja 1", ttl=0)

# Mostrar la tabla interactiva en la pantalla
st.dataframe(df)
