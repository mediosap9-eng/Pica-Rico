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

# Carga de datos de inventario
try:
  df_insumos = pd.read_csv(
      "Base_Datos_PicaRico - Hoja 1.csv", sep=None, engine="python"
  )
except Exception as e:
  df_insumos = pd.DataFrame()

# Pestañas principales
tab1, tab2, tab3 = st.tabs(
    ["🍽️ Toma de Pedidos", "📦 Inventario de Insumos", "💵 Caja y Control"]
)

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
    if st.button("Agregar al pedido"):
      st.success("¡Plato agregado correctamente a tu pedido!")

  with st.container():
    st.markdown("### Tus datos de entrega")
    nombre_cli = st.text_input("Nombre")
    celular_cli = st.text_input("Celular (9 dígitos)")
    if st.button("Confirmar Pedido Final"):
      if nombre_cli:
        st.success(
            f"¡Muchas gracias {nombre_cli}! Tu pedido ha sido enviado con"
            " éxito."
        )
      else:
        st.warning("Por favor ingresa tu nombre.")

with tab2:
  st.subheader("Inventario de Insumos y Costos")
  if not df_insumos.empty:
    st.dataframe(df_insumos, width="stretch")
  else:
    st.warning("No hay datos cargados en el inventario.")

with tab3:
  st.subheader("Control de Caja y Ventas")
  col_c1, col_c2, col_c3 = st.columns(3)
  col_c1.metric("Pedidos del Día", "0")
  col_c2.metric("Ingresos Totales", "S/ 0.00")
  col_c3.metric("Estado de Caja", "Abierta 🟢")
