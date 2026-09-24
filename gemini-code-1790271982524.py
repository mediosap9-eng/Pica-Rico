import pandas as pd
import streamlit as st

st.title("Inventario y Costos - Pica Rico")

# Pega aquí tu enlace CSV publicado de Google Sheets entre las comillas:
url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ73geoKeOV7OMLo5HNC5mDYkHrHB-MKAoHC4wpgePoCEDwILcXR9Xl5tbakixFuCg3kEPXCaQg6qCT/pub?output=csv"

if url_csv:
  df = pd.read_csv(url_csv, sep=",")
  st.dataframe(df)
else:
  st.info(
      "Por favor, ingresa el enlace de tu Google Sheet en formato CSV para"
      " visualizar los datos."
  )
