"""Lunch Microcentro - app local en Streamlit."""
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

from db import init_db, get_conn, costo_plato, get_cfg, is_seeded, USE_TURSO

DB_PATH = Path(__file__).parent / "data" / "lunch.db"

# ============================================================
# Setup
# ============================================================
st.set_page_config(
    page_title="Lunch Microcentro",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Inicializar DB + seed si está vacía (idempotente, funciona local y en Turso)
@st.cache_resource
def _bootstrap():
    init_db()
    with get_conn() as c:
        if not is_seeded(c):
            from seed import run as seed_run
            seed_run()
    return True

_bootstrap()


# ============================================================
# Helpers
# ============================================================
def money(v):
    if v is None:
        return "—"
    return f"${v:,.0f}".replace(",", ".")


def money_2(v):
    if v is None:
        return "—"
    return f"${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return f"{v*100:.1f}%"


def dia_hoy():
    nombres = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
    return nombres[dt.date.today().weekday()]


# CSS custom
st.markdown(
    """
<style>
    .main {padding-top: 1rem;}
    .stMetric {background: #F9FAFB; padding: 1rem; border-radius: 8px; border: 1px solid #E5E7EB;}
    .stMetric label {font-size: 0.85rem; color: #6B7280;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700; color: #1F2937;}
    .stTabs [data-baseweb="tab-list"] {gap: 4px;}
    .stTabs [data-baseweb="tab"] {padding: 8px 16px; border-radius: 6px;}
    h1, h2, h3 {color: #1F2937;}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Sidebar
# ============================================================
with get_conn() as c:
    nombre = get_cfg(c, "nombre_negocio", "Lunch Microcentro")

st.sidebar.markdown(f"### 🍽️ {nombre}")
st.sidebar.caption(f"Hoy: {dt.date.today().strftime('%A %d/%m/%Y')}")
st.sidebar.divider()

page = st.sidebar.radio(
    "Menú",
    [
        "Dashboard",
        "Pedidos",
        "Producción del día",
        "Costos por plato",
        "Recetario",
        "Insumos",
        "Packaging",
        "Gastos",
        "Clientes",
        "Configuración",
    ],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption(f"DB: `{'Turso cloud' if USE_TURSO else DB_PATH.name}`")


# ============================================================
# PAGINA: DASHBOARD
# ============================================================
def page_dashboard():
    st.title("Dashboard")
    st.caption("Resumen ejecutivo de la semana en curso.")

    with get_conn() as c:
        # Pedidos de la semana
        lunes_actual = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
        viernes_actual = lunes_actual + dt.timedelta(days=4)
        pedidos = c.execute(
            "SELECT * FROM pedidos WHERE fecha BETWEEN ? AND ?",
            (lunes_actual, viernes_actual),
        ).fetchall()

        # Conteo por plato/día
        platos = c.execute("SELECT * FROM platos").fetchall()
        plato_by_id = {p["id"]: dict(p) for p in platos}
        plato_by_name = {p["nombre"]: dict(p) for p in platos}

        # Para cada plato, contar cuántas viandas tiene en pedidos de la semana
        dia_to_col = {"LUN": "lunes", "MAR": "martes", "MIE": "miercoles", "JUE": "jueves", "VIE": "viernes"}
        viandas_por_plato = {p["nombre"]: 0 for p in platos}
        for p in pedidos:
            for plato in platos:
                col = dia_to_col.get(plato["dia"])
                if col and p[col] and plato["nombre"] in p[col]:
                    viandas_por_plato[plato["nombre"]] += 1

        # Calcular KPIs
        ingreso_total = 0
        costo_total = 0
        for plato in platos:
            comida, pack, total = costo_plato(c, plato["id"])
            n = viandas_por_plato[plato["nombre"]]
            ingreso_total += n * plato["precio_venta"]
            costo_total += n * total

        ganancia = ingreso_total - costo_total
        margen = (ganancia / ingreso_total) if ingreso_total else 0

        total_gastos = c.execute("SELECT COALESCE(SUM(total),0) as t FROM gastos").fetchone()["t"]

    # KPIs en columnas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pedidos confirmados", sum(viandas_por_plato.values()))
    c2.metric("Ingreso semana", money(ingreso_total))
    c3.metric("Costo semana", money(costo_total))
    c4.metric("Ganancia", money(ganancia), pct(margen) if ingreso_total else None)

    st.divider()

    # Ranking de platos
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Ranking de platos · semana")
        rows = []
        with get_conn() as c:
            for plato in platos:
                comida, pack, total = costo_plato(c, plato["id"])
                n = viandas_por_plato[plato["nombre"]]
                margen_plato = (plato["precio_venta"] - total) / plato["precio_venta"]
                rows.append({
                    "Plato": plato["nombre"],
                    "Día": plato["dia"],
                    "Pedidos": n,
                    "Costo total": total,
                    "Precio": plato["precio_venta"],
                    "Margen": margen_plato,
                    "Ingreso": n * plato["precio_venta"],
                    "Ganancia": n * (plato["precio_venta"] - total),
                })
        df = pd.DataFrame(rows).sort_values("Pedidos", ascending=False)
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Costo total": st.column_config.NumberColumn(format="$%.0f"),
                "Precio": st.column_config.NumberColumn(format="$%.0f"),
                "Margen": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                "Ingreso": st.column_config.NumberColumn(format="$%.0f"),
                "Ganancia": st.column_config.NumberColumn(format="$%.0f"),
            },
        )

    with col_b:
        st.subheader("Compras totales")
        st.metric("Acumulado", money_2(total_gastos))
        with get_conn() as c:
            cats = c.execute(
                "SELECT categoria, SUM(total) as t FROM gastos GROUP BY categoria ORDER BY t DESC"
            ).fetchall()
        for r in cats:
            st.caption(f"**{r['categoria']}** · {money_2(r['t'])}")


# ============================================================
# PAGINA: PEDIDOS
# ============================================================
def page_pedidos():
    st.title("Pedidos")

    tab1, tab2 = st.tabs(["📋 Lista", "➕ Nuevo pedido"])

    with tab1:
        with get_conn() as c:
            pedidos = c.execute(
                """SELECT p.*, cl.nombre as cliente, cl.empresa
                   FROM pedidos p JOIN clientes cl ON cl.id = p.cliente_id
                   ORDER BY p.fecha DESC, p.id DESC"""
            ).fetchall()
        if not pedidos:
            st.info("Todavía no hay pedidos cargados.")
        else:
            df = pd.DataFrame([dict(p) for p in pedidos])
            df = df[["fecha", "cliente", "empresa", "lunes", "martes", "miercoles", "jueves", "viernes", "estado_pago", "observaciones"]]
            df.columns = ["Fecha", "Cliente", "Empresa", "Lun", "Mar", "Mié", "Jue", "Vie", "Pago", "Obs."]
            st.dataframe(df, hide_index=True, use_container_width=True)

    with tab2:
        with get_conn() as c:
            clientes = c.execute("SELECT id, nombre, empresa FROM clientes ORDER BY nombre").fetchall()
            platos = c.execute("SELECT * FROM platos WHERE activo=1 ORDER BY dia").fetchall()

        plato_lun = [p["nombre"] for p in platos if p["dia"] == "LUN"]
        plato_mar = [p["nombre"] for p in platos if p["dia"] == "MAR"]
        plato_mie = [p["nombre"] for p in platos if p["dia"] == "MIE"]
        plato_jue = [p["nombre"] for p in platos if p["dia"] == "JUE"]
        plato_vie = [p["nombre"] for p in platos if p["dia"] == "VIE"]

        with st.form("nuevo_pedido"):
            col1, col2 = st.columns(2)
            with col1:
                if not clientes:
                    st.warning("Cargá al menos un cliente primero (pestaña Clientes).")
                    st.stop()
                cliente_id = st.selectbox(
                    "Cliente",
                    options=[c["id"] for c in clientes],
                    format_func=lambda i: next(f"{cl['nombre']} ({cl['empresa'] or ''})" for cl in clientes if cl["id"] == i),
                )
                fecha = st.date_input("Fecha pedido", value=dt.date.today())
            with col2:
                estado_pago = st.selectbox("Estado de pago", ["Pendiente", "Pagado", "Transferencia", "Efectivo"])

            st.markdown("**Selección por día**")
            cL, cM, cX, cJ, cV = st.columns(5)
            with cL:
                lun = st.selectbox("Lunes", [""] + plato_lun)
            with cM:
                mar = st.selectbox("Martes", [""] + plato_mar)
            with cX:
                mie = st.selectbox("Miércoles", [""] + plato_mie)
            with cJ:
                jue = st.selectbox("Jueves", [""] + plato_jue)
            with cV:
                vie = st.selectbox("Viernes", [""] + plato_vie)

            obs = st.text_area("Observaciones", placeholder="Sin sal, alergias, instrucciones…", height=70)

            submitted = st.form_submit_button("Crear pedido", type="primary", use_container_width=True)
            if submitted:
                with get_conn() as c:
                    c.execute(
                        """INSERT INTO pedidos(cliente_id,fecha,lunes,martes,miercoles,jueves,viernes,observaciones,estado_pago)
                           VALUES(?,?,?,?,?,?,?,?,?)""",
                        (cliente_id, fecha, lun or None, mar or None, mie or None, jue or None, vie or None, obs, estado_pago),
                    )
                st.success("Pedido cargado.")
                st.rerun()


# ============================================================
# PAGINA: PRODUCCIÓN DEL DÍA
# ============================================================
def page_produccion():
    st.title("Producción del día")
    hoy = dia_hoy()
    st.caption(f"Hoy es **{hoy}** ({dt.date.today().strftime('%d/%m/%Y')})")

    fecha_target = st.date_input("Fecha a planificar", value=dt.date.today())
    nombres = {0: "LUN", 1: "MAR", 2: "MIE", 3: "JUE", 4: "VIE"}
    dia_col = {"LUN": "lunes", "MAR": "martes", "MIE": "miercoles", "JUE": "jueves", "VIE": "viernes"}
    dia = nombres.get(fecha_target.weekday())

    if dia is None:
        st.warning("Fin de semana: no hay producción programada.")
        return

    col_name = dia_col[dia]
    with get_conn() as c:
        pedidos = c.execute(
            f"""SELECT p.{col_name} as plato, cl.nombre as cliente, p.observaciones
                FROM pedidos p JOIN clientes cl ON cl.id = p.cliente_id
                WHERE p.fecha = ? AND p.{col_name} IS NOT NULL""",
            (fecha_target,),
        ).fetchall()

        platos = c.execute("SELECT * FROM platos WHERE dia=?", (dia,)).fetchall()

    if not pedidos:
        st.info("Aún no hay pedidos para esta fecha.")
        return

    # Agregar +10% buffer
    st.subheader("Resumen de producción")
    rows = []
    for plato in platos:
        n = sum(1 for p in pedidos if plato["nombre"] in (p["plato"] or ""))
        rows.append({"Plato": plato["nombre"], "Pedidos": n, "A preparar (+10%)": -(-int(n * 1.1) // 1) if n else 0})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.subheader("Lista de cocina")
    for plato in platos:
        clientes_plato = [p for p in pedidos if plato["nombre"] in (p["plato"] or "")]
        if not clientes_plato:
            continue
        with st.expander(f"🍽️ {plato['nombre']} · {len(clientes_plato)} viandas", expanded=True):
            for p in clientes_plato:
                obs = f" — {p['observaciones']}" if p["observaciones"] else ""
                st.markdown(f"- **{p['cliente']}**{obs}")

    # Ingredientes totales necesarios
    st.subheader("Ingredientes a usar (suma de todas las viandas)")
    with get_conn() as c:
        ing_totales = {}
        for plato in platos:
            n = sum(1 for p in pedidos if plato["nombre"] in (p["plato"] or ""))
            if n == 0:
                continue
            cur = c.execute(
                """SELECT i.nombre, i.unidad, r.cantidad_servida, r.rendimiento
                   FROM receta r JOIN insumos i ON i.id=r.insumo_id
                   WHERE r.plato_id=?""",
                (plato["id"],),
            )
            for row in cur:
                cant_cruda = (row["cantidad_servida"] / max(row["rendimiento"], 0.001)) * n
                k = (row["nombre"], row["unidad"])
                ing_totales[k] = ing_totales.get(k, 0) + cant_cruda
    if ing_totales:
        df = pd.DataFrame(
            [{"Ingrediente": k[0], "Cantidad cruda total": round(v, 1), "Unidad": k[1]} for k, v in ing_totales.items()]
        ).sort_values("Ingrediente")
        st.dataframe(df, hide_index=True, use_container_width=True)


# ============================================================
# PAGINA: COSTOS POR PLATO
# ============================================================
def page_costos():
    st.title("Costos por plato")
    st.caption("Costo real = comida (con rendimiento) + packaging. Editá precio o receta y se recalcula solo.")

    with get_conn() as c:
        platos = c.execute("SELECT * FROM platos ORDER BY dia, nombre").fetchall()
        margen_obj = float(get_cfg(c, "margen_objetivo", 0.65))
        margen_min = float(get_cfg(c, "margen_minimo", 0.45))
        rows = []
        for p in platos:
            comida, pack, total = costo_plato(c, p["id"])
            margen = (p["precio_venta"] - total) / p["precio_venta"] if p["precio_venta"] else 0
            estado = "✓ Óptimo" if margen >= margen_obj else ("~ Aceptable" if margen >= margen_min else "! Revisar")
            rows.append({
                "Día": p["dia"], "Plato": p["nombre"],
                "Costo comida": comida, "Costo packaging": pack, "Costo total": total,
                "Precio venta": p["precio_venta"], "Margen": margen, "Estado": estado,
            })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Costo comida": st.column_config.NumberColumn(format="$%.0f"),
            "Costo packaging": st.column_config.NumberColumn(format="$%.0f"),
            "Costo total": st.column_config.NumberColumn(format="$%.0f"),
            "Precio venta": st.column_config.NumberColumn(format="$%.0f"),
            "Margen": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
        },
    )

    st.divider()
    st.subheader("Detalle por plato")
    sel = st.selectbox("Plato", [p["nombre"] for p in platos])
    with get_conn() as c:
        pid = c.execute("SELECT id FROM platos WHERE nombre=?", (sel,)).fetchone()["id"]
        ings = c.execute(
            """SELECT i.nombre, i.unidad, r.cantidad_servida, r.rendimiento, i.precio_unitario
               FROM receta r JOIN insumos i ON i.id=r.insumo_id WHERE r.plato_id=?""",
            (pid,),
        ).fetchall()
        packs = c.execute(
            """SELECT p.nombre, pp.cantidad, p.unidades_por_pack, p.precio_pack
               FROM plato_packaging pp JOIN packaging p ON p.id=pp.packaging_id WHERE pp.plato_id=?""",
            (pid,),
        ).fetchall()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🥗 Ingredientes**")
        ing_rows = []
        for r in ings:
            cruda = r["cantidad_servida"] / max(r["rendimiento"], 0.001)
            costo = cruda * r["precio_unitario"]
            ing_rows.append({
                "Insumo": r["nombre"],
                "Servido": f"{r['cantidad_servida']} {r['unidad']}",
                "Rendimiento": pct(r["rendimiento"]),
                "Cant. cruda": f"{cruda:.1f} {r['unidad']}",
                "Costo": costo,
            })
        st.dataframe(
            pd.DataFrame(ing_rows), hide_index=True, use_container_width=True,
            column_config={"Costo": st.column_config.NumberColumn(format="$%.0f")},
        )
    with col2:
        st.markdown("**📦 Packaging**")
        pack_rows = []
        for r in packs:
            unit = r["precio_pack"] / max(r["unidades_por_pack"], 1)
            costo = unit * r["cantidad"]
            pack_rows.append({
                "Item": r["nombre"], "Cant.": r["cantidad"],
                "Unit.": unit, "Costo": costo,
            })
        st.dataframe(
            pd.DataFrame(pack_rows), hide_index=True, use_container_width=True,
            column_config={
                "Unit.": st.column_config.NumberColumn(format="$%.2f"),
                "Costo": st.column_config.NumberColumn(format="$%.2f"),
            },
        )


# ============================================================
# PAGINA: RECETARIO
# ============================================================
def page_recetario():
    st.title("Recetario")
    st.caption("Editá cantidad servida y rendimiento por ingrediente. El costo se recalcula solo.")

    with get_conn() as c:
        platos = c.execute("SELECT * FROM platos ORDER BY dia, nombre").fetchall()

    sel = st.selectbox("Seleccioná plato", [p["nombre"] for p in platos])

    with get_conn() as c:
        plato = c.execute("SELECT * FROM platos WHERE nombre=?", (sel,)).fetchone()
        ings = c.execute(
            """SELECT r.id as receta_id, i.id as insumo_id, i.nombre, i.unidad,
                      r.cantidad_servida, r.rendimiento, i.precio_unitario
               FROM receta r JOIN insumos i ON i.id=r.insumo_id WHERE r.plato_id=?
               ORDER BY i.nombre""",
            (plato["id"],),
        ).fetchall()
        todos_insumos = c.execute("SELECT id, nombre, unidad FROM insumos ORDER BY nombre").fetchall()

    df_edit = pd.DataFrame([{
        "id": r["receta_id"], "Insumo": r["nombre"], "Unidad": r["unidad"],
        "Servido": r["cantidad_servida"], "Rendimiento": r["rendimiento"],
        "Precio unit.": r["precio_unitario"],
    } for r in ings])

    st.markdown(f"### {plato['nombre']}  ·  Precio venta: {money(plato['precio_venta'])}")

    edited = st.data_editor(
        df_edit,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": None,
            "Unidad": st.column_config.TextColumn(disabled=True),
            "Insumo": st.column_config.TextColumn(disabled=True),
            "Servido": st.column_config.NumberColumn(min_value=0, step=1),
            "Rendimiento": st.column_config.NumberColumn(min_value=0.1, max_value=5.0, step=0.05, format="%.2f"),
            "Precio unit.": st.column_config.NumberColumn(disabled=True, format="$%.2f"),
        },
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Guardar cambios", type="primary"):
            with get_conn() as c:
                for _, row in edited.iterrows():
                    c.execute(
                        "UPDATE receta SET cantidad_servida=?, rendimiento=? WHERE id=?",
                        (float(row["Servido"]), float(row["Rendimiento"]), int(row["id"])),
                    )
            st.success("Receta actualizada.")
            st.rerun()

    # Sumario en vivo
    with get_conn() as c:
        comida, pack, total = costo_plato(c, plato["id"])
    margen = (plato["precio_venta"] - total) / plato["precio_venta"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Costo comida", money(comida))
    c2.metric("Costo packaging", money(pack))
    c3.metric("Costo total", money(total))
    c4.metric("Margen", pct(margen))

    st.divider()
    with st.expander("➕ Agregar ingrediente al plato"):
        with st.form(f"add_ing_{plato['id']}"):
            ins_sel = st.selectbox(
                "Insumo",
                options=[i["id"] for i in todos_insumos],
                format_func=lambda i: next(f"{x['nombre']} ({x['unidad']})" for x in todos_insumos if x["id"] == i),
            )
            cant = st.number_input("Cantidad servida", min_value=0.0, value=100.0, step=1.0)
            rend = st.number_input("Rendimiento (1.0 = sin merma)", min_value=0.1, max_value=5.0, value=1.0, step=0.05)
            if st.form_submit_button("Agregar", type="primary"):
                with get_conn() as c:
                    c.execute(
                        "INSERT INTO receta(plato_id,insumo_id,cantidad_servida,rendimiento) VALUES(?,?,?,?)",
                        (plato["id"], ins_sel, cant, rend),
                    )
                st.rerun()

    with st.expander("🗑️ Eliminar ingrediente"):
        if not ings:
            st.info("Sin ingredientes para eliminar.")
        else:
            del_id = st.selectbox(
                "Ingrediente a eliminar",
                options=[r["receta_id"] for r in ings],
                format_func=lambda i: next(f"{r['nombre']}" for r in ings if r["receta_id"] == i),
            )
            if st.button("Eliminar", type="secondary"):
                with get_conn() as c:
                    c.execute("DELETE FROM receta WHERE id=?", (del_id,))
                st.rerun()


# ============================================================
# PAGINA: INSUMOS
# ============================================================
def page_insumos():
    st.title("Insumos · maestro de ingredientes")
    st.caption("Precio por unidad ($/gr, $/ml, $/unidad). Si cambia el precio acá, se actualiza en todas las recetas.")

    with get_conn() as c:
        rows = c.execute("SELECT * FROM insumos ORDER BY categoria, nombre").fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        st.info("No hay insumos.")
        return

    edited = st.data_editor(
        df[["id", "nombre", "categoria", "unidad", "precio_unitario", "rendimiento_default", "notas"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": None,
            "nombre": "Nombre",
            "categoria": "Categoría",
            "unidad": "Unidad",
            "precio_unitario": st.column_config.NumberColumn("Precio unit.", format="$%.2f", min_value=0),
            "rendimiento_default": st.column_config.NumberColumn("Rendimiento default", format="%.2f", min_value=0.1, max_value=5),
            "notas": "Notas",
        },
        num_rows="dynamic",
    )

    if st.button("💾 Guardar", type="primary"):
        with get_conn() as c:
            for _, row in edited.iterrows():
                if pd.isna(row.get("id")):
                    c.execute(
                        """INSERT INTO insumos(nombre,categoria,unidad,precio_unitario,rendimiento_default,notas)
                           VALUES(?,?,?,?,?,?)""",
                        (row["nombre"], row.get("categoria"), row["unidad"],
                         float(row["precio_unitario"]), float(row.get("rendimiento_default") or 1),
                         row.get("notas")),
                    )
                else:
                    c.execute(
                        """UPDATE insumos SET nombre=?, categoria=?, unidad=?, precio_unitario=?,
                                              rendimiento_default=?, notas=? WHERE id=?""",
                        (row["nombre"], row.get("categoria"), row["unidad"],
                         float(row["precio_unitario"]), float(row.get("rendimiento_default") or 1),
                         row.get("notas"), int(row["id"])),
                    )
        st.success("Insumos actualizados.")
        st.rerun()


# ============================================================
# PAGINA: PACKAGING
# ============================================================
def page_packaging():
    st.title("Packaging · descartables")
    st.caption("Carga unidades por pack y precio. El costo unitario se calcula solo.")

    with get_conn() as c:
        rows = c.execute("SELECT * FROM packaging ORDER BY nombre").fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    df["costo_unit"] = df["precio_pack"] / df["unidades_por_pack"]

    st.dataframe(
        df[["nombre", "unidades_por_pack", "precio_pack", "costo_unit", "notas"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "nombre": "Item",
            "unidades_por_pack": "Unidades por pack",
            "precio_pack": st.column_config.NumberColumn("Precio pack", format="$%.2f"),
            "costo_unit": st.column_config.NumberColumn("Costo unitario", format="$%.2f"),
            "notas": "Notas",
        },
    )

    with st.expander("✏️ Editar packaging"):
        edited = st.data_editor(
            df[["id", "nombre", "unidades_por_pack", "precio_pack", "notas"]],
            hide_index=True,
            use_container_width=True,
            column_config={"id": None},
            num_rows="dynamic",
        )
        if st.button("💾 Guardar packaging", type="primary"):
            with get_conn() as c:
                for _, row in edited.iterrows():
                    if pd.isna(row.get("id")):
                        c.execute(
                            "INSERT INTO packaging(nombre,unidades_por_pack,precio_pack,notas) VALUES(?,?,?,?)",
                            (row["nombre"], int(row["unidades_por_pack"]), float(row["precio_pack"]), row.get("notas")),
                        )
                    else:
                        c.execute(
                            "UPDATE packaging SET nombre=?, unidades_por_pack=?, precio_pack=?, notas=? WHERE id=?",
                            (row["nombre"], int(row["unidades_por_pack"]), float(row["precio_pack"]),
                             row.get("notas"), int(row["id"])),
                        )
            st.rerun()


# ============================================================
# PAGINA: GASTOS
# ============================================================
def page_gastos():
    st.title("Gastos")

    tab1, tab2 = st.tabs(["📋 Lista", "➕ Nuevo gasto"])
    with tab1:
        with get_conn() as c:
            rows = c.execute("SELECT * FROM gastos ORDER BY fecha DESC, id DESC").fetchall()
            cats = c.execute("SELECT categoria, SUM(total) as t FROM gastos GROUP BY categoria ORDER BY t DESC").fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            st.info("Sin gastos cargados.")
            return

        c1, c2 = st.columns([3, 1])
        with c1:
            st.dataframe(
                df[["fecha", "categoria", "producto", "cantidad", "unidad_medida", "precio_unitario", "total", "lugar"]],
                hide_index=True, use_container_width=True,
                column_config={
                    "fecha": "Fecha", "categoria": "Categoría", "producto": "Producto",
                    "cantidad": "Cant.", "unidad_medida": "U.medida",
                    "precio_unitario": st.column_config.NumberColumn("Precio U.", format="$%.2f"),
                    "total": st.column_config.NumberColumn("Total", format="$%.2f"),
                    "lugar": "Lugar",
                },
            )
        with c2:
            st.metric("Total acumulado", money_2(df["total"].sum()))
            st.markdown("**Por categoría**")
            for r in cats:
                st.caption(f"{r['categoria']} · {money_2(r['t'])}")

    with tab2:
        with st.form("nuevo_gasto"):
            c1, c2 = st.columns(2)
            with c1:
                fecha = st.date_input("Fecha", value=dt.date.today())
                cat = st.selectbox("Categoría", [
                    "COMIDA - PROTEÍNA", "COMIDA - LÁCTEOS", "COMIDA - SECOS", "COMIDA - VERDURA",
                    "PACKAGING", "LIMPIEZA", "OTROS"
                ])
                producto = st.text_input("Producto")
            with c2:
                cantidad = st.number_input("Cantidad", min_value=0.0, value=1.0, step=1.0)
                um = st.text_input("Unidad medida", placeholder="500gr, 1L, paq., u")
                lugar = st.text_input("Lugar / proveedor", placeholder="Vital, mayorista, etc")
            c1, c2 = st.columns(2)
            with c1:
                precio_u = st.number_input("Precio unitario", min_value=0.0, value=0.0, step=10.0)
            with c2:
                total = st.number_input("Total", min_value=0.0, value=0.0, step=10.0)

            if st.form_submit_button("Cargar gasto", type="primary", use_container_width=True):
                if not producto or total <= 0:
                    st.error("Cargá producto y total.")
                else:
                    with get_conn() as c:
                        c.execute(
                            """INSERT INTO gastos(fecha,categoria,producto,cantidad,unidad_medida,precio_unitario,total,lugar)
                               VALUES(?,?,?,?,?,?,?,?)""",
                            (fecha, cat, producto, cantidad, um, precio_u, total, lugar),
                        )
                    st.success("Gasto cargado.")
                    st.rerun()


# ============================================================
# PAGINA: CLIENTES
# ============================================================
def page_clientes():
    st.title("Clientes")
    tab1, tab2 = st.tabs(["📋 Lista", "➕ Nuevo cliente"])
    with tab1:
        with get_conn() as c:
            rows = c.execute(
                """SELECT cl.*, COUNT(p.id) as pedidos
                   FROM clientes cl LEFT JOIN pedidos p ON p.cliente_id=cl.id
                   GROUP BY cl.id ORDER BY cl.nombre"""
            ).fetchall()
        if not rows:
            st.info("Sin clientes cargados.")
        else:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(
                df[["nombre", "empresa", "direccion", "telefono", "pedidos", "restricciones", "forma_pago", "cliente_desde"]],
                hide_index=True, use_container_width=True,
                column_config={
                    "nombre": "Nombre", "empresa": "Empresa", "direccion": "Dirección",
                    "telefono": "Tel WA", "pedidos": "Pedidos", "restricciones": "Alergias / restricciones",
                    "forma_pago": "Pago", "cliente_desde": "Desde",
                },
            )

    with tab2:
        with st.form("nuevo_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre y apellido *")
                empresa = st.text_input("Empresa")
                direccion = st.text_input("Dirección")
            with c2:
                telefono = st.text_input("Teléfono (WA)")
                forma_pago = st.selectbox("Forma de pago", ["Pendiente", "Efectivo", "Transferencia", "MercadoPago"])
                restric = st.text_input("Restricciones / alergias")
            if st.form_submit_button("Crear cliente", type="primary"):
                if not nombre.strip():
                    st.error("Nombre es obligatorio.")
                else:
                    with get_conn() as c:
                        c.execute(
                            """INSERT INTO clientes(nombre,empresa,direccion,telefono,forma_pago,restricciones)
                               VALUES(?,?,?,?,?,?)""",
                            (nombre, empresa, direccion, telefono, forma_pago, restric),
                        )
                    st.success("Cliente creado.")
                    st.rerun()


# ============================================================
# PAGINA: CONFIGURACIÓN
# ============================================================
def page_config():
    st.title("Configuración")
    with get_conn() as c:
        rows = c.execute("SELECT * FROM config ORDER BY clave").fetchall()
        platos = c.execute("SELECT * FROM platos ORDER BY dia").fetchall()

    st.subheader("Parámetros del negocio")
    df = pd.DataFrame([dict(r) for r in rows])
    edited = st.data_editor(
        df[["clave", "valor", "descripcion"]],
        hide_index=True, use_container_width=True,
        column_config={"clave": st.column_config.TextColumn(disabled=True)},
    )
    if st.button("💾 Guardar configuración", type="primary"):
        with get_conn() as c:
            for _, row in edited.iterrows():
                c.execute("UPDATE config SET valor=? WHERE clave=?", (str(row["valor"]), row["clave"]))
        st.success("Configuración guardada.")
        st.rerun()

    st.divider()
    st.subheader("Platos y precios")
    df_p = pd.DataFrame([dict(p) for p in platos])
    edited_p = st.data_editor(
        df_p[["id", "nombre", "dia", "precio_venta", "activo"]],
        hide_index=True, use_container_width=True,
        column_config={
            "id": None,
            "nombre": "Plato",
            "dia": st.column_config.SelectboxColumn(options=["LUN", "MAR", "MIE", "JUE", "VIE"]),
            "precio_venta": st.column_config.NumberColumn("Precio venta", format="$%.0f"),
            "activo": st.column_config.CheckboxColumn("Activo"),
        },
    )
    if st.button("💾 Guardar platos", type="primary"):
        with get_conn() as c:
            for _, row in edited_p.iterrows():
                c.execute(
                    "UPDATE platos SET nombre=?, dia=?, precio_venta=?, activo=? WHERE id=?",
                    (row["nombre"], row["dia"], float(row["precio_venta"]),
                     1 if row["activo"] else 0, int(row["id"])),
                )
        st.success("Platos guardados.")
        st.rerun()


# ============================================================
# Router
# ============================================================
pages = {
    "Dashboard": page_dashboard,
    "Pedidos": page_pedidos,
    "Producción del día": page_produccion,
    "Costos por plato": page_costos,
    "Recetario": page_recetario,
    "Insumos": page_insumos,
    "Packaging": page_packaging,
    "Gastos": page_gastos,
    "Clientes": page_clientes,
    "Configuración": page_config,
}
pages[page]()
