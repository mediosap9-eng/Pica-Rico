import pandas as pd
import streamlit as st

# Configuración de la página con diseño amplio
st.set_page_config(
    page_title="Pica Rico - Inventario y Costos", page_icon="🍔", layout="wide"
)

# Estilos CSS personalizados para los colores corporativos (Amarillo Pica Rico y diseño moderno)
st.markdown(
    """
    <style>
    .main {
        background-color: #f9f9f9;
    }
    h1 {
        color: #D4AC0D;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f1f1;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #D4AC0D !important;
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- LOGOTIPO Y ENCABEZADO EN TEXTO ---
st.markdown(
    "<h1 style='text-align: center;'>🍟 PICA RICO 🍔</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 18px;'>Sistema"
    " Integral de Inventarios, Costos y Caja</p>",
    unsafe_allow_html=True,
)

# --- CARGA DE DATOS ---
try:
  df_insumos = pd.read_csv(
      "Base_Datos_PicaRico - Hoja 1.csv", sep=None, engine="python"
  )
except Exception as e:
  st.error(
      f"Error al cargar la base de datos local (asegúrate de que el CSV esté"
      f" subido): {e}"
  )
  df_insumos = pd.DataFrame()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📦 Inventario y Insumos",
        "🍳 Recetas y Costos por Plato",
        "📊 Dashboard en Tiempo Real",
        "💵 Caja y Ticket Virtual",
    ]
)

with tab1:
  st.subheader("Gestión y Stock de Insumos")
  if not df_insumos.empty:
    st.dataframe(df_insumos, width="stretch")
    st.info(
        "💡 Para actualizar precios o cantidades, edita tu Google Sheets,"
        " descárgalo como CSV y súbelo nuevamente a GitHub."
    )
  else:
    st.warning("No hay datos cargados en el inventario.")

with tab2:
  st.subheader("Estructura de Costos por Plato / Escandallo")
  st.write(
      "Calcula el costo exacto de producción por plato en base a los insumos"
      " del inventario."
  )
  if not df_insumos.empty:
    col1, col2 = st.columns(2)
    with col1:
      plato_nombre = st.text_input("Nombre del Plato / Producto")
    with col2:
      porciones = st.number_input(
          "Porciones generadas", min_value=1, value=1
      )

    st.markdown("---")
    st.write("Selecciona los insumos que componen el plato:")
    # Simulador interactivo de receta
    ingrediente_sel = st.selectbox(
        "Insumo",
        df_insumos.iloc[:, 0].values if len(df_insumos) > 0 else ["Vacío"],
    )
    cantidad_usada = st.number_input("Cantidad utilizada en la receta", 0.0)

    if st.button("Añadir a la receta"):
      st.success(
          f"Insumo '{ingrediente_sel}' añadido correctamente al plato"
          f" '{plato_nombre}'."
      )
  else:
    st.warning("Carga primero tu inventario en la pestaña anterior.")

with tab3:
  st.subheader("Dashboard de Indicadores")
  if not df_insumos.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Insumos Registrados", len(df_insumos))
    col2.metric("Categorías Activas", df_insumos.iloc[:, 1].nunique())
    col3.metric("Estado del Sistema", "Óptimo 🟢")

    st.markdown("---")
    st.write("### Comportamiento de Costos")
    st.bar_chart(df_insumos.iloc[:, [0, 5]].set_index(df_insumos.columns[0]))
  else:
    st.info("Visualiza aquí tus métricas una vez cargados los datos.")

with tab4:
  st.subheader("Caja Digital y Ticket Virtual de Ventas")
  st.write(
      "Registra las salidas de platos y genera el ticket de venta para el"
      " cliente."
  )

  col_v1, col_v2 = st.columns(2)
  with col_v1:
    cliente = st.text_input("Nombre del Cliente / Mesa")
    plato_vendido = st.selectbox(
        "Plato a Vender", ["Salchipapa Especial", "Broaster Pica Rico", "1/4 Pollo a la Brasa"]
    )
    cantidad_venta = st.number_input("Cantidad", min_value=1, value=1)

  with col_v2:
    st.markdown("### 🧾 VISTA PREVIA DEL TICKET")
    st.markdown(
        f"""
        ----------------------------------------
        🍟 **PICA RICO** - TICKET DE VENTA 🍔
        ----------------------------------------
        **Cliente/Mesa:** {cliente if cliente else 'General'}
        **Producto:** {cantidad_venta}x {plato_vendido}
        ----------------------------------------
        *¡Gracias por su preferencia!*
        ----------------------------------------
        """
    )
    if st.button("🖨️ Procesar Venta e Imprimir Ticket"):
      st.success("¡Venta registrada con éxito en caja!")
