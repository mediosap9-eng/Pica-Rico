"""
Sistema de inventario, costos y recetas para Pica Rico.
Ejecutar con: streamlit run app.py
"""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import logica as L

st.set_page_config(page_title="Pica Rico - Control de Restaurante", page_icon="🌶️", layout="wide")

# ------------------------------------------------------------------ Estilos Visuales Pica Rico (CSS Branding)
st.markdown("""
<style>
    /* Fondo general cálido corporativo */
    .stApp {
        background-color: #ffcc33;
        color: #211333;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #fce38a;
        color: #211333;
    }
    /* Títulos y textos principales */
    h1, h2, h3, h4, h5, h6, span, label, p {
        color: #211333 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    /* Tarjetas de métricas */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 2px solid #211333;
    }
    [data-testid="stMetricValue"] {
        color: #211333 !important;
    }
    /* Botones generales */
    .stButton>button {
        background-color: #211333;
        color: #ffcc33;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #d32f2f;
        color: #ffffff;
    }
    /* Tarjeta de Ticket Térmico */
    .ticket-box {
        background-color: #ffffff;
        color: #211333;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        border: 2px dashed #211333;
        max-width: 400px;
        margin: auto;
    }
</style>
""", unsafe_allow_html=True)

try:
    L.init_db()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()

def money(x):
    return f"S/ {x:,.2f}"

# ------------------------------------------------------------------ Dashboard
def pagina_dashboard():
    st.title("📊 Dashboard - Pica Rico")
    c1, c2 = st.columns(2)
    desde = c1.date_input("Desde", date.today() - timedelta(days=30))
    hasta = c2.date_input("Hasta", date.today())
    k = L.kpis_periodo(desde, hasta)
    objetivo = L.get_cfg("food_cost_objetivo", "30")

    m = st.columns(4)
    m[0].metric("Ventas netas", money(k["ingreso_neto"]))
    m[1].metric("Food cost teórico", f"{k['food_cost_teorico_pct']:.1f}%",
                delta=f"{k['food_cost_teorico_pct'] - objetivo:+.1f} pts vs objetivo", delta_color="inverse")
    m[2].metric("Food cost real (con mermas)", f"{k['food_cost_real_pct']:.1f}%",
                delta=f"{k['food_cost_real_pct'] - k['food_cost_teorico_pct']:+.1f} pts vs teórico",
                delta_color="inverse")
    m[3].metric("Utilidad bruta", money(k["utilidad_bruta"]))
    
    m2 = st.columns(4)
    m2[0].metric("Costo de lo vendido", money(k["cmv_teorico"]))
    m2[1].metric("Merma registrada", money(k["merma_registrada"]))
    m2[2].metric("Faltantes de inventario", money(k["faltante_inventario"]))
    m2[3].metric("Valor del inventario", money(k["valor_inventario"]))

    st.subheader("🚨 Alertas")
    a, b = st.columns(2)
    with a:
        st.markdown("**Stock bajo el mínimo (hay que pedir)**")
        s = L.alertas_stock()
        if s.empty:
            st.success("Todo el stock está sobre el mínimo.")
        else:
            st.dataframe(s, hide_index=True, use_container_width=True)
    with b:
        st.markdown("**Por vencer (estimado desde último ingreso)**")
        v = L.alertas_vencimiento(3)
        if v.empty:
            st.success("Nada por vencer en 3 días.")
        else:
            st.dataframe(v[["nombre", "stock_actual", "unidad_compra", "vence", "dias_restantes"]],
                         hide_index=True, use_container_width=True)

    st.markdown("**Cambios de precio recientes de insumos**")
    var = L.variaciones_precio()
    if var.empty:
        st.info("Aún no hay cambios de precio registrados.")
    else:
        st.dataframe(var, hide_index=True, use_container_width=True,
                     column_config={"variacion_pct": st.column_config.NumberColumn("variación %", format="%.1f%%")})

    st.markdown("**Platos con food cost por encima del objetivo**")
    c = L.costos_recetas()
    if not c.empty:
        c = c[c.food_cost_pct > objetivo]
        if c.empty:
            st.success(f"Todos los platos están por debajo de {objetivo:.0f}%.")
        else:
            st.dataframe(c[["nombre", "costo_porcion", "precio_venta", "food_cost_pct", "precio_sugerido"]]
                         .round(2), hide_index=True, use_container_width=True)


# ------------------------------------------------------------------ Nuevo Módulo: Caja / Ventas Virtual
def pagina_caja_ventas():
    st.title("🌶️ Caja Virtual y Registro de Ventas")
    st.markdown("Registra ventas individuales, menús completos o promociones especiales del día. El sistema descontará automáticamente los insumos en Google Sheets.")

    costos = L.costos_recetas()
    if costos.empty:
        st.warning("Primero debes registrar recetas en el sistema.")
        return

    tab_v1, tab_v2, tab_v3 = st.tabs(["🛒 Venta Rápida / Menú del Día", "📋 Registro por Lote", "🕘 Historial y Tickets"])

    with tab_v1:
        with st.form("form_caja_rapida", clear_on_submit=True):
            st.subheader("Nueva Transacción de Caja")
            c1, c2 = st.columns(2)
            tipo_venta = c1.selectbox("Tipo de Venta", ["Menú completo (Entrada + Segundo + Refresco)", "Solo segundo", "Plato a la carta", "Promoción Especial"])
            
            nombre_promo = ""
            if "Promoción" in tipo_venta or "Menú" in tipo_venta:
                nombre_promo = c2.text_input("Nombre del Banquete / Promoción del Día", placeholder="Ej: Banquete Criollo / Menú Ejecutivo Jueves")
            
            plato_sel = st.selectbox("Seleccionar Plato Base / Principal", costos.nombre.tolist())
            rec_row = costos[costos.nombre == plato_sel].iloc[0]
            
            c3, c4, c5 = st.columns(3)
            cantidad = c3.number_input("Cantidad", 1, 100, 1)
            
            # Precio sugerido según tipo
            precio_sug = float(rec_row.precio_venta)
            if "Menú completo" in tipo_venta:
                precio_sug = 12.00
            elif "Solo segundo" in tipo_venta:
                precio_sug = 9.00
                
            precio_unit = c4.number_input("Precio unitario de venta (S/)", 0.0, value=precio_sug, step=0.5)
            
            tipo_pago = c5.selectbox("Tipo de Pago", ["Efectivo", "Yape", "Plin", "Tarjeta / Transferencia"])
            
            cliente = st.text_input("Nombre del Cliente (Opcional)", "Cliente General")
            fecha_venta = st.date_input("Fecha de venta", date.today())
            
            submitted = st.form_submit_button("🔥 Registrar Venta y Descontar Stock")
            if submitted:
                total_venta = cantidad * precio_unit
                L.registrar_venta(
                    receta_id=int(rec_row.id),
                    cantidad=float(cantidad),
                    fecha=fecha_venta,
                    tipo_venta=tipo_venta,
                    nombre_promocion=nombre_promo,
                    cliente=cliente,
                    tipo_pago=tipo_pago,
                    precio_final_override=precio_unit
                )
                st.success(f"¡Venta registrada con éxito! Total: S/ {total_venta:.2f}. Inventario actualizado en Google Sheets.")
                
                # Generar vista previa de ticket térmico
                st.markdown("### 📄 Vista Previa del Ticket Térmico")
                ticket_html = f"""
                <div class="ticket-box">
                    <h3 style="text-align:center; margin:0;">PICA RICO</h3>
                    <p style="text-align:center; margin:0; font-size:12px;">Sazón Casera y Antojos</p>
                    <hr style="border-top: 1px dashed #211333;">
                    <p><b>Fecha:</b> {fecha_venta} <br>
                    <b>Cliente:</b> {cliente}<br>
                    <b>Tipo Pago:</b> {tipo_pago}</p>
                    <hr style="border-top: 1px dashed #211333;">
                    <p><b>{cantidad}x</b> {plato_sel}<br>
                    <small>({tipo_venta} {f'- ' + nombre_promo if nombre_promo else ''})</small><br>
                    <b>Subtotal:</b> S/ {total_venta:.2f}</p>
                    <hr style="border-top: 1px dashed #211333;">
                    <h3 style="text-align:center; margin:0;">TOTAL: S/ {total_venta:.2f}</h3>
                    <p style="text-align:center; font-size:10px; margin-top:10px;">¡Gracias por su preferencia! Pica Rico 🌶️</p>
                </div>
                """
                st.markdown(ticket_html, unsafe_allow_html=True)
                st.info("💡 Puedes copiar este diseño o enviarlo directamente a través de WhatsApp Web con un cliente.")

    with tab_v2:
        st.subheader("Registro Masivo Diario (Cierre Rápido)")
        fecha_lote = st.date_input("Fecha", date.today(), key="f_lote")
        g = pd.DataFrame({"id": costos.id, "plato": costos.nombre, "vendidos": 0})
        ed = st.data_editor(g, hide_index=True, use_container_width=True, key="grid_ventas_lote",
                            disabled=["id", "plato"],
                            column_config={"vendidos": st.column_config.NumberColumn(min_value=0, step=1)})
        if st.button("✅ Registrar Lote de Ventas"):
            n = 0
            for _, r in ed.iterrows():
                if r.vendidos and r.vendidos > 0:
                    L.registrar_venta(int(r.id), float(r.vendidos), fecha_lote, tipo_venta="Lote Diario")
                    n += 1
            if n:
                st.success(f"Ventas de {n} plato(s) registradas e inventario descontado en Google Sheets.")
            else:
                st.warning("No ingresaste cantidades.")

    with tab_v3:
        st.subheader("Historial de Ventas Registradas")
        h = L.q("ventas")
        if not h.empty:
            st.dataframe(h.sort_values("id", ascending=False).head(100), hide_index=True, use_container_width=True)
        else:
            st.info("Aún no hay ventas registradas.")


# ------------------------------------------------------------------ Proveedores
def pagina_proveedores():
    st.title("🚚 Proveedores")
    df = L.q("proveedores")
    ed = st.data_editor(df, hide_index=True, disabled=["id"], use_container_width=True, key="ed_prov",
                        column_config={"dias_entrega": st.column_config.NumberColumn("días de entrega", min_value=0, step=1)})
    if st.button("💾 Guardar cambios", key="g_prov"):
        for _, r in ed.iterrows():
            L.run_update("proveedores", int(r.id), {
                "nombre": r.nombre, "contacto": r.contacto, "telefono": r.telefono,
                "email": r.email, "dias_entrega": int(r.dias_entrega or 0), "notas": r.notas
            })
        st.success("Guardado en Google Sheets.")
        st.rerun()

    with st.expander("➕ Nuevo proveedor"):
        with st.form("f_prov", clear_on_submit=True):
            c = st.columns(3)
            nombre = c[0].text_input("Nombre *")
            contacto = c[1].text_input("Contacto")
            tel = c[2].text_input("Teléfono")
            c = st.columns(3)
            email = c[0].text_input("Email")
            dias = c[1].number_input("Días de entrega", 0, 60, 1)
            notas = c[2].text_input("Notas...")
            if st.form_submit_button("Agregar") and nombre.strip():
                try:
                    L.run_insert("proveedores", [nombre.strip(), contacto, tel, email, int(dias), notas])
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo agregar: {e}")


# ------------------------------------------------------------------ Insumos
def pagina_insumos():
    st.title("📦 Insumos")
    prov = L.q("proveedores")
    pmap = dict(zip(prov.nombre, prov.id)) if not prov.empty else {}
    imap = {v: k for k, v in pmap.items()}

    df = L.q("insumos")
    if df.empty:
        st.info("Aún no hay insumos. Agrega el primero abajo.")
    else:
        df["proveedor"] = df.proveedor_id.map(imap)
        df["costo_unit_receta"] = L.costo_unit_receta(df.precio_compra, df.factor_conversion, df.merma_pct)
        cols = ["id", "nombre", "categoria", "proveedor", "precio_compra", "unidad_compra", "unidad_receta",
                "factor_conversion", "merma_pct", "costo_unit_receta", "dias_vida", "stock_minimo",
                "stock_actual", "ultimo_ingreso"]
        
        ed = st.data_editor(
            df[cols], hide_index=True, use_container_width=True, key="ed_ins",
            disabled=["id", "costo_unit_receta", "stock_actual", "ultimo_ingreso"],
            column_config={
                "categoria": st.column_config.SelectboxColumn("categoría", options=L.CATEGORIAS),
                "proveedor": st.column_config.SelectboxColumn("proveedor", options=list(pmap)),
                "unidad_compra": st.column_config.SelectboxColumn("u. compra", options=L.UNIDADES),
                "unidad_receta": st.column_config.SelectboxColumn("u. receta", options=L.UNIDADES),
                "precio_compra": st.column_config.NumberColumn("precio compra", min_value=0.0, format="%.3f"),
                "factor_conversion": st.column_config.NumberColumn("factor conv.", min_value=0.0001),
                "merma_pct": st.column_config.NumberColumn("merma %", min_value=0.0, max_value=95.0),
                "costo_unit_receta": st.column_config.NumberColumn("costo x u. receta", format="%.4f"),
                "stock_actual": st.column_config.NumberColumn("stock actual", format="%.2f"),
            })
        if st.button("💾 Guardar cambios", key="g_ins"):
            for _, r in ed.iterrows():
                L.actualizar_precio(int(r.id), float(r.precio_compra))
                L.run_update("insumos", int(r.id), {
                    "nombre": r.nombre, "categoria": r.categoria, "proveedor_id": pmap.get(r.proveedor),
                    "unidad_compra": r.unidad_compra, "unidad_receta": r.unidad_receta,
                    "factor_conversion": float(r.factor_conversion), "merma_pct": float(r.merma_pct),
                    "dias_vida": int(r.dias_vida or 0), "stock_minimo": float(r.stock_minimo or 0)
                })
            st.success("Guardado en Google Sheets.")
            st.rerun()

    with st.expander("➕ Nuevo insumo"):
        with st.form("f_ins", clear_on_submit=True):
            c = st.columns(3)
            nombre = c[0].text_input("Nombre *")
            cat = c[1].selectbox("Categoría", L.CATEGORIAS)
            prv = c[2].selectbox("Proveedor", ["(ninguno)"] + list(pmap))
            c = st.columns(4)
            precio = c[0].number_input("Precio de compra", 0.0, step=0.1, format="%.3f")
            uc = c[1].selectbox("Unidad de compra", L.UNIDADES, index=0)
            ur = c[2].selectbox("Unidad de receta", L.UNIDADES, index=1)
            factor = c[3].number_input("Factor", 0.0001, value=1000.0)
            c = st.columns(4)
            merma = c[0].number_input("Merma %", 0.0, 95.0, 0.0)
            vida = c[1].number_input("Días vida", 0, 3650, 0)
            smin = c[2].number_input("Stock mínimo", 0.0)
            sini = c[3].number_input("Stock inicial", 0.0)
            if st.form_submit_button("Agregar") and nombre.strip():
                try:
                    L.crear_insumo(nombre.strip(), cat, pmap.get(prv), precio, uc, ur, factor, merma, vida, smin, sini)
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo agregar: {e}")


# ------------------------------------------------------------------ Recetas
def pagina_recetas():
    st.title("📖 Recetas y Costos")
    with st.expander("➕ Nuevo plato"):
        with st.form("f_rec", clear_on_submit=True):
            c = st.columns(4)
            nombre = c[0].text_input("Nombre del plato *")
            cat = c[1].text_input("Categoría", "Platos de fondo")
            porc = c[2].number_input("Porciones", 0.25, 1000.0, 1.0, step=1.0)
            precio = c[3].number_input("Precio de venta", 0.0, step=0.5)
            if st.form_submit_button("Crear") and nombre.strip():
                L.run_insert("recetas", [nombre.strip(), cat, porc, precio, ""])
                st.rerun()

    costos = L.costos_recetas()
    if costos.empty:
        st.info("Crea tu primer plato arriba.")
        return

    sel = st.selectbox("Plato", costos.nombre)
    r = costos[costos.nombre == sel].iloc[0]
    rid = int(r.id)
    objetivo = L.get_cfg("food_cost_objetivo", "30")

    m = st.columns(5)
    m[0].metric("Costo total", money(r.costo_total))
    m[1].metric("Costo porción", money(r.costo_porcion))
    m[2].metric("Food cost", f"{r.food_cost_pct:.1f}%")
    m[3].metric("Margen", money(r.margen), delta=f"{r.margen_pct:.0f}%")
    m[4].metric("Sugerido", money(r.precio_sugerido))

    det = L.detalle_receta(rid)
    if not det.empty:
        st.dataframe(det, hide_index=True, use_container_width=True)

    ins = L.q("insumos")
    if not ins.empty:
        with st.form("f_add_item", clear_on_submit=True):
            c = st.columns([3, 2, 1])
            nom = c[0].selectbox("Insumo", ins.nombre)
            cant = c[1].number_input("Cantidad", 0.0, step=10.0)
            if c[2].form_submit_button("Agregar") and cant > 0:
                iid = int(ins[ins.nombre == nom].id.iloc[0])
                L.run_insert("receta_items", [rid, iid, cant])
                st.rerun()


# ------------------------------------------------------------------ Movimientos
def pagina_movimientos():
    st.title("🔄 Movimientos de Inventario")
    ins = L.q("insumos")
    if ins.empty:
        st.info("Primero crea insumos.")
        return
    etiquetas = {f"{r.nombre} ({r.unidad_compra})": int(r.id) for r in ins.itertuples()}
    t1, t2, t3 = st.tabs(["🛒 Compra", "🗑️ Merma", "🕘 Historial"])

    with t1:
        with st.form("f_compra", clear_on_submit=True):
            c = st.columns(4)
            lab = c[0].selectbox("Insumo", list(etiquetas))
            cant = c[1].number_input("Cantidad", 0.0, step=1.0)
            fila = ins[ins.id == etiquetas[lab]].iloc[0]
            precio = c[2].number_input("Precio unitario", 0.0, value=float(fila.precio_compra), format="%.3f")
            fecha = c[3].date_input("Fecha", date.today())
            nota = st.text_input("Nota / Factura")
            if st.form_submit_button("Registrar compra") and cant > 0:
                iid = etiquetas[lab]
                L.actualizar_precio(iid, precio, fecha)
                L.mover(iid, "compra", cant, nota, fecha)
                st.success("Compra registrada en Google Sheets.")

    with t2:
        with st.form("f_merma", clear_on_submit=True):
            c = st.columns(3)
            lab = c[0].selectbox("Insumo", list(etiquetas), key="m_ins")
            cant = c[1].number_input("Cantidad perdida", 0.0, step=0.1)
            motivo = c[2].selectbox("Motivo", ["Vencido", "Error de cocina", "Derrame", "Otro"])
            if st.form_submit_button("Registrar merma") and cant > 0:
                L.mover(etiquetas[lab], "merma", -cant, motivo)
                st.success("Merma registrada.")

    with t3:
        h = L.q("movimientos")
        if not h.empty:
            st.dataframe(h.sort_values("id", ascending=False).head(200), hide_index=True, use_container_width=True)


# ------------------------------------------------------------------ Reportes
def pagina_reportes():
    st.title("📈 Reportes")
    c = st.columns(2)
    desde = c[0].date_input("Desde", date.today() - timedelta(days=30), key="r_d")
    hasta = c[1].date_input("Hasta", date.today(), key="r_h")
    df = L.ingenieria_menu(desde, hasta)
    if df.empty:
        st.info("No hay suficientes datos de ventas en el período.")
    else:
        st.dataframe(df.round(2), hide_index=True, use_container_width=True)


# ------------------------------------------------------------------ Navegación
PAGINAS = {
    "📊 Dashboard": pagina_dashboard,
    "🌶️ Caja y Ventas": pagina_caja_ventas,
    "🔄 Movimientos": pagina_movimientos,
    "📖 Recetas": pagina_recetas,
    "📦 Insumos": pagina_insumos,
    "🚚 Proveedores": pagina_proveedores,
    "📈 Reportes": pagina_reportes,
}

with st.sidebar:
    st.header("🌶️ Pica Rico")
    pag = st.radio("Menú", list(PAGINAS), label_visibility="collapsed")
    st.divider()
    st.subheader("⚙️ Parámetros")
    imp = st.number_input("Impuesto incluido (%)", 0.0, 50.0, L.get_cfg("impuesto_pct", "0"))
    obj = st.number_input("Food cost objetivo (%)", 5.0, 80.0, L.get_cfg("food_cost_objetivo", "30"))
    if imp != L.get_cfg("impuesto_pct", "0") or obj != L.get_cfg("food_cost_objetivo", "30"):
        L.set_cfg("impuesto_pct", imp)
        L.set_cfg("food_cost_objetivo", obj)
        st.rerun()

PAGINAS[pag]()