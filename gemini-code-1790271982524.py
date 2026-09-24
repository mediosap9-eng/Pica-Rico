import pandas as pd
import streamlit as st

st.title("Inventario y Costos - Pica Rico")

try:
  # Forzamos la lectura detectando el separador correcto (coma o punto y coma)
  df = pd.read_csv("Base_Datos_PicaRico - Hoja 1.csv", sep=None, engine="python")
  st.success("¡Datos cargados correctamente desde el archivo local!")
  st.dataframe(df, width="stretch")
except Exception as e:
  st.error(f"Error al cargar el archivo: {e}")
