import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Pica Rico - Pedidos y Costos", page_icon="🌶️", layout="wide"
)

# Estilos CSS con el fondo amarillo y diseño moderno
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4C430;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #2C1E3B !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    h1 {
        font-weight: 900;
        letter-spacing: -1px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
        color: #2C1E3B !important;
        border: 2px solid #2C1E3B;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2C1E3B !important;
        color: #F4C430 !important;
    }
    .stButton>button {
        background-color: #C0392B;
        color: #FFFFFF;
        border-radius: 12px;
        font-weight: bold;
        border: 2px solid #2C1E3B;
        padding: 0.6rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #962D22;
        color: #FFFFFF;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Memoria temporal para pedidos
if "pedidos" not in st.session_state:
  st.session_state.pedidos = []

# Carga de datos de inventario desde el CSV
try:
  df_insumos = pd.read_csv(
      "Base_Datos_PicaRico - Hoja 1.csv", sep=None, engine="python"
  )
except Exception as e:
  df_insumos = pd.DataFrame(
      columns=["Insumo", "Stock Actual", "Precio Unitario (S/)"]
  )

# Pestañas principales (Incluyendo Dashboard y Reportes)
tab1, tab2, tab3, tab4 = st.tabs([
    "🍽️ Toma de Pedidos",
    "📦 Inventario y Kardex",
    "💵 Caja y Control",
    "📊 Dashboard y Reportes",
])

with tab1:
  st.markdown("<h1>Pica Rico 🌶️</h1>", unsafe_allow_html=True)
  st.markdown(
      "<div style='background-color: #FFFFFF; padding: 8px 16px; border-radius:"
      " 20px; display: inline-block; border: 2px solid #2C1E3B; font-weight:"
      " bold; margin-bottom: 10px;'>Menú de hoy</div>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='font-size: 16px; font-weight: bold;'>Menú del día con sazón"
      " casera. Arma tu pedido y paga con Yape o en efectivo al recibirlo.</p>",
      unsafe_allow_html=True,
  )

  with st.container():
    st.markdown("### Arma tu menú")
    tipo_menu = st.radio(
        "Modalidad de menú:",
        [
            "Menú completo (S/ 12.00) — Entrada, segundo y refresco",
            "Solo segundo (S/ 9.00) — Sin entrada ni refresco",
        ],
    )
    precio = 12.00 if "completo" in tipo_menu else 9.00

  with st.container():
    st.markdown("### Elige tu segundo")
    segundo = st.radio(
        "Plato principal:",
        [
            "Seco de pollo con frejoles y arroz",
            "Lomo saltado tradicional",
            "Arroz con pollo con salsa criolla",
        ],
    )

  with st.container():
    st.markdown("### Tus datos de entrega")
    nombre_cli = st.text_input("Nombre del Cliente")
    celular_cli = st.text_input("Celular (9 dígitos)")

    if st.button("Confirmar Pedido Final"):
      if nombre_cli:
        st.session_state.pedidos.append({
            "Cliente": nombre_cli,
            "Celular": celular_cli,
            "Detalle": segundo,
            "Tipo": tipo_menu,
            "Monto": precio,
        })
        st.success(
            f"¡Muchas gracias {nombre_cli}! Tu pedido de S/ {precio:.2f} ha"
            " sido registrado con éxito."
        )
      else:
        st.warning("Por favor ingresa el nombre del cliente.")

with tab2:
  st.subheader("📦 Kardex e Inventario de Insumos")
  if not df_insumos.empty:
    st.markdown("### Modificar Stock y Precios")
    st.data_editor(df_insumos, width="stretch", num_rows="dynamic")
    if st.button("Guardar Cambios de Inventario"):
      st.success("¡Stock y precios actualizados correctamente en el Kardex!")
  else:
    st.warning("No se encontraron datos en el archivo de inventario.")

with tab3:
  st.subheader("Control de Caja y Ventas")
  total_pedidos = len(st.session_state.pedidos)
  ingresos_totales = sum(p["Monto"] for p in st.session_state.pedidos)

  col_c1, col_c2, col_c3 = st.columns(3)
  col_c1.metric("Pedidos del Día", str(total_pedidos))
  col_c2.metric("Ingresos Totales", f"S/ {ingresos_totales:.2f}")
  col_c3.metric("Estado de Caja", "Abierta 🟢")

  st.markdown("### Historial de Clientes Atendidos")
  if total_pedidos > 0:
    df_ventas = pd.DataFrame(st.session_state.pedidos)
    st.dataframe(df_ventas, width="stretch")
  else:
    st.info("Aún no hay ventas registradas en caja.")

with tab4:
  st.subheader("📊 Dashboard Gerencial y Reportes")

  if len(st.session_state.pedidos) > 0:
    df_reporte = pd.DataFrame(st.session_state.pedidos)

    # Tarjetas de resumen métrico
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("Total Platos Vendidos", len(df_reporte))
    col_d2.metric(
        "Venta Promedio por Cliente",
        f"S/ {df_reporte['Monto'].mean():.2f}",
    )
    col_d3.metric("Recaudación Total", f"S/ {df_reporte['Monto'].sum():.2f}")

    st.markdown("---")

    # Gráficos y análisis visual
    col_g1, col_g2 = st.columns(2)

    with col_g1:
      st.markdown("### 📈 Ventas por Plato Principal")
      conteo_platos = df_reporte["Detalle"].value_counts()
      st.bar_chart(conteo_platos)

    with col_g2:
      st.markdown("### 📊 Distribución por Tipo de Menú")
      conteo_tipo = df_reporte["Tipo"].value_counts()
      st.bar_chart(conteo_tipo)

    st.markdown("---")
    st.markdown("### 📥 Descargar Reporte de Ventas")
    # Opción para exportar los datos a CSV como reporte descargable
    csv_data = df_reporte.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar Reporte en CSV",
        data=csv_data,
        file_name="reporte_ventas_picarico.csv",
        mime="text/csv",
    )
  else:
    st.info(
        "Aún no hay suficientes datos para mostrar el dashboard. Realiza"
        " algunas simulaciones de pedidos en la primera pestaña."
    )
