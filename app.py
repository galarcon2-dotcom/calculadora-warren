"""
app.py
Calculadora de Puente de Armadura Tipo Warren — Interfaz Streamlit.
Análisis estructural completo con evaluación de seguridad y diagrama interactivo.
Compatible con Streamlit Cloud · Python 3.11+
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from warren import MATERIALS, HistoryManager, WarrenTruss

# ── CONFIGURACIÓN DE PÁGINA ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Calculadora Warren",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS PERSONALIZADO ─────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Fondo general */
    .stApp { background-color: #F0F4F8; }

    /* Header superior */
    .main-header {
        background: linear-gradient(135deg, #0F2744 0%, #1E3A5F 100%);
        padding: 1.4rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-size: 1.7rem;
        margin: 0;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .main-header p {
        color: #7FB3D3;
        margin: 0.3rem 0 0;
        font-size: 0.88rem;
    }

    /* Tarjetas de métricas */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1E3A5F !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #7FB3D3 !important;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
    }

    /* Botón primario */
    .stButton > button[kind="primary"] {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.55rem 1.4rem;
        border: none;
        width: 100%;
        font-size: 1rem;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
        box-shadow: 0 4px 10px rgba(37,99,235,0.35);
    }

    /* Sugerencias */
    .suggestion-box {
        background: #FFFFFF;
        border-left: 4px solid #2563EB;
        border-radius: 6px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.92rem;
        color: #1E293B;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Info pills en sidebar */
    .info-pill {
        background: #142D4C;
        border: 1px solid #2E5A8A;
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        font-size: 0.82rem;
    }
    .info-pill span { color: #7FB3D3; font-weight: 600; }
    .info-pill p    { color: #FFFFFF; margin: 0; font-weight: 700; }

    /* Separador sidebar */
    .sidebar-divider { border-top: 1px solid #2E5A8A; margin: 0.8rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── INICIALIZACIÓN DE ESTADO ──────────────────────────────────────────────────

if "history_manager" not in st.session_state:
    st.session_state.history_manager = HistoryManager()

if "calc_results" not in st.session_state:
    st.session_state.calc_results = None

if "calc_safety" not in st.session_state:
    st.session_state.calc_safety = None


# ── FUNCIONES AUXILIARES ──────────────────────────────────────────────────────

def color_estado(estado: str) -> str:
    """Devuelve el color HTML según el estado del miembro."""
    return {"SEGURO": "#16A34A", "LIMITE": "#D97706", "FALLA": "#DC2626"}.get(estado, "#64748B")


def badge_estado(estado: str) -> str:
    """Devuelve HTML de una etiqueta de color para el estado."""
    colores = {
        "SEGURO": ("#DCFCE7", "#16A34A"),
        "LIMITE": ("#FEF3C7", "#D97706"),
        "FALLA":  ("#FEE2E2", "#DC2626"),
    }
    bg, fg = colores.get(estado, ("#F1F5F9", "#64748B"))
    return f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:12px;font-weight:700;font-size:0.8rem">{estado}</span>'


def build_truss_figure(
    res: dict[str, Any],
    safety: dict[str, Any],
) -> go.Figure:
    """
    Construye el diagrama interactivo de la armadura Warren con Plotly.
    Verde = Tensión | Rojo = Compresión | Grosor ∝ magnitud de fuerza.
    """
    L, H, n = res["L"], res["H"], res["panels"]
    d = L / n

    top_nodes = [(i * d, H) for i in range(n + 1)]
    bot_nodes = [(i * d, 0) for i in range(n + 1)]

    evals   = {e["id"]: e for e in safety["member_evals"]}
    max_f   = max(abs(e["force"]) for e in safety["member_evals"]) or 1.0

    fig = go.Figure()

    def member_style(mid: str) -> tuple[str, float, str]:
        """Devuelve (color, grosor, texto_hover) para un miembro."""
        e    = evals.get(mid, {})
        f    = abs(e.get("force", 0))
        tipo = e.get("stress_type", "")
        col  = "#16A34A" if tipo == "Tension" else "#DC2626"
        w    = max(1.5, (f / max_f) * 7 + 1)
        hover = (
            f"<b>{e.get('name','')}</b><br>"
            f"Fuerza: {e.get('force',0):.3f} kN<br>"
            f"Tipo: {tipo}<br>"
            f"σ: {e.get('sigma_MPa',0):.2f} MPa<br>"
            f"Ratio: {e.get('ratio',0):.3f}<br>"
            f"Estado: {e.get('status','')}"
        )
        return col, w, hover

    # ── Cordón inferior
    for i in range(n):
        col, w, hover = member_style(f"CI{i+1}")
        x0, y0 = bot_nodes[i]
        x1, y1 = bot_nodes[i + 1]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=col, width=w),
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
        ))

    # ── Cordón superior
    for i in range(n):
        col, w, hover = member_style(f"CS{i+1}")
        x0, y0 = top_nodes[i]
        x1, y1 = top_nodes[i + 1]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=col, width=w),
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
        ))

    # ── Diagonales (patrón W alternado)
    for i in range(n):
        col, w, hover = member_style(f"D{i+1}")
        if i % 2 == 0:
            x0, y0 = bot_nodes[i]
            x1, y1 = top_nodes[i + 1]
        else:
            x0, y0 = top_nodes[i]
            x1, y1 = bot_nodes[i + 1]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=col, width=w),
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
        ))

    # ── Nodos inferiores (azul)
    bx = [p[0] for p in bot_nodes]
    by = [p[1] for p in bot_nodes]
    fig.add_trace(go.Scatter(
        x=bx, y=by,
        mode="markers",
        marker=dict(size=10, color="#2563EB", line=dict(width=2, color="#FFFFFF")),
        name="Nodo inferior",
        hovertemplate="Nodo inferior<br>x = %{x:.2f} m<extra></extra>",
    ))

    # ── Nodos superiores (naranja — puntos de carga)
    tx = [p[0] for p in top_nodes]
    ty = [p[1] for p in top_nodes]
    fig.add_trace(go.Scatter(
        x=tx, y=ty,
        mode="markers",
        marker=dict(size=10, color="#F97316", line=dict(width=2, color="#FFFFFF")),
        name="Nodo superior",
        hovertemplate="Nodo superior<br>x = %{x:.2f} m<extra></extra>",
    ))

    # ── Apoyos (triángulos en los extremos del cordón inferior)
    for xi in [0, L]:
        fig.add_shape(
            type="path",
            path=(
                f"M {xi},{-H*0.04} "
                f"L {xi - d*0.10},{-H*0.14} "
                f"L {xi + d*0.10},{-H*0.14} Z"
            ),
            fillcolor="#475569",
            line=dict(color="#CBD5E1", width=1),
        )

    # ── Línea de rodillo bajo el apoyo derecho
    fig.add_shape(
        type="line",
        x0=L - d * 0.12, y0=-H * 0.16,
        x1=L + d * 0.12, y1=-H * 0.16,
        line=dict(color="#475569", width=3),
    )

    # ── Flechas de carga en nodos intermedios superiores
    P_node = res["P_node"]
    arrow_len = H * 0.18
    for i in range(1, n):
        xc = i * d
        fig.add_annotation(
            x=xc, y=H,
            ax=xc, ay=H + arrow_len,
            xref="x", yref="y",
            axref="x", ayref="y",
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor="#F59E0B",
            text=f"{P_node:.1f} kN",
            font=dict(size=9, color="#92400E"),
            showarrow=True,
        )

    # ── Leyenda manual (líneas de color)
    for col, nombre in [("#16A34A", "Tensión"), ("#DC2626", "Compresión")]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            line=dict(color=col, width=3),
            name=nombre,
        ))

    # ── Anotaciones de dimensiones
    fig.add_annotation(
        x=L / 2, y=-H * 0.28,
        text=f"<b>L = {L} m</b>",
        showarrow=False,
        font=dict(size=11, color="#475569"),
    )
    fig.add_annotation(
        x=-d * 0.5, y=H / 2,
        text=f"<b>H = {H} m</b>",
        showarrow=False,
        font=dict(size=11, color="#475569"),
        textangle=-90,
    )

    # ── Layout
    fig.update_layout(
        title=dict(
            text=f"Armadura Warren  |  L={L} m  ·  H={H} m  ·  {n} paneles",
            font=dict(size=14, color="#1E293B"),
            x=0.5,
        ),
        xaxis=dict(
            range=[-d * 0.8, L + d * 0.8],
            visible=False,
            fixedrange=False,
        ),
        yaxis=dict(
            range=[-H * 0.45, H * 1.55],
            scaleanchor="x",
            scaleratio=1,
            visible=False,
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            font=dict(size=11),
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        height=420,
        hovermode="closest",
    )

    return fig


def run_calculation(
    L: float,
    H: float,
    panels: int,
    P: float,
    area_cm2: float,
    material: str,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Ejecuta el cálculo y guarda en historial. Devuelve (results, safety)."""
    truss  = WarrenTruss(L, H, panels, P)
    safety = truss.evaluate_safety(material=material, section_area_cm2=area_cm2)
    res    = truss.results

    sigma_max = max(e["sigma_MPa"] for e in safety["member_evals"])

    st.session_state.history_manager.save({
        "timestamp":     res["timestamp"],
        "params": {
            "L":        L,
            "H":        H,
            "panels":   panels,
            "P":        P,
            "area_cm2": area_cm2,
            "material": material,
        },
        "verdict":       safety["verdict"],
        "v_level":       safety["v_level"],
        "max_force":     res["max_force"],
        "sigma_max_MPa": round(sigma_max, 2),
        "critical":      safety["critical_members"],
        "suggestions":   safety["suggestions"],
    })

    return res, safety


# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### PARÁMETROS DE ENTRADA")
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    L       = st.number_input("Longitud total L (m)",   min_value=2.0,  max_value=500.0, value=20.0, step=1.0)
    H       = st.number_input("Altura H (m)",           min_value=0.5,  max_value=100.0, value=3.0,  step=0.5)
    panels  = st.number_input("Número de paneles",      min_value=2,    max_value=20,    value=6,    step=1)
    P       = st.number_input("Carga total P (kN)",     min_value=1.0,  max_value=1e6,   value=500.0, step=10.0)
    area    = st.number_input("Área de sección (cm²)",  min_value=1.0,  max_value=5000.0, value=50.0, step=1.0)
    material = st.selectbox("Material", list(MATERIALS.keys()))

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    calcular = st.button("⚡  CALCULAR", type="primary")
    limpiar  = st.button("🗑️  LIMPIAR RESULTADOS")

    if limpiar:
        st.session_state.calc_results = None
        st.session_state.calc_safety  = None
        st.rerun()

    # Información contextual
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    Fy = MATERIALS[material]["Fy_MPa"]
    st.markdown(
        f"""
        <div class="info-pill"><span>Material seleccionado</span><p>Fy = {Fy:.0f} MPa  ·  σ_adm = {Fy/1.67:.1f} MPa</p></div>
        <div class="info-pill"><span>Factor de seguridad</span><p>FS = 1.67 (AISC ASD)</p></div>
        <div class="info-pill"><span>Relación H/L</span><p>{H/L:.3f}  (recomendado 0.08–0.15)</p></div>
        <div class="info-pill"><span>Paneles</span><p>{int(panels)}  (recomendado 4–12)</p></div>
        """,
        unsafe_allow_html=True,
    )


# ── CÁLCULO ───────────────────────────────────────────────────────────────────

if calcular:
    # Validación de entradas
    errores: list[str] = []
    if L <= 0 or H <= 0 or P <= 0:
        errores.append("L, H y P deben ser mayores que cero.")
    if not (2 <= int(panels) <= 20):
        errores.append("El número de paneles debe estar entre 2 y 20.")
    if area <= 0:
        errores.append("El área de sección debe ser mayor que cero.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        with st.spinner("Calculando fuerzas internas..."):
            res, safety = run_calculation(
                float(L), float(H), int(panels),
                float(P), float(area), str(material),
            )
        st.session_state.calc_results = res
        st.session_state.calc_safety  = safety
        st.rerun()


# ── ENCABEZADO ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="main-header">
        <h1>🌉 Puente de Armadura Tipo Warren</h1>
        <p>Análisis Estructural · Esfuerzo Admisible · Método de Secciones · v2.0</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── TABS PRINCIPALES ──────────────────────────────────────────────────────────

tab_resumen, tab_miembros, tab_historial, tab_diagrama = st.tabs([
    "📊 Resumen",
    "📋 Tabla de Miembros",
    "🕒 Historial",
    "📐 Diagrama",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN
# ══════════════════════════════════════════════════════════════════════════════

with tab_resumen:
    res    = st.session_state.calc_results
    safety = st.session_state.calc_safety

    if res is None:
        st.info("👈  Configure los parámetros en el panel lateral y presione **CALCULAR** para ver los resultados.")
    else:
        # Banner de estado
        v_level  = safety["v_level"]
        verdict  = safety["verdict"]
        ico_map  = {"safe": "✅", "warn": "⚠️", "danger": "❌"}

        if v_level == "safe":
            st.success(f"{ico_map[v_level]}  **{verdict}** — Material: {safety['material']}  ·  σ_adm = {safety['allowable_MPa']} MPa  ·  Área = {safety['section_area_cm2']} cm²")
        elif v_level == "warn":
            st.warning(f"{ico_map[v_level]}  **{verdict}** — Material: {safety['material']}  ·  σ_adm = {safety['allowable_MPa']} MPa  ·  Área = {safety['section_area_cm2']} cm²")
        else:
            st.error(f"{ico_map[v_level]}  **{verdict}** — Material: {safety['material']}  ·  σ_adm = {safety['allowable_MPa']} MPa  ·  Área = {safety['section_area_cm2']} cm²")

        # Métricas clave
        sigma_max = max(e["sigma_MPa"] for e in safety["member_evals"])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Ra = Rb",       f"{res['Ra']} kN")
        c2.metric("Fuerza Máx.",   f"{res['max_force']} kN")
        c3.metric("Tensión Máx.",  f"{sigma_max:.1f} MPa")
        c4.metric("N° Miembros",   res["n_members"])
        c5.metric("Áng. Diagonal", f"{res['angle_deg']}°")

        st.markdown("---")

        # Desglose por tipo de miembro
        col_a, col_b, col_c = st.columns(3)

        top_f  = [e for e in safety["member_evals"] if e["type"] == "top_chord"]
        bot_f  = [e for e in safety["member_evals"] if e["type"] == "bot_chord"]
        diag_f = [e for e in safety["member_evals"] if e["type"] == "diagonal"]

        def mini_metric(container, label: str, members: list[dict]) -> None:
            if not members:
                return
            max_r   = max(e["ratio"] for e in members)
            max_s   = max(abs(e["force"]) for e in members)
            n_falla = sum(1 for e in members if e["status"] == "FALLA")
            container.markdown(f"**{label}** ({len(members)} elementos)")
            container.metric("Fuerza máx.", f"{max_s:.2f} kN")
            container.metric("Ratio máx.",  f"{max_r:.3f}")
            if n_falla:
                container.error(f"🔴 {n_falla} miembro(s) en falla")

        mini_metric(col_a, "🔴 Cordón Superior", top_f)
        mini_metric(col_b, "🔵 Cordón Inferior", bot_f)
        mini_metric(col_c, "🟢 Diagonales",      diag_f)

        st.markdown("---")

        # Recuento de estados
        n_safe  = sum(1 for e in safety["member_evals"] if e["color"] == "safe")
        n_warn  = sum(1 for e in safety["member_evals"] if e["color"] == "warn")
        n_dang  = sum(1 for e in safety["member_evals"] if e["color"] == "danger")

        col_s, col_w, col_d = st.columns(3)
        col_s.metric("✅ Seguros",  n_safe)
        col_w.metric("⚠️ Límite",   n_warn)
        col_d.metric("❌ En Falla", n_dang)

        st.markdown("---")

        # Sugerencias de diseño
        st.subheader("💡 Sugerencias de Diseño")
        for sug in safety["suggestions"]:
            if v_level == "danger":
                st.markdown(
                    f'<div class="suggestion-box" style="border-left-color:#DC2626">⚠️  {sug}</div>',
                    unsafe_allow_html=True,
                )
            elif v_level == "warn":
                st.markdown(
                    f'<div class="suggestion-box" style="border-left-color:#D97706">⚡  {sug}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="suggestion-box" style="border-left-color:#16A34A">✅  {sug}</div>',
                    unsafe_allow_html=True,
                )

        # Parámetros del cálculo
        with st.expander("📌 Parámetros del cálculo", expanded=False):
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("Longitud L",    f"{res['L']} m")
            pc1.metric("Altura H",      f"{res['H']} m")
            pc2.metric("Paneles",       res["panels"])
            pc2.metric("Carga total",   f"{res['P_total']} kN")
            pc3.metric("Carga por nodo", f"{res['P_node']} kN")
            pc3.metric("Long. diagonal", f"{res['diag']} m")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLA DE MIEMBROS
# ══════════════════════════════════════════════════════════════════════════════

with tab_miembros:
    res    = st.session_state.calc_results
    safety = st.session_state.calc_safety

    if res is None:
        st.info("Calcule primero para ver la tabla de miembros.")
    else:
        st.subheader("Tabla de Fuerzas en Miembros")

        # Construir DataFrame
        rows = []
        for e in safety["member_evals"]:
            rows.append({
                "ID":              e["id"],
                "Nombre":          e["name"],
                "Tipo":            e["stress_type"],
                "Fuerza (kN)":     round(e["force"], 3),
                "Longitud (m)":    round(e["length"], 3),
                "σ (MPa)":         round(e["sigma_MPa"], 2),
                "σ_adm (MPa)":     round(e["allowable_MPa"], 1),
                "Ratio":           round(e["ratio"], 3),
                "Estado":          e["status"],
            })

        df = pd.DataFrame(rows)

        # Filtros interactivos
        col_f1, col_f2 = st.columns(2)
        tipo_filter   = col_f1.multiselect(
            "Filtrar por tipo",
            ["Tension", "Compresion"],
            default=["Tension", "Compresion"],
        )
        estado_filter = col_f2.multiselect(
            "Filtrar por estado",
            ["SEGURO", "LIMITE", "FALLA"],
            default=["SEGURO", "LIMITE", "FALLA"],
        )

        df_filtered = df[
            df["Tipo"].isin(tipo_filter) &
            df["Estado"].isin(estado_filter)
        ]

        # Colorear filas según estado
        def highlight_estado(row: pd.Series) -> list[str]:
            colores = {
                "SEGURO": "background-color:#DCFCE7; color:#16A34A",
                "LIMITE": "background-color:#FEF3C7; color:#D97706",
                "FALLA":  "background-color:#FEE2E2; color:#DC2626",
            }
            c = colores.get(row["Estado"], "")
            return [c] * len(row)

        st.dataframe(
            df_filtered.style.apply(highlight_estado, axis=1),
            use_container_width=True,
            height=min(450, 40 + len(df_filtered) * 38),
            hide_index=True,
        )

        # Resumen rápido
        n_s = sum(1 for e in safety["member_evals"] if e["color"] == "safe")
        n_w = sum(1 for e in safety["member_evals"] if e["color"] == "warn")
        n_d = sum(1 for e in safety["member_evals"] if e["color"] == "danger")
        st.caption(
            f"Total: {res['n_members']} miembros  ·  "
            f"✅ Seguros: {n_s}  ·  ⚠️ Límite: {n_w}  ·  ❌ Falla: {n_d}  ·  "
            f"Ra = Rb = {res['Ra']} kN  ·  Ángulo diagonal = {res['angle_deg']}°"
        )

        # Descarga CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️  Descargar tabla CSV",
            data=csv,
            file_name=f"warren_miembros_{res['timestamp'].replace(' ','_').replace(':','-')}.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORIAL
# ══════════════════════════════════════════════════════════════════════════════

with tab_historial:
    hm      = st.session_state.history_manager
    records = hm.get_all()

    col_h1, col_h2 = st.columns([6, 1])
    col_h1.subheader("🕒 Historial de Cálculos")
    if col_h2.button("🗑️ Borrar historial"):
        hm.clear()
        st.success("Historial borrado.")
        st.rerun()

    if not records:
        st.info("No hay registros en el historial. Realice un cálculo para comenzar.")
    else:
        hist_rows = []
        for r in records:
            p = r.get("params", {})
            hist_rows.append({
                "Fecha":        r.get("timestamp", ""),
                "L (m)":        p.get("L", ""),
                "H (m)":        p.get("H", ""),
                "Paneles":      p.get("panels", ""),
                "P (kN)":       p.get("P", ""),
                "Área (cm²)":   p.get("area_cm2", ""),
                "Material":     p.get("material", ""),
                "Estado":       r.get("verdict", ""),
                "Fmax (kN)":    r.get("max_force", ""),
                "σmax (MPa)":   r.get("sigma_max_MPa", ""),
            })

        df_hist = pd.DataFrame(hist_rows)

        def highlight_historial(row: pd.Series) -> list[str]:
            colores = {
                "SEGURO":    "background-color:#DCFCE7",
                "PRECAUCION":"background-color:#FEF3C7",
                "PELIGROSO": "background-color:#FEE2E2",
            }
            c = colores.get(row["Estado"], "")
            return [c] * len(row)

        st.dataframe(
            df_hist.style.apply(highlight_historial, axis=1),
            use_container_width=True,
            height=min(500, 50 + len(df_hist) * 38),
            hide_index=True,
        )

        st.caption(f"Total de registros: {len(records)}")

        # Descarga del historial
        csv_hist = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️  Descargar historial CSV",
            data=csv_hist,
            file_name="warren_historial.csv",
            mime="text/csv",
        )

        # Gráfico de evolución del σ_max
        if len(records) > 1:
            st.markdown("---")
            st.subheader("📈 Evolución de σ_max por cálculo")
            fechas  = [r.get("timestamp", f"#{i+1}") for i, r in enumerate(reversed(records))]
            sigmas  = [r.get("sigma_max_MPa", 0) for r in reversed(records)]
            verdicts= [r.get("v_level", "safe") for r in reversed(records)]
            colores = [
                {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}.get(v, "#64748B")
                for v in verdicts
            ]
            fig_hist = go.Figure(go.Bar(
                x=fechas,
                y=sigmas,
                marker_color=colores,
                text=[f"{s:.1f}" for s in sigmas],
                textposition="outside",
                hovertemplate="Fecha: %{x}<br>σmax: %{y:.2f} MPa<extra></extra>",
            ))
            fig_hist.update_layout(
                xaxis_title="Cálculo",
                yaxis_title="σmax (MPa)",
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin=dict(l=10, r=10, t=20, b=80),
                height=320,
            )
            st.plotly_chart(fig_hist, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DIAGRAMA
# ══════════════════════════════════════════════════════════════════════════════

with tab_diagrama:
    res    = st.session_state.calc_results
    safety = st.session_state.calc_safety

    st.subheader("📐 Diagrama de la Armadura")

    if res is None:
        st.info("Calcule primero para visualizar el diagrama.")
    else:
        st.caption(
            "🟢 Verde = Tensión  ·  🔴 Rojo = Compresión  ·  "
            "Grosor proporcional a la magnitud de la fuerza"
        )

        fig_truss = build_truss_figure(res, safety)
        st.plotly_chart(fig_truss, use_container_width=True)

        # Tabla de colores / fuerzas máximas por tipo
        col_d1, col_d2, col_d3 = st.columns(3)

        top_max  = max(abs(e["force"]) for e in safety["member_evals"] if e["type"] == "top_chord")
        bot_max  = max(abs(e["force"]) for e in safety["member_evals"] if e["type"] == "bot_chord")
        diag_max = max(abs(e["force"]) for e in safety["member_evals"] if e["type"] == "diagonal")

        col_d1.metric("Cordón Superior — Fmax", f"{top_max:.2f} kN", help="Generalmente en compresión")
        col_d2.metric("Cordón Inferior — Fmax", f"{bot_max:.2f} kN", help="Generalmente en tensión")
        col_d3.metric("Diagonales — Fmax",      f"{diag_max:.2f} kN")


# ── PIE DE PÁGINA ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.8rem'>"
    "Calculadora de Armadura Tipo Warren · v2.0 · "
    "Método de Secciones · Factor de Seguridad FS = 1.67 (AISC ASD)"
    "</p>",
    unsafe_allow_html=True,
)
