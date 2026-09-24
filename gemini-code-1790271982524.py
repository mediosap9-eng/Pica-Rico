import pandas as pd
import streamlit as st

st.title("Inventario y Costos - Pica Rico")

try:
  # Leemos el archivo CSV subido a la misma carpeta
  df = pd.read_csv("Base_Datos_PicaRico - Hoja 1.csv")
  st.success("¡Datos cargados correctamente desde el archivo local!")
  st.dataframe(df, use_container_width=True)
except Exception as e:
  st.error(f"Error al cargar el archivo: {e}")
