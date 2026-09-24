"""
Lógica de negocio del sistema de inventario, costos y recetas para Pica Rico.
Adaptado para persistencia en Google Sheets.
"""
from datetime import date
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

UNIDADES = ["kg", "g", "l", "ml", "unidad", "caja", "paquete", "lata",
            "botella", "docena", "bolsa", "porción"]
CATEGORIAS = ["Carnes", "Pescados y mariscos", "Verduras y frutas", "Lácteos y huevos",
              "Secos y granos", "Abarrotes", "Bebidas", "Salsas y condimentos",
              "Panadería", "Descartables", "Otros"]

# ---------------------------------------------------------------- Conexión Google Sheets
def get_gspread_client():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        return client
    else:
        raise Exception("No se encontraron las credenciales 'gcp_service_account' en st.secrets.")

def get_sheet(sheet_name):
    client = get_gspread_client()
    spreadsheet_url = st.secrets.get("google_sheets", {}).get("spreadsheet_url")
    if spreadsheet_url:
        sh = client.open_by_url(spreadsheet_url)
    else:
        sh = client.open("PicaRico_Inventario") # Nombre por defecto en tu Drive
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
        # Inicializar cabeceras según la tabla
        if sheet_name == "config":
            ws.append_row(["clave", "valor"])
        elif sheet_name == "proveedores":
            ws.append_row(["id", "nombre", "contacto", "telefono", "email", "dias_entrega", "notas"])
        elif sheet_name == "insumos":
            ws.append_row(["id", "nombre", "categoria", "proveedor_id", "precio_compra", "unidad_compra", "unidad_receta", "factor_conversion", "merma_pct", "dias_vida", "stock_minimo", "stock_actual", "ultimo_ingreso"])
        elif sheet_name == "historial_precios":
            ws.append_row(["id", "insumo_id", "fecha", "precio"])
        elif sheet_name == "recetas":
            ws.append_row(["id", "nombre", "categoria", "porciones", "precio_venta", "notas"])
        elif sheet_name == "receta_items":
            ws.append_row(["id", "receta_id", "insumo_id", "cantidad"])
        elif sheet_name == "movimientos":
            ws.append_row(["id", "insumo_id", "fecha", "tipo", "cantidad", "costo_unit", "nota"])
        elif sheet_name == "ventas":
            ws.append_row(["id", "receta_id", "fecha", "cantidad", "precio_neto_unit", "costo_unit", "tipo_venta", "nombre_promocion", "cliente", "tipo_pago"])
    return ws

def q(sql_or_table, params=()):
    """Función de compatibilidad para leer tablas desde Google Sheets simulando SQL básico"""
    # Si pasan una consulta simple o el nombre de una tabla
    table_name = sql_or_table.strip().lower()
    if "from " in table_name:
        # Extraer nombre de tabla básico tras FROM
        parts = table_name.split("from ")
        table_part = parts[1].split(" ")[0].split("[\n")[0].strip()
        ws = get_sheet(table_part)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        return df
    else:
        ws = get_sheet(sql_or_table)
        data = ws.get_all_records()
        return pd.DataFrame(data)

def init_db():
    tablas = ["config", "proveedores", "insumos", "historial_precios", "recetas", "receta_items", "movimientos", "ventas"]
    for t in tablas:
        get_sheet(t)
    # Configurar valores por defecto si están vacíos
    df_cfg = q("config")
    if df_cfg.empty or "impuesto_pct" not in df_cfg.values:
        set_cfg("impuesto_pct", "0")
        set_cfg("food_cost_objetivo", "30")

def get_cfg(clave, default="0"):
    df = q("config")
    if df.empty or "clave" not in df.columns:
        return float(default)
    res = df[df.clave == clave]
    if len(res) > 0:
        return float(res.valor.values[0])
    return float(default)

def set_cfg(clave, valor):
    ws = get_sheet("config")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if row.get("clave") == clave:
            ws.update_cell(idx, 2, str(valor))
            return
    ws.append_row([clave, str(valor)])

def run_insert(table, row_data):
    ws = get_sheet(table)
    existing = ws.get_all_records()
    new_id = len(existing) + 1
    # Asegurar que el ID sea el primer elemento
    full_row = [new_id] + list(row_data)
    ws.append_row(full_row)
    return new_id

def run_update(table, id_val, update_dict):
    ws = get_sheet(table)
    data = ws.get_all_records()
    headers = ws.row_values(1)
    for idx, row in enumerate(data, start=2):
        if str(row.get("id")) == str(id_val):
            for col_name, val in update_dict.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    ws.update_cell(idx, col_idx, val)
            return

def run_delete(table, id_val):
    ws = get_sheet(table)
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if str(row.get("id")) == str(id_val):
            ws.delete_rows(idx)
            return

# ---------------------------------------------------------------- Negocio
def costo_unit_receta(precio_compra, factor, merma_pct):
    return precio_compra / factor / (1 - merma_pct / 100.0)

def actualizar_precio(insumo_id, nuevo_precio, fecha=None):
    fecha = (fecha or date.today()).isoformat()
    df_ins = q("insumos")
    fila = df_ins[df_ins.id == int(insumo_id)]
    if fila.empty:
        return False
    precio_actual = float(fila.precio_compra.values[0])
    if abs(precio_actual - float(nuevo_precio)) < 1e-9:
        return False
    run_update("insumos", insumo_id, {"precio_compra": float(nuevo_precio)})
    run_insert("historial_precios", [int(insumo_id), fecha, float(nuevo_precio)])
    return True

def crear_insumo(nombre, categoria, proveedor_id, precio, u_compra, u_receta, factor,
                 merma_pct, dias_vida, stock_min, stock_ini=0.0):
    iid = run_insert("insumos", [nombre, categoria, proveedor_id, precio, u_compra, u_receta, factor,
                                 merma_pct, dias_vida, stock_min, stock_ini, ""])
    run_insert("historial_precios", [iid, date.today().isoformat(), precio])
    return iid

def mover(insumo_id, tipo, cantidad, nota="", fecha=None):
    fecha = (fecha or date.today()).isoformat()
    df_ins = q("insumos")
    fila = df_ins[df_ins.id == int(insumo_id)]
    if fila.empty:
        return
    precio_compra = float(fila.precio_compra.values[0])
    stock_actual = float(fila.stock_actual.values[0])
    
    run_insert("movimientos", [int(insumo_id), fecha, tipo, float(cantidad), precio_compra, nota])
    nuevo_stock = stock_actual + float(cantidad)
    updates = {"stock_actual": nuevo_stock}
    if tipo == "compra":
        updates["ultimo_ingreso"] = fecha
    run_update("insumos", int(insumo_id), updates)

def costos_recetas():
    iva = get_cfg("impuesto_pct", "0")
    objetivo = get_cfg("food_cost_objetivo", "30")
    
    df_recetas = q("recetas")
    df_items = q("receta_items")
    df_insumos = q("insumos")
    
    if df_recetas.empty:
        return pd.DataFrame(columns=["id", "nombre", "categoria", "porciones", "precio_venta", "costo_total", "n_ingredientes", "costo_porcion", "precio_neto", "food_cost_pct", "margen", "margen_pct", "precio_sugerido"])
    
    # Calcular costo por insumo
    if not df_insumos.empty:
        df_insumos["costo_u_receta"] = df_insumos.precio_compra / df_insumos.factor_conversion / (1 - df_insumos.merma_pct / 100.0)
    else:
        df_insumos["costo_u_receta"] = 0
        
    resultados = []
    for _, rec in df_recetas.iterrows():
        rid = rec.id
        items = df_items[df_items.receta_id == rid] if not df_items.empty else pd.DataFrame()
        costo_total = 0
        n_ing = len(items)
        for _, it in items.iterrows():
            ins = df_insumos[df_insumos.id == it.insumo_id]
            if not ins.empty:
                costo_total += float(it.cantidad) * float(ins.costo_u_receta.values[0])
        
        porciones = float(rec.porciones) if rec.porciones > 0 else 1.0
        costo_porcion = costo_total / porciones
        precio_venta = float(rec.precio_venta)
        precio_neto = precio_venta / (1 + iva / 100.0) if iva >= 0 else precio_venta
        fc_pct = (costo_porcion / precio_neto * 100) if precio_neto > 0 else 0.0
        margen = precio_neto - costo_porcion
        margen_pct = (margen / precio_neto * 100) if precio_neto > 0 else 0.0
        precio_sug = costo_porcion / (objetivo / 100.0) * (1 + iva / 100.0) if objetivo > 0 else 0
        
        resultados.append({
            "id": rid,
            "nombre": rec.nombre,
            "categoria": rec.categoria,
            "porciones": porciones,
            "precio_venta": precio_venta,
            "costo_total": costo_total,
            "n_ingredientes": n_ing,
            "costo_porcion": costo_porcion,
            "precio_neto": precio_neto,
            "food_cost_pct": fc_pct,
            "margen": margen,
            "margen_pct": margen_pct,
            "precio_sugerido": precio_sug
        })
    return pd.DataFrame(resultados)

def detalle_receta(receta_id):
    df_items = q("receta_items")
    df_ins = q("insumos")
    items = df_items[df_items.receta_id == int(receta_id)] if not df_items.empty else pd.DataFrame()
    if items.empty:
        return pd.DataFrame(columns=["id", "insumo", "cantidad", "unidad", "costo_unit", "costo_linea"])
    
    res = []
    for _, it in items.iterrows():
        ins = df_ins[df_ins.id == it.insumo_id]
        if not ins.empty:
            i = ins.iloc[0]
            c_unit = float(i.precio_compra) / float(i.factor_conversion) / (1 - float(i.merma_pct) / 100.0)
            c_linea = float(it.cantidad) * c_unit
            res.append({
                "id": it.id,
                "insumo": i.nombre,
                "cantidad": it.cantidad,
                "unidad": i.unidad_receta,
                "costo_unit": c_unit,
                "costo_linea": c_linea
            })
    return pd.DataFrame(res)

def registrar_venta(receta_id, cantidad, fecha=None, tipo_venta="Plato individual", nombre_promocion="", cliente="General", tipo_pago="Efectivo", precio_final_override=None):
    if cantidad <= 0:
        return
    fecha = (fecha or date.today()).isoformat()
    costos = costos_recetas()
    rec = costos[costos.id == int(receta_id)].iloc[0]
    
    p_neto = float(precio_final_override) if precio_final_override is not None else float(rec.precio_neto)
    c_unit = float(rec.costo_porcion)
    
    run_insert("ventas", [int(receta_id), fecha, float(cantidad), p_neto, c_unit, tipo_venta, nombre_promocion, cliente, tipo_pago])
    
    df_items = q("receta_items")
    df_ins = q("insumos")
    items = df_items[df_items.receta_id == int(receta_id)] if not df_items.empty else pd.DataFrame()
    
    for _, it in items.iterrows():
        ins = df_ins[df_ins.id == it.insumo_id]
        if not ins.empty:
            i = ins.iloc[0]
            uso = (cantidad * float(it.cantidad) / float(rec.porciones)
                   / (1 - float(i.merma_pct) / 100.0) / float(i.factor_conversion))
            mover(int(it.insumo_id), "venta", -uso, f"Venta {cantidad:g} x {rec.nombre} ({tipo_venta})", date.fromisoformat(fecha))

def kpis_periodo(desde, hasta):
    d, h = desde.isoformat(), hasta.isoformat()
    v = q("ventas")
    if not v.empty and "fecha" in v.columns:
        v["fecha_dt"] = pd.to_datetime(v.fecha).dt.date
        v_per = v[(v.fecha_dt >= desde) & (v.fecha_dt <= hasta)]
    else:
        v_per = pd.DataFrame(columns=["cantidad", "precio_neto_unit", "costo_unit"])
        
    ingreso = float((v_per.cantidad * v_per.precio_neto_unit).sum()) if not v_per.empty else 0.0
    cmv = float((v_per.cantidad * v_per.costo_unit).sum()) if not v_per.empty else 0.0
    
    mm = q("movimientos")
    if not mm.empty and "fecha" in mm.columns:
        mm["fecha_dt"] = pd.to_datetime(mm.fecha).dt.date
        mm_per = mm[(mm.fecha_dt >= desde) & (mm.fecha_dt <= hasta)]
    else:
        mm_per = pd.DataFrame(columns=["tipo", "cantidad", "costo_unit"])
        
    merma_reg = 0.0
    faltante = 0.0
    if not mm_per.empty:
        for _, r in mm_per.iterrows():
            if r.tipo in ["merma", "ajuste"] and float(r.cantidad) < 0:
                val = -float(r.cantidad) * float(r.costo_unit)
                if r.tipo == "merma":
                    merma_reg += val
                else:
                    faltante += val
                    
    ins = q("insumos")
    inv = float((ins.stock_actual * ins.precio_compra).sum()) if not ins.empty else 0.0
    
    return {
        "ingreso_neto": ingreso,
        "cmv_teorico": cmv,
        "food_cost_teorico_pct": (cmv / ingreso * 100) if ingreso else 0.0,
        "merma_registrada": merma_reg,
        "faltante_inventario": faltante,
        "food_cost_real_pct": ((cmv + merma_reg + faltante) / ingreso * 100) if ingreso else 0.0,
        "utilidad_bruta": ingreso - cmv - merma_reg - faltante,
        "valor_inventario": inv,
    }

def alertas_stock():
    ins = q("insumos")
    if ins.empty:
        return pd.DataFrame()
    prov = q("proveedores")
    if not prov.empty:
        df = ins.merge(prov, left_on="proveedor_id", right_on="id", suffixes=("", "_prov"), how="left")
    else:
        df = ins.copy()
        df["nombre_prov"] = "-"
        df["dias_entrega"] = 0
        
    alertas = df[(df.stock_actual <= df.stock_minimo) & (df.stock_minimo > 0)]
    return alertas

def alertas_vencimiento(dias_alerta=3):
    ins = q("insumos")
    if ins.empty or "dias_vida" not in ins.columns:
        return pd.DataFrame()
    df = ins[(ins.dias_vida > 0) & (ins.ultimo_ingreso != "") & (ins.stock_actual > 0)].copy()
    if df.empty:
        return df
    df["vence"] = pd.to_datetime(df.ultimo_ingreso) + pd.to_timedelta(df.dias_vida, unit="D")
    df["dias_restantes"] = (df.vence - pd.Timestamp(date.today())).dt.days
    df["vence"] = df.vence.dt.date
    return df[df.dias_restantes <= dias_alerta].sort_values("dias_restantes")

def variaciones_precio():
    hp = q("historial_precios")
    ins = q("insumos")
    if hp.empty or ins.empty:
        return pd.DataFrame()
    # Último y penúltimo precio por insumo
    res = []
    for iid, grupo in hp.groupby("insumo_id"):
        grupo = grupo.sort_values("id")
        if len(grupo) >= 2:
            ant = grupo.iloc[-2].precio
            act = grupo.iloc[-1].precio
            fecha = grupo.iloc[-1].fecha
            nombre_ins = ins[ins.id == iid].nombre.values
            if len(nombre_ins) > 0:
                res.append({
                    "nombre": nombre_ins[0],
                    "precio_anterior": ant,
                    "precio_actual": act,
                    "fecha": fecha,
                    "variacion_pct": (act / ant - 1) * 100
                })
    if not res:
        return pd.DataFrame()
    df_res = pd.DataFrame(res)
    return df_res.sort_values("variacion_pct", ascending=False)

def ingenieria_menu(desde, hasta):
    v = q("ventas")
    r = q("recetas")
    if v.empty or r.empty:
        return pd.DataFrame()
    v["fecha_dt"] = pd.to_datetime(v.fecha).dt.date
    v_per = v[(v.fecha_dt >= desde) & (v.fecha_dt <= hasta)]
    if v_per.empty:
        return pd.DataFrame()
        
    agrupado = v_per.groupby("receta_id").agg(
        vendidas=("cantidad", "sum"),
        ingreso=("precio_neto_unit", lambda x: (x * v_per.loc[x.index, "cantidad"]).sum()),
        margen_unit=("precio_neto_unit", lambda x: ((x - v_per.loc[x.index, "costo_unit"]).sum() / len(x)))
    ).reset_index()
    
    df = agrupado.merge(r, left_on="receta_id", right_on="id")
    if df.empty:
        return pd.DataFrame()
        
    umbral_pop = 0.7 * (1 / len(df)) * 100
    df["popularidad_pct"] = df.vendidas / df.vendidas.sum() * 100
    margen_prom = (df.margen_unit * df.vendidas).sum() / df.vendidas.sum()

    def clase(row):
        pop, mar = row.popularidad_pct >= umbral_pop, row.margen_unit >= margen_prom
        return ("⭐ Estrella" if pop and mar else "🐴 Caballo (popular, poco margen)" if pop
                else "🧩 Rompecabezas (buen margen, poco pedido)" if mar else "🐕 Perro")
    df["clasificacion"] = df.apply(clase, axis=1)
    return df.sort_values("ingreso", ascending=False)
