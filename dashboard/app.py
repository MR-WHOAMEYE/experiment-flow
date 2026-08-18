"""
EaaS Platform — Streamlit Multi-Page App Entry Point (Sprint 9 UI Redesign)

Launch with:
    streamlit run dashboard/app.py

Architecture:
    This file is the sole entry point.  It handles:
      - sys.path fix (single place, before any local imports)
      - st.set_page_config  (must be first Streamlit call)
      - Global CSS injection (Inter font, dark theme, glassmorphism)
      - Page registry: st.navigation() + st.Page() with callable pages
      - Session-state page-reference dict so any page can call st.switch_page()
"""
import sys
from pathlib import Path

import streamlit as st

# ── sys.path fix — keep here; must be BEFORE any local imports ───────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Local page modules ────────────────────────────────────────────────────────
from dashboard.pages import (  # noqa: E402
    home,
    create_experiment,
    results_dashboard,
    history,
    settings,
)

# ─────────────────────────────────────────────────────────────────────────────
# App config  (must be the very first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Experiment Flow",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS — dark theme, Inter font, glassmorphism cards
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: #0a0e1a !important;
}
/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1326 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebarNavLink"] {
    color: #64748b !important;
    border-radius: 8px !important;
    margin: 2px 8px !important;
    padding: 8px 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(99,102,241,0.12) !important;
    color: #818cf8 !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(99,102,241,0.18) !important;
    color: #a5b4fc !important;
    border-left: 3px solid #6366f1 !important;
}
[data-testid="stSidebarHeader"] {
    padding: 20px 16px 8px !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    color: #e2e8f0 !important;
    letter-spacing: 0.01em !important;
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #e2e8f0 !important;
    letter-spacing: -0.01em !important;
}
p, li, .stMarkdown p { color: #cbd5e1 !important; }
code { color: #a5b4fc !important; background: rgba(99,102,241,0.12) !important;
       border-radius: 4px !important; padding: 1px 5px !important; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* ── Input widgets ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stMultiselect > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
label, .stRadio label, .stCheckbox label { color: #94a3b8 !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    background: rgba(255,255,255,0.05) !important;
    color: #e2e8f0 !important;
}
.stButton > button:hover {
    border-color: rgba(99,102,241,0.4) !important;
    background: rgba(99,102,241,0.08) !important;
    color: #a5b4fc !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
    color: white !important;
    transform: translateY(-2px) !important;
}

/* ── DataFrames / Tables ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
.stDataFrame > div { background: rgba(255,255,255,0.03) !important; }
thead tr th { background: rgba(99,102,241,0.1) !important; color: #a5b4fc !important; }
tbody tr { background: rgba(255,255,255,0.02) !important; }
tbody tr:hover { background: rgba(99,102,241,0.06) !important; }
tbody tr td { color: #cbd5e1 !important; }

/* ── Alerts ── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
[data-testid="stNotificationContentInfo"]    { background: rgba(6,182,212,0.08)  !important; }
[data-testid="stNotificationContentSuccess"] { background: rgba(16,185,129,0.08) !important; }
[data-testid="stNotificationContentWarning"] { background: rgba(245,158,11,0.08) !important; }
[data-testid="stNotificationContentError"]   { background: rgba(244,63,94,0.08)  !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
}

/* ── Progress bar (file uploader etc.) ── */
.stProgress > div > div { background: #6366f1 !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── Plotly charts ── */
.js-plotly-plot .plotly { border-radius: 12px !important; }

/* ══════════════════════════════════════════════════
   Custom component classes used by page modules
   ══════════════════════════════════════════════════ */

/* Hero section */
@keyframes gradientFlow {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.hero-section {
    background: linear-gradient(-45deg, #0f172a, #1e1b4b, #1a1035, #0f172a, #0a0e1a);
    background-size: 400% 400%;
    animation: gradientFlow 12s ease infinite;
    border-radius: 20px;
    padding: 72px 48px;
    text-align: center;
    margin-bottom: 40px;
    border: 1px solid rgba(99,102,241,0.18);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.05);
}
.hero-eyebrow {
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6366f1;
    margin-bottom: 20px;
}
.hero-title {
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 20px;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 1.1rem;
    color: rgba(255,255,255,0.55);
    line-height: 1.6;
    max-width: 560px;
    margin: 0 auto 8px;
}

/* Glassmorphism card */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

/* Metric card */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(99,102,241,0.25);
}
.metric-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #6366f1;
    line-height: 1.1;
    margin-bottom: 6px;
}
.metric-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Verdict boxes */
.verdict-win {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 14px;
    padding: 20px 28px;
    margin: 16px 0;
}
.verdict-lose {
    background: rgba(244,63,94,0.08);
    border: 1px solid rgba(244,63,94,0.25);
    border-radius: 14px;
    padding: 20px 28px;
    margin: 16px 0;
}
"""

st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Page registry — build once, store in session_state for switch_page()
# ─────────────────────────────────────────────────────────────────────────────
_home_page     = st.Page(home.show,                title="Home",              icon="🏠", default=True,  url_path="home")
_create_page   = st.Page(create_experiment.show,   title="Create Experiment", icon="🧪",                url_path="create")
_results_page  = st.Page(results_dashboard.show,   title="Results",           icon="📊",                url_path="results")
_history_page  = st.Page(history.show,             title="History",           icon="📋",                url_path="history")
_settings_page = st.Page(settings.show,            title="Settings",          icon="⚙️",                url_path="settings")

# Make page references available to every page via session_state
if "pages" not in st.session_state:
    st.session_state.pages = {
        "home":     _home_page,
        "create":   _create_page,
        "results":  _results_page,
        "history":  _history_page,
        "settings": _settings_page,
    }

# ── Sidebar branding ──────────────────────────────────────────────────────────
st.sidebar.markdown(
    "<div style='padding:8px 8px 24px; font-size:1.15rem; font-weight:800;"
    "color:#e2e8f0; letter-spacing:-0.01em'>🔬 Experiment Flow</div>",
    unsafe_allow_html=True,
)
st.sidebar.caption("EaaS Analytics Platform · v1.1.0")
st.sidebar.markdown("---")

# ── Navigation ────────────────────────────────────────────────────────────────
pg = st.navigation(
    [_home_page, _create_page, _results_page, _history_page, _settings_page],
    position="sidebar",
)
pg.run()
