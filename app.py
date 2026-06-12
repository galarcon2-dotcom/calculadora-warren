# ============================================================
#  app.py  —  Calculadora de Armadura Tipo Warren
#  Interfaz Streamlit — Portada + Calculadora completa
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

from warren import WarrenTruss, HistoryManager, MATERIALS

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Puente Warren — Calculadora",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── ESTILOS GLOBALES ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── fuentes & fondo global ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=Playfair+Display:wght@700;900&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── ocultar decoraciones Streamlit ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; }

  /* ── HOME — hero ── */
  .hero {
    background: linear-gradient(135deg, #0F2744 0%, #1E3A5F 60%, #0A1F38 100%);
    padding: 0;
    border-radius: 0 0 32px 32px;
    min-height: 380px;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse 80% 60% at 70% 50%, rgba(37,99,235,.25) 0%, transparent 70%);
  }
  .hero-inner {
    position: relative; z-index: 2;
    display: flex; align-items: center; justify-content: space-between;
    padding: 60px 80px 60px 80px;
    gap: 40px; flex-wrap: wrap;
  }
  .hero-badge {
    font-size: .72rem; font-weight: 700; letter-spacing: .18em;
    color: #7FB3D3; text-transform: uppercase; margin-bottom: 12px;
  }
  .hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 900; color: #FFFFFF;
    line-height: 1.1; margin: 0 0 16px 0;
  }
  .hero-title span { color: #2563EB; }
  .hero-rule {
    width: 220px; height: 4px;
    background: linear-gradient(90deg,#2563EB,#7FB3D3);
    border-radius: 2px; margin-bottom: 20px;
  }
  .hero-sub {
    color: #94A3B8; font-size: 1rem; line-height: 1.6;
    max-width: 440px; margin-bottom: 0;
  }

  /* ── HOME — pills ── */
  .pills-row {
    background: #0A1F38;
    padding: 28px 80px;
    display: flex; gap: 20px; flex-wrap: wrap;
    border-radius: 0 0 32px 32px;
  }
  .pill {
    background: #142D4C;
    border: 1px solid #2E5A8A;
    border-radius: 12px;
    padding: 14px 22px;
    min-width: 140px; text-align: center;
  }
  .pill-label { color: #7FB3D3; font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
  .pill-value { color: #FFFFFF; font-size: 1.05rem; font-weight: 700; margin-top: 4px; }

  /* ── HOME — enter button ── */
  .enter-wrap { padding: 36px 80px 48px; text-align: center; background: #0A1F38; border-radius: 0 0 32px 32px; }
  .version-lbl { color: #2E5A8A; font-size: .8rem; margin-top: 14px; }

  /* ── HEADER barra calculadora ── */
  .calc-header {
    background: linear-gradient(90deg, #0F2744 0%, #1E3A5F 100%);
    padding: 14px 32px;
    display: flex; align-items: center; justify-content: space-between;
    border-radius: 0 0 16px 16px;
    margin-bottom: 8px;
  }
  .calc-header-title { color: #FFFFFF; font-size: 1.1rem; font-weight: 700; letter-spacing: .05em; }
  .calc-header-sub   { color: #7FB3D3; font-size: .8rem; margin-top: 2px; }

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E3A5F 0%, #0F2744 100%) !important;
  }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stSelectbox label { color: #FFFFFF !important; font-weight: 600; }
  [data-testid="stSidebar"] .stNumberInput input,
  [data-testid="stSidebar"] .stSelectbox select { background: #EAF0FB !important; }
  [data-testid="stSidebar"] .sidebar-title {
    color: #7FB3D3; font-size: .72rem; font-weight: 700;
    letter-spacing: .18em; text-transform: uppercase;
    padding: 18px 0 6px 0;
  }
  [data-testid="stSidebar"] .sidebar-info {
    color: #7FB3D3; font-size: .78rem; line-height: 1.7;
    border-top: 1px solid #2E5A8A; padding-top: 14px; margin-top: 12px;
  }

  /* ── METRIC CARDS ── */
  [data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }
  [data-testid="stMetricLabel"]  { color: #64748B !important; font-size: .78rem !important; }
  [data-testid="stMetricValue"]  { color: #1E3A5F !important; font-size: 1.5rem !important; font-weight: 700 !important; }
  [data-testid="stMetricDelta"]  { font-size: .78rem !important; }

  /* ── TABS ── */
  button[data-baseweb="tab"] { font-weight: 600 !important; font-size: .88rem !important; }
  button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563EB !important;
    border-bottom: 3px solid #2563EB !important;
  }

  /* ── DATAFRAME ── */
  [data-testid="stDataFrame"] table { font-size: .82rem; }

  /* ── VERDICT banner ── */
  .verdict-safe   { background:#DCFCE7; border-left:6px solid #16A34A; padding:16px 24px; border-radius:8px; }
  .verdict-warn   { background:#FEF3C7; border-left:6px solid #D97706; padding:16px 24px; border-radius:8px; }
  .verdict-danger { background:#FEE2E2; border-left:6px solid #DC2626; padding:16px 24px; border-radius:8px; }
  .verdict-title  { font-size:1.5rem; font-weight:800; margin:0; }
  .verdict-sub    { font-size:.88rem; color:#475569; margin-top:4px; }

  /* ── SUGGESTIONS ── */
  .sug-item {
    padding: 10px 16px; border-radius: 8px; margin-bottom: 8px;
    font-size: .88rem; font-weight: 500;
  }
  .sug-safe   { background:#F0FDF4; border:1px solid #BBF7D0; color:#15803D; }
  .sug-warn   { background:#FFFBEB; border:1px solid #FDE68A; color:#92400E; }
  .sug-danger { background:#FFF1F2; border:1px solid #FECDD3; color:#BE123C; }
</style>
""", unsafe_allow_html=True)

# ── ESTADO DE SESIÓN ─────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"
if "calc_done" not in st.session_state:
    st.session_state.calc_done = False
if "results" not in st.session_state:
    st.session_state.results = None
if "safety" not in st.session_state:
    st.session_state.safety = None


# ════════════════════════════════════════════════════════════════════════════
#  PÁGINA: HOME
# ════════════════════════════════════════════════════════════════════════════
def render_home() -> None:
    """Portada de bienvenida con botón de ingreso a la calculadora."""

    # ── SVG miniatura del puente Warren ─────────────────────────────────────
    warren_svg = """
    <svg viewBox="0 0 420 180" xmlns="http://www.w3.org/2000/svg" width="380" height="160">
      <!-- cordón inferior -->
      <line x1="20" y1="130" x2="400" y2="130" stroke="#2563EB" stroke-width="4"/>
      <!-- cordón superior -->
      <line x1="20" y1="50"  x2="400" y2="50"  stroke="#DC2626" stroke-width="4"/>
      <!-- diagonales alternadas (8 paneles) -->
      <line x1="20"  y1="130" x2="67.5" y2="50"  stroke="#16A34A" stroke-width="2.5"/>
      <line x1="67.5" y1="50" x2="115"  y2="130" stroke="#F97316" stroke-width="2.5"/>
      <line x1="115"  y1="130" x2="162.5" y2="50"  stroke="#16A34A" stroke-width="2.5"/>
      <line x1="162.5" y1="50" x2="210"  y2="130" stroke="#F97316" stroke-width="2.5"/>
      <line x1="210"  y1="130" x2="257.5" y2="50"  stroke="#16A34A" stroke-width="2.5"/>
      <line x1="257.5" y1="50" x2="305"  y2="130" stroke="#F97316" stroke-width="2.5"/>
      <line x1="305"  y1="130" x2="352.5" y2="50"  stroke="#16A34A" stroke-width="2.5"/>
      <line x1="352.5" y1="50" x2="400"  y2="130" stroke="#F97316" stroke-width="2.5"/>
      <!-- nodos inferiores -->
      <circle cx="20"   cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="67.5" cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="115"  cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="162.5" cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="210"  cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="257.5" cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="305"  cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="352.5" cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="400"  cy="130" r="6" fill="#7FB3D3" stroke="#0F2744" stroke-width="1.5"/>
      <!-- nodos superiores -->
      <circle cx="20"   cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="67.5" cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="115"  cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="162.5" cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="210"  cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="257.5" cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="305"  cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="352.5" cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <circle cx="400"  cy="50" r="6" fill="#F97316" stroke="#0F2744" stroke-width="1.5"/>
      <!-- apoyos -->
      <polygon points="20,132 10,150 30,150"  fill="#7FB3D3" stroke="#0F2744" stroke-width="1"/>
      <polygon points="400,132 390,150 410,150" fill="#7FB3D3" stroke="#0F2744" stroke-width="1"/>
      <line x1="386" y1="150" x2="414" y2="150" stroke="#7FB3D3" stroke-width="3"/>
      <!-- cargas -->
      <line x1="67.5"  y1="50" x2="67.5"  y2="30" stroke="#F59E0B" stroke-width="2.5" marker-start="url(#arrow)"/>
      <line x1="115"   y1="50" x2="115"   y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <line x1="162.5" y1="50" x2="162.5" y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <line x1="210"   y1="50" x2="210"   y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <line x1="257.5" y1="50" x2="257.5" y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <line x1="305"   y1="50" x2="305"   y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <line x1="352.5" y1="50" x2="352.5" y2="30" stroke="#F59E0B" stroke-width="2.5"/>
      <!-- leyenda -->
      <line x1="20"  y1="168" x2="44"  y2="168" stroke="#2563EB" stroke-width="3"/>
      <text x="48"  y="172" fill="#7FB3D3" font-size="10" font-family="Inter,sans-serif">Cord. inf.</text>
      <line x1="110" y1="168" x2="134" y2="168" stroke="#DC2626" stroke-width="3"/>
      <text x="138" y="172" fill="#7FB3D3" font-size="10" font-family="Inter,sans-serif">Cord. sup.</text>
      <line x1="200" y1="168" x2="224" y2="168" stroke="#16A34A" stroke-width="2.5"/>
      <text x="228" y="172" fill="#7FB3D3" font-size="10" font-family="Inter,sans-serif">Diagonal T</text>
      <line x1="298" y1="168" x2="322" y2="168" stroke="#F97316" stroke-width="2.5"/>
      <text x="326" y="172" fill="#7FB3D3" font-size="10" font-family="Inter,sans-serif">Diagonal C</text>
    </svg>
    """

    # ── bloque hero ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="hero">
      <div class="hero-inner">
        <div>
          <div class="hero-badge">Universidad Cardenal Miguel Obando Bravo · UNICA</div>
          <h1 class="hero-title">Calculadora<br><span>Tipo Warren</span></h1>
          <div class="hero-rule"></div>
          <p class="hero-sub">
            Análisis estructural de armaduras por el método de secciones.<br>
            Evaluación de esfuerzos admisibles, reacciones, fuerzas internas
            y generación automática de sugerencias de diseño.
          </p>
        </div>
        <div style="opacity:.95">{warren_svg}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── pills de características ─────────────────────────────────────────────
    st.markdown("""
    <div class="pills-row">
      <div class="pill">
        <div class="pill-label">Método</div>
        <div class="pill-value">Secciones</div>
      </div>
      <div class="pill">
        <div class="pill-label">Factor de Seguridad</div>
        <div class="pill-value">FS = 1.67</div>
      </div>
      <div class="pill">
        <div class="pill-label">Materiales</div>
        <div class="pill-value">A36 · A572 · Al</div>
      </div>
      <div class="pill">
        <div class="pill-label">Paneles</div>
        <div class="pill-value">2 — 20</div>
      </div>
      <div class="pill">
        <div class="pill-label">Versión</div>
        <div class="pill-value">v2.0</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── botón de ingreso ─────────────────────────────────────────────────────
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        if st.button(
            "▶  Ingresar a la Calculadora",
            key="btn_enter",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "calculator"
            st.rerun()

    st.markdown("""
    <p style='text-align:center; color:#2E5A8A; font-size:.82rem; margin-top:10px;'>
        v2.0 · Armadura Warren simétrica · Proyecto Integrador — Ingeniería
    </p>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  PÁGINA: CALCULADORA
# ════════════════════════════════════════════════════════════════════════════
def render_calculator() -> None:
    """Calculadora principal con sidebar + pestañas."""

    history_mgr = HistoryManager()

    # ── header barra ─────────────────────────────────────────────────────────
    col_title, col_back = st.columns([5, 1])
    with col_title:
        st.markdown("""
        <div class="calc-header">
          <div>
            <div class="calc-header-title">🏗️ PUENTE DE ARMADURA TIPO WARREN</div>
            <div class="calc-header-sub">Análisis Estructural · Esfuerzo Admisible · Historial</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col_back:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("← Portada", key="btn_back"):
            st.session_state.page = "home"
            st.session_state.calc_done = False
            st.rerun()

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Parámetros de Entrada</div>',
                    unsafe_allow_html=True)

        L      = st.number_input("Longitud total L (m)",  min_value=1.0, max_value=500.0,  value=20.0, step=0.5)
        H      = st.number_input("Altura H (m)",          min_value=0.5, max_value=100.0,  value=3.0,  step=0.25)
        panels = st.number_input("Número de paneles",     min_value=2,   max_value=20,      value=6,    step=1)
        P      = st.number_input("Carga total P (kN)",    min_value=1.0, max_value=1e7,     value=500.0,step=10.0)
        area   = st.number_input("Área de sección (cm²)", min_value=1.0, max_value=10000.0, value=50.0, step=1.0)
        mat    = st.selectbox("Material", list(MATERIALS.keys()))

        st.markdown("---")
        calc_btn  = st.button("⚡ CALCULAR",  use_container_width=True, type="primary")
        clear_btn = st.button("🔄 LIMPIAR",   use_container_width=True)

        st.markdown("""
        <div class="sidebar-info">
          Armadura Warren simétrica<br>
          Carga distribuida en nodos superiores<br>
          Método de secciones | FS = 1.67<br>
          Paneles recomendados: 4-12<br>
          Relación H/L ideal: 0.08-0.15
        </div>
        """, unsafe_allow_html=True)

    # ── limpiar ───────────────────────────────────────────────────────────────
    if clear_btn:
        st.session_state.calc_done = False
        st.session_state.results   = None
        st.session_state.safety    = None
        st.rerun()

    # ── calcular ──────────────────────────────────────────────────────────────
    if calc_btn:
        # validaciones
        errors: list[str] = []
        if L  <= 0: errors.append("La longitud L debe ser positiva.")
        if H  <= 0: errors.append("La altura H debe ser positiva.")
        if P  <= 0: errors.append("La carga P debe ser positiva.")
        if area <= 0: errors.append("El área de sección debe ser positiva.")
        if not (2 <= panels <= 20): errors.append("Los paneles deben estar entre 2 y 20.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            truss  = WarrenTruss(float(L), float(H), int(panels), float(P))
            safety = truss.evaluate_safety(material=mat, section_area_cm2=float(area))
            res    = truss.results

            sigma_max = max(e["sigma_MPa"] for e in safety["member_evals"])

            history_mgr.save({
                "timestamp":    res["timestamp"],
                "params":       {"L": L, "H": H, "panels": panels,
                                 "P": P, "area_cm2": area, "material": mat},
                "verdict":      safety["verdict"],
                "v_level":      safety["v_level"],
                "max_force":    res["max_force"],
                "sigma_max_MPa": round(sigma_max, 2),
                "critical":     safety["critical_members"],
                "suggestions":  safety["suggestions"],
            })

            st.session_state.results   = res
            st.session_state.safety    = safety
            st.session_state.calc_done = True
            st.rerun()

    # ── PESTAÑAS ──────────────────────────────────────────────────────────────
    tab_res, tab_mem, tab_hist, tab_diag = st.tabs([
        "📊 Resumen", "📋 Tabla de Miembros", "🕒 Historial", "📐 Diagrama"
    ])

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 1: RESUMEN
    # ──────────────────────────────────────────────────────────────────────────
    with tab_res:
        if not st.session_state.calc_done:
            st.info("ℹ️ Configure los parámetros en el panel lateral y presione **CALCULAR**.")
        else:
            res    = st.session_state.results
            safety = st.session_state.safety
            lv     = safety["v_level"]
            v      = safety["verdict"]

            # banner de veredicto
            ico   = {"safe": "✅", "warn": "⚠️", "danger": "❌"}[lv]
            cls   = {"safe": "verdict-safe", "warn": "verdict-warn", "danger": "verdict-danger"}[lv]
            st.markdown(f"""
            <div class="{cls}">
              <p class="verdict-title">{ico}  {v}</p>
              <p class="verdict-sub">
                Material: {safety['material']} &nbsp;|&nbsp;
                σ_adm = {safety['allowable_MPa']} MPa &nbsp;|&nbsp;
                Área = {safety['section_area_cm2']} cm²
              </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # métricas
            sigma_max = max(e["sigma_MPa"] for e in safety["member_evals"])
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Ra = Rb (kN)",      f"{res['Ra']}")
            c2.metric("Fuerza Máx. (kN)",  f"{res['max_force']}")
            c3.metric("Tensión Máx. (MPa)",f"{sigma_max:.1f}")
            c4.metric("N° Miembros",       f"{res['n_members']}")
            c5.metric("Ángulo Diagonal",   f"{res['angle_deg']}°")

            # conteo de estados
            n_s = sum(1 for e in safety["member_evals"] if e["color"] == "safe")
            n_w = sum(1 for e in safety["member_evals"] if e["color"] == "warn")
            n_d = sum(1 for e in safety["member_evals"] if e["color"] == "danger")

            st.markdown("---")
            ca, cb, cc = st.columns(3)
            ca.metric("✅ Miembros Seguros", n_s)
            cb.metric("⚠️ Miembros Límite",  n_w)
            cc.metric("❌ Miembros en Falla", n_d)

            # parámetros geométricos
            st.markdown("---")
            st.markdown("#### Parámetros Geométricos")
            pg1, pg2, pg3, pg4 = st.columns(4)
            pg1.metric("Longitud total (m)",    res["L"])
            pg2.metric("Altura (m)",            res["H"])
            pg3.metric("Longitud panel d (m)",  res["d"])
            pg4.metric("Longitud diagonal (m)", res["diag"])

            # sugerencias de diseño
            st.markdown("---")
            st.markdown("#### 💡 Sugerencias de Diseño")
            sug_cls = {"safe": "sug-safe", "warn": "sug-warn", "danger": "sug-danger"}[lv]
            for s in safety["suggestions"]:
                st.markdown(f'<div class="sug-item {sug_cls}">{s}</div>',
                            unsafe_allow_html=True)

            # alerta global
            if lv == "safe":
                st.success("✅ La armadura cumple con todos los criterios de esfuerzo admisible.")
            elif lv == "warn":
                st.warning(f"⚠️ Miembros cercanos al límite: {', '.join(safety['warning_members'])}")
            else:
                st.error(f"❌ Miembros en falla: {', '.join(safety['critical_members'])}")

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 2: TABLA DE MIEMBROS
    # ──────────────────────────────────────────────────────────────────────────
    with tab_mem:
        if not st.session_state.calc_done:
            st.info("ℹ️ Calcule primero para ver la tabla de miembros.")
        else:
            safety = st.session_state.safety
            res    = st.session_state.results

            rows = []
            for e in safety["member_evals"]:
                rows.append({
                    "ID":              e["id"],
                    "Nombre":          e["name"],
                    "Tipo":            e["stress_type"],
                    "Fuerza (kN)":     e["force"],
                    "Longitud (m)":    e["length"],
                    "Esfuerzo (MPa)":  e["sigma_MPa"],
                    "Admisible (MPa)": e["allowable_MPa"],
                    "Ratio":           e["ratio"],
                    "Estado":          e["status"],
                })

            df = pd.DataFrame(rows)

            # colorear la columna Estado
            def color_estado(val: str) -> str:
                if val == "FALLA":  return "background-color:#FEE2E2; color:#DC2626; font-weight:700"
                if val == "LÍMITE": return "background-color:#FEF3C7; color:#D97706; font-weight:700"
                return "background-color:#DCFCE7; color:#16A34A; font-weight:700"

            def color_ratio(val: float) -> str:
                if val > 1.0:  return "color:#DC2626; font-weight:700"
                if val > 0.85: return "color:#D97706; font-weight:700"
                return "color:#16A34A"

            styled = (
                df.style
                .applymap(color_estado, subset=["Estado"])
                .applymap(color_ratio,  subset=["Ratio"])
                .format({
                    "Fuerza (kN)":     "{:.3f}",
                    "Longitud (m)":    "{:.3f}",
                    "Esfuerzo (MPa)":  "{:.2f}",
                    "Admisible (MPa)": "{:.1f}",
                    "Ratio":           "{:.3f}",
                })
            )

            st.markdown(f"""
            **Total:** {res['n_members']} miembros &nbsp;|&nbsp;
            Ra = Rb = **{res['Ra']} kN** &nbsp;|&nbsp;
            Ángulo diagonal = **{res['angle_deg']}°**
            """)
            st.dataframe(styled, use_container_width=True, height=500)

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 3: HISTORIAL
    # ──────────────────────────────────────────────────────────────────────────
    with tab_hist:
        h_col1, h_col2 = st.columns([4, 1])
        with h_col1:
            st.markdown("#### 🕒 Historial de Cálculos")
        with h_col2:
            if st.button("🗑️ Borrar historial", key="btn_clear_hist"):
                history_mgr.clear()
                st.success("Historial borrado.")
                st.rerun()

        records = history_mgr.get_all()

        if not records:
            st.info("No hay cálculos guardados aún.")
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

            def color_hist_estado(val: str) -> str:
                if val == "PELIGROSO":  return "background-color:#FEE2E2; color:#DC2626; font-weight:700"
                if val == "PRECAUCIÓN": return "background-color:#FEF3C7; color:#D97706; font-weight:700"
                return "background-color:#DCFCE7; color:#16A34A; font-weight:700"

            st.dataframe(
                df_hist.style.applymap(color_hist_estado, subset=["Estado"]),
                use_container_width=True,
                height=400,
            )

            # descargar historial
            csv = df_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar historial CSV",
                data=csv,
                file_name="historial_warren.csv",
                mime="text/csv",
            )

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 4: DIAGRAMA (Plotly)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_diag:
        if not st.session_state.calc_done:
            st.info("ℹ️ Calcule primero para ver el diagrama de la armadura.")
        else:
            res    = st.session_state.results
            safety = st.session_state.safety
            render_plotly_truss(res, safety)


# ════════════════════════════════════════════════════════════════════════════
#  DIAGRAMA PLOTLY
# ════════════════════════════════════════════════════════════════════════════
def render_plotly_truss(res: dict, safety: dict) -> None:
    """Dibuja la armadura Warren con Plotly: nodos, miembros, apoyos y cargas."""

    L  = res["L"]
    Ht = res["H"]
    n  = res["panels"]
    d  = L / n

    evals_map  = {e["id"]: e for e in safety["member_evals"]}
    max_force  = max(abs(e["force"]) for e in safety["member_evals"]) or 1.0

    top_nodes = [(i * d, Ht) for i in range(n + 1)]
    bot_nodes = [(i * d, 0.0) for i in range(n + 1)]

    fig = go.Figure()

    def member_style(mid: str) -> tuple[str, float]:
        """Retorna (color, linewidth) según tensión/compresión y magnitud."""
        e     = evals_map.get(mid, {})
        force = abs(e.get("force", 0.0))
        width = max(1.5, (force / max_force) * 8)
        color = "#16A34A" if e.get("stress_type") in ("Tensión", "Tension") else "#DC2626"
        return color, width

    def add_member(x0: float, y0: float, x1: float, y1: float,
                   mid: str, label: str) -> None:
        color, width = member_style(mid)
        e = evals_map.get(mid, {})
        hover = (
            f"<b>{label}</b><br>"
            f"Fuerza: {e.get('force', 0):.3f} kN<br>"
            f"Esfuerzo: {e.get('sigma_MPa', 0):.2f} MPa<br>"
            f"Admisible: {e.get('allowable_MPa', 0):.1f} MPa<br>"
            f"Ratio: {e.get('ratio', 0):.3f}<br>"
            f"Estado: <b>{e.get('status', '')}</b>"
        )
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(color=color, width=width),
            hovertemplate=hover,
            name=mid,
            showlegend=False,
        ))

    # cordón inferior
    for i in range(n):
        add_member(bot_nodes[i][0], 0, bot_nodes[i+1][0], 0, f"CI{i+1}", f"Cordón Inferior {i+1}")

    # cordón superior
    for i in range(n):
        add_member(top_nodes[i][0], Ht, top_nodes[i+1][0], Ht, f"CS{i+1}", f"Cordón Superior {i+1}")

    # diagonales
    for i in range(n):
        if i % 2 == 0:
            add_member(bot_nodes[i][0], 0, top_nodes[i+1][0], Ht, f"D{i+1}", f"Diagonal {i+1}")
        else:
            add_member(top_nodes[i][0], Ht, bot_nodes[i+1][0], 0, f"D{i+1}", f"Diagonal {i+1}")

    # nodos inferiores
    fig.add_trace(go.Scatter(
        x=[b[0] for b in bot_nodes],
        y=[0.0]  * len(bot_nodes),
        mode="markers",
        marker=dict(size=10, color="#2563EB", line=dict(color="white", width=2)),
        name="Nodos inferiores",
        hovertemplate="Nodo inferior<br>x = %{x:.2f} m<extra></extra>",
    ))

    # nodos superiores
    fig.add_trace(go.Scatter(
        x=[t[0] for t in top_nodes],
        y=[Ht]  * len(top_nodes),
        mode="markers",
        marker=dict(size=10, color="#F97316", line=dict(color="white", width=2)),
        name="Nodos superiores",
        hovertemplate="Nodo superior<br>x = %{x:.2f} m<extra></extra>",
    ))

    # apoyos — triángulos via shapes
    apoyo_size = Ht * 0.12
    for ax in [0.0, L]:
        # triángulo
        fig.add_shape(type="path",
            path=(f"M {ax} {-apoyo_size*0.15} "
                  f"L {ax - apoyo_size*0.6} {-apoyo_size} "
                  f"L {ax + apoyo_size*0.6} {-apoyo_size} Z"),
            fillcolor="#64748B", line=dict(color="#334155", width=1))
    # línea de apoyo rodillo en el extremo derecho
    fig.add_shape(type="line",
        x0=L - apoyo_size*0.65, y0=-apoyo_size - 0.02*Ht,
        x1=L + apoyo_size*0.65, y1=-apoyo_size - 0.02*Ht,
        line=dict(color="#64748B", width=3))

    # cargas — flechas en nodos interiores superiores
    arrow_len = Ht * 0.25
    for i in range(1, n):
        xc = i * d
        fig.add_annotation(
            x=xc, y=Ht,
            ax=xc, ay=Ht + arrow_len,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True,
            arrowhead=2, arrowsize=1.4, arrowwidth=2.5,
            arrowcolor="#F59E0B",
            text="", standoff=4,
        )

    # anotaciones de dimensiones
    fig.add_annotation(x=L/2, y=-Ht*0.22,
        text=f"L = {L} m", showarrow=False,
        font=dict(size=12, color="#475569"))
    fig.add_annotation(x=-L*0.06, y=Ht/2,
        text=f"H = {Ht} m", showarrow=False,
        font=dict(size=12, color="#475569"), textangle=-90)

    # leyenda manual como traces invisibles
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines",
        line=dict(color="#16A34A", width=4), name="Tensión"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines",
        line=dict(color="#DC2626", width=4), name="Compresión"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
        marker=dict(size=9, color="#2563EB"), name="Nodo inferior"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
        marker=dict(size=9, color="#F97316"), name="Nodo superior"))

    fig.update_layout(
        title=dict(
            text=f"Armadura Warren — {n} paneles | L={L} m | H={Ht} m",
            font=dict(size=15, color="#1E293B"),
            x=0.01,
        ),
        xaxis=dict(
            title="Posición (m)",
            range=[-L*0.10, L*1.08],
            showgrid=True, gridcolor="#E2E8F0",
            zeroline=False,
        ),
        yaxis=dict(
            title="Altura (m)",
            range=[-Ht*0.45, Ht*1.55],
            showgrid=True, gridcolor="#E2E8F0",
            scaleanchor="x", scaleratio=1,
            zeroline=False,
        ),
        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#FFFFFF",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="#F1F5F9", bordercolor="#CBD5E1", borderwidth=1,
        ),
        margin=dict(l=60, r=40, t=60, b=60),
        height=520,
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "🟢 Verde = Tensión &nbsp;|&nbsp; 🔴 Rojo = Compresión "
        "&nbsp;|&nbsp; Grosor proporcional a magnitud de fuerza"
    )


# ════════════════════════════════════════════════════════════════════════════
#  ROUTER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
def main() -> None:
    if st.session_state.page == "home":
        render_home()
    else:
        render_calculator()


if __name__ == "__main__":
    main()
