import pandas as pd
import streamlit as st

st.title("Inventario y Costos - Pica Rico")

# Enlace CSV de Google Sheets
url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ73geokEOV7OMLo5mDYkHrHB-MKAoHC4wpgePoCEDwILcXR9X15tbakixFuG3kEPXCaQg6qCT/pub?output=csv"

if url_csv:
  try:
    # Intentamos leer normalmente
    df = pd.read_csv(url_csv)
    # Si detecta que hay una sola columna, forzamos la división por comas
    if len(df.columns) == 1:
      df = pd.read_csv(url_csv, sep=';')

    st.success('¡Datos cargados con éxito!')
    st.dataframe(df, use_container_width=True)
  except Exception as e:
    st.error(f'Error al procesar los datos: {e}')
else:
  st.info('Por favor, ingresa el enlace de tu Google Sheet.')
