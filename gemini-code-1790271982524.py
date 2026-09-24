import pandas as pd
import streamlit as st

st.title("Inventario y Costos - Pica Rico")

url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ73geokEOV7OMLo5mDYkHrHB-MKAoHC4wpgePoCEDwILcXR9X15tbakixFuG3kEPXCaQg6qCT/pub?output=csv"

if url_csv:
  try:
    df = pd.read_csv(url_csv)
    st.success("¡Datos cargados correctamente desde Google Sheets!")
    st.dataframe(df, use_container_width=True)
  except Exception as e:
    st.error(f"Error al leer los datos: {e}")
else:
  st.info("Por favor, ingresa el enlace.")
