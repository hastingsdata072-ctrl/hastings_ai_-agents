"""
Linda Afya Health Assistant
Main Streamlit application entry point.

Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from i18n.translations import t

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Linda Afya Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state defaults ────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "page" not in st.session_state:
    st.session_state.page = "home"

lang = st.session_state.lang

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default sidebar toggle & sidebar completely */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }

    /* Remove default top padding */
    .block-container { padding-top: 0rem !important; }
    header[data-testid="stHeader"] { display: none; }

    /* ── Top navbar ── */
    .topnav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #006633 0%, #004d26 100%);
        padding: 10px 24px;
        border-radius: 0 0 12px 12px;
        margin-bottom: 16px;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .topnav-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        text-decoration: none;
    }
    .topnav-brand span.sub {
        font-size: 0.72rem;
        font-weight: normal;
        opacity: 0.8;
        display: block;
        line-height: 1;
    }
    .topnav-links {
        display: flex;
        gap: 6px;
        align-items: center;
    }
    .nav-btn {
        background: rgba(255,255,255,0.12);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 0.82rem;
        cursor: pointer;
        text-decoration: none;
        transition: background 0.2s;
        white-space: nowrap;
    }
    .nav-btn:hover { background: rgba(255,255,255,0.25); }
    .nav-btn.active {
        background: white;
        color: #006633 !important;
        font-weight: bold;
        border-color: white;
    }
    .nav-lang {
        background: #BB0000;
        color: white !important;
        border: none;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 0.82rem;
        cursor: pointer;
        margin-left: 10px;
    }
    .nav-lang:hover { background: #990000; }

    /* ── Cards ── */
    .feature-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        height: 155px;
        transition: box-shadow 0.2s;
    }
    .feature-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

    /* ── Metric ── */
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: bold !important; }

    /* ── Primary button colour ── */
    .stButton > button[kind="primary"] {
        background: #006633 !important;
        border: none;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover { background: #004d26 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper — set page & rerun ─────────────────────────────────────────────────
def nav_to(page_key):
    st.session_state.page = page_key
    st.rerun()


# ── Top navigation bar (HTML) — display only ─────────────────────────────────
page = st.session_state.page
lang = st.session_state.lang

nav_labels = {
    "home":         ("🏠 Home",               "🏠 Nyumbani"),
    "triage":       ("🩺 Symptom Checker",     "🩺 Ukaguzi wa Dalili"),
    "clinic":       ("🏥 Clinic Locator",      "🏥 Tafuta Kliniki"),
    "immunization": ("💉 Immunization",        "💉 Chanjo"),
    "chat":         ("💬 Health Chat",         "💬 Mazungumzo"),
}

def nav_label(key):
    idx = 0 if lang == "en" else 1
    return nav_labels[key][idx]

# Render navbar HTML (visual only)
links_html = ""
for key in ["home", "triage", "clinic", "immunization", "chat"]:
    active_cls = "active" if page == key else ""
    links_html += f'<span class="nav-btn {active_cls}">{nav_label(key)}</span>'

lang_toggle_label = "🇰🇪 Kiswahili" if lang == "en" else "🇬🇧 English"

st.markdown(f"""
<div class="topnav">
    <div class="topnav-brand">
        <span style="font-size:1.8rem">🏥</span>
        <div>
            Linda Afya
            <span class="sub">Health Assistant · MoH Aligned</span>
        </div>
    </div>
    <div class="topnav-links">
        {links_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Actual navigation buttons (invisible, overlaid via Streamlit columns) ─────
# We render real Streamlit buttons in a top row that triggers rerun
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, _, lang_col = st.columns(
    [1.2, 1.6, 1.5, 1.4, 1.4, 2, 1.2]
)

with nav_col1:
    if st.button("🏠 Home" if lang == "en" else "🏠 Nyumbani",
                 key="nav_home", use_container_width=True):
        nav_to("home")

with nav_col2:
    if st.button("🩺 Symptom Checker" if lang == "en" else "🩺 Dalili",
                 key="nav_triage", use_container_width=True):
        nav_to("triage")

with nav_col3:
    if st.button("🏥 Clinic Locator" if lang == "en" else "🏥 Kliniki",
                 key="nav_clinic", use_container_width=True):
        nav_to("clinic")

with nav_col4:
    if st.button("💉 Immunization" if lang == "en" else "💉 Chanjo",
                 key="nav_imm", use_container_width=True):
        nav_to("immunization")

with nav_col5:
    if st.button("💬 Health Chat" if lang == "en" else "💬 Mazungumzo",
                 key="nav_chat", use_container_width=True):
        nav_to("chat")

with lang_col:
    if st.button(lang_toggle_label, key="lang_toggle", use_container_width=True):
        st.session_state.lang = "sw" if lang == "en" else "en"
        st.rerun()

st.divider()

# ── Re-read after possible language toggle ────────────────────────────────────
lang = st.session_state.lang
page = st.session_state.page


# ── HOME ──────────────────────────────────────────────────────────────────────
if page == "home":
    st.markdown(f"## {t('home_welcome', lang)}")
    st.markdown(t("home_desc", lang))
    st.markdown("")

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        (col1, "🩺", t("home_card_triage", lang),      t("home_card_triage_desc", lang),      "triage"),
        (col2, "🏥", t("home_card_clinic", lang),       t("home_card_clinic_desc", lang),       "clinic"),
        (col3, "💉", t("home_card_immunization", lang), t("home_card_immunization_desc", lang), "immunization"),
        (col4, "💬", t("home_card_chat", lang),         t("home_card_chat_desc", lang),         "chat"),
    ]
    for col, icon, title, desc, target in cards:
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-weight:bold;margin:8px 0 4px 0">{title}</div>
                <div style="font-size:0.82rem;color:#555">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            if st.button(
                f"Open {title}" if lang == "en" else f"Fungua {title}",
                key=f"home_btn_{target}",
                use_container_width=True,
            ):
                nav_to(target)

    st.divider()
    st.warning(t("home_disclaimer", lang))
    st.markdown("""
    <div style="background:#BB0000;color:white;padding:12px 20px;border-radius:8px;
                text-align:center;margin-top:10px">
        📞 <strong>Kenya Health Emergency Line: 0800 720 021</strong> (Free, 24/7)
    </div>
    """, unsafe_allow_html=True)


# ── SYMPTOM CHECKER ───────────────────────────────────────────────────────────
elif page == "triage":
    from pages.symptom_checker import render
    render(lang)


# ── CLINIC LOCATOR ────────────────────────────────────────────────────────────
elif page == "clinic":
    from pages.clinic_locator import render
    render(lang)


# ── IMMUNIZATION TRACKER ──────────────────────────────────────────────────────
elif page == "immunization":
    from pages.immunization_tracker import render
    render(lang)


# ── HEALTH CHAT ───────────────────────────────────────────────────────────────
elif page == "chat":
    from pages.health_chat import render
    render(lang)
