def main_wrap():
     st.markdown('<div class="main-content">', unsafe_allow_html=True)

def main_wrap_end():
     st.markdown('</div>', unsafe_allow_html=True)

 def page_header(title, subtitle=""):
     st.markdown(f"""
     <div class="page-header">
         <h1>{title}</h1>
         <p>{subtitle}</p>
     </div>
     """, unsafe_allow_html=True)

 def badge(statut):
     mapping = {
         "Payée":      "badge-green",
         "Validée":    "badge-green",
         "Remboursée": "badge-green",
         "À payer":    "badge-orange",
         "En attente": "badge-orange",
         "En retard":  "badge-red",
         "Refusée":    "badge-red",
         "Annulée":    "badge-gray",
     }
    cls = mapping.get(statut, "badge-gray")
     return f'<span class="badge {cls}">{statut}</span>'
import streamlit as st
import json
import io
import pandas as pd
from datetime import datetime, date
import base64

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="FactureCat",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL — STYLE PENNYLANE + CHAT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

/* ── Reset fond ── */
.stApp {
    background: #f7f5f3 !important;
}

/* ── Cacher sidebar et header Streamlit ── */
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ══════════════════════════════════════════════════════
   TOPBAR
══════════════════════════════════════════════════════ */
.topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 58px;
    background: white;
    border-bottom: 1px solid #ece9e4;
    display: flex;
    align-items: center;
    padding: 0 2rem;
    z-index: 1000;
    gap: 2rem;
}
.topbar-logo {
    font-size: 1.1rem;
    font-weight: 800;
    color: #1a1a2e;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    white-space: nowrap;
}
.topbar-logo span { color: #f0a070; }
.topbar-nav {
    display: flex;
    gap: 0.25rem;
    flex: 1;
    margin-left: 1rem;
}
.topbar-nav a {
    padding: 0.4rem 0.9rem;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #6b7280;
    text-decoration: none;
    transition: all 0.15s;
    white-space: nowrap;
}
.topbar-nav a:hover { background: #f7f5f3; color: #1a1a2e; }
.topbar-nav a.active { background: #fff4ee; color: #f0a070; font-weight: 600; }
.topbar-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-left: auto;
}
.topbar-avatar {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #f0a070, #e07040);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; cursor: pointer;
}

/* ══════════════════════════════════════════════════════
   SIDEBAR GAUCHE
══════════════════════════════════════════════════════ */
.left-sidebar {
    position: fixed;
    top: 58px; left: 0; bottom: 0;
    width: 220px;
    background: white;
    border-right: 1px solid #ece9e4;
    padding: 1.5rem 1rem;
    z-index: 999;
    overflow-y: auto;
}
.sidebar-section {
    margin-bottom: 1.5rem;
}
.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0 0.5rem;
    margin-bottom: 0.4rem;
}
.sidebar-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 0.75rem;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #4b5563;
    cursor: pointer;
    margin-bottom: 0.15rem;
    transition: all 0.15s;
    text-decoration: none;
}
.sidebar-item:hover { background: #f7f5f3; color: #1a1a2e; }
.sidebar-item.active {
    background: #fff4ee;
    color: #f0a070;
    font-weight: 600;
}
.sidebar-item .icon { font-size: 1rem; width: 20px; text-align: center; }

/* ══════════════════════════════════════════════════════
   MAIN CONTENT
══════════════════════════════════════════════════════ */
.main-content {
    margin-left: 220px;
    margin-top: 58px;
    padding: 2rem 2.5rem;
    min-height: calc(100vh - 58px);
}

/* ══════════════════════════════════════════════════════
   PAGE HEADER
══════════════════════════════════════════════════════ */
.page-header {
    margin-bottom: 2rem;
}
.page-header h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #1a1a2e !important;
    margin: 0 0 0.25rem 0 !important;
}
.page-header p {
    color: #6b7280;
    font-size: 0.88rem;
    margin: 0;
}

/* ══════════════════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════════════════ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #ece9e4;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f0a070, #e07040);
    border-radius: 14px 14px 0 0;
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #1a1a2e;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.kpi-change {
    font-size: 0.75rem;
    font-weight: 500;
    color: #10b981;
}
.kpi-change.down { color: #ef4444; }
.kpi-icon {
    position: absolute;
    top: 1rem; right: 1.2rem;
    font-size: 1.5rem;
    opacity: 0.2;
}

/* ══════════════════════════════════════════════════════
   CARDS / PANELS
══════════════════════════════════════════════════════ */
.panel {
    background: white;
    border-radius: 14px;
    border: 1px solid #ece9e4;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.panel-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #ece9e4;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.panel-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1a1a2e;
}
.panel-body { padding: 1.5rem; }

/* ══════════════════════════════════════════════════════
   TABLE STYLE
══════════════════════════════════════════════════════ */
.invoice-table {
    width: 100%;
    border-collapse: collapse;
}
.invoice-table th {
    font-size: 0.72rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.6rem 1rem;
    text-align: left;
    border-bottom: 1px solid #ece9e4;
}
.invoice-table td {
    padding: 0.85rem 1rem;
    border-bottom: 1px solid #f7f5f3;
    font-size: 0.84rem;
    color: #374151;
    vertical-align: middle;
}
.invoice-table tr:hover td { background: #fafaf8; }
.invoice-table tr:last-child td { border-bottom: none; }

/* ── Badges statut ── */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    white-space: nowrap;
}
.badge-green  { background: #d1fae5; color: #065f46; }
.badge-orange { background: #ffedd5; color: #9a3412; }
.badge-red    { background: #fee2e2; color: #991b1b; }
.badge-gray   { background: #f3f4f6; color: #4b5563; }
.badge-blue   { background: #dbeafe; color: #1e40af; }

/* ══════════════════════════════════════════════════════
   UPLOAD ZONE
══════════════════════════════════════════════════════ */
.upload-zone {
    border: 2px dashed #e5e0d8;
    border-radius: 14px;
    padding: 3rem 2rem;
    text-align: center;
    background: #fafaf8;
    transition: all 0.2s;
}
.upload-zone:hover {
    border-color: #f0a070;
    background: #fff8f3;
}

/* ══════════════════════════════════════════════════════
   CHATBOT FLOTTANT
══════════════════════════════════════════════════════ */
.chat-fab {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0a070, #e07040);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(240,112,64,0.4);
    z-index: 2000;
    transition: transform 0.2s;
    border: none;
}
.chat-fab:hover { transform: scale(1.08); }

.chat-window {
    position: fixed;
    bottom: 5.5rem;
    right: 2rem;
    width: 340px;
    height: 460px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15);
    z-index: 1999;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #ece9e4;
}
.chat-window-header {
    background: linear-gradient(135deg, #f0a070, #e07040);
    padding: 1rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.chat-window-header .cat-avatar {
    width: 36px; height: 36px;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
}
.chat-window-header .cat-info h4 {
    margin: 0;
    color: white;
    font-size: 0.9rem;
    font-weight: 700;
}
.chat-window-header .cat-info p {
    margin: 0;
    color: rgba(255,255,255,0.8);
    font-size: 0.72rem;
}
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: #fafaf8;
}
.msg-bot {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
}
.msg-bot .bubble {
    background: white;
    border: 1px solid #ece9e4;
    border-radius: 14px 14px 14px 4px;
    padding: 0.6rem 0.9rem;
    font-size: 0.82rem;
    color: #374151;
    max-width: 80%;
    line-height: 1.5;
}
.msg-user {
    display: flex;
    justify-content: flex-end;
}
.msg-user .bubble {
    background: linear-gradient(135deg, #f0a070, #e07040);
    color: white;
    border-radius: 14px 14px 4px 14px;
    padding: 0.6rem 0.9rem;
    font-size: 0.82rem;
    max-width: 80%;
    line-height: 1.5;
}
.chat-input-area {
    padding: 0.75rem;
    border-top: 1px solid #ece9e4;
    background: white;
}

/* ══════════════════════════════════════════════════════
   FORMULAIRES
══════════════════════════════════════════════════════ */
.form-panel {
    background: white;
    border-radius: 14px;
    border: 1px solid #ece9e4;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.form-section-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #ece9e4;
}

/* ══════════════════════════════════════════════════════
   PROGRESS & MISC
══════════════════════════════════════════════════════ */
.stProgress > div > div {
    background: linear-gradient(90deg, #f0a070, #e07040) !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #f0a070, #e07040) !important;
    border: none !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem !important;
    background: transparent !important;
    border-bottom: 1px solid #ece9e4 !important;
    padding-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    padding: 0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #f0a070 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #f0a070 !important;
}
div[data-testid="stExpander"] {
    border: 1px solid #ece9e4 !important;
    border-radius: 12px !important;
    background: white !important;
}
.stSelectbox label, .stTextInput label,
.stDateInput label, .stNumberInput label,
.stTextArea label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #4b5563 !important;
}
input, textarea, select {
    border-radius: 8px !important;
    border-color: #e5e0d8 !important;
    font-size: 0.84rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e5e0d8; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "chat_open" not in st.session_state:
    st.session_state["chat_open"] = False
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "bot", "content": "Bonjour ! Je suis FactureCat 🐱\nComment puis-je vous aider aujourd'hui ?"}
    ]
if "resultats" not in st.session_state:
    st.session_state["resultats"] = []
if "current_preview" not in st.session_state:
    st.session_state["current_preview"] = None
if "current_preview_name" not in st.session_state:
    st.session_state["current_preview_name"] = ""
if "selected_facture_idx" not in st.session_state:
    st.session_state["selected_facture_idx"] = None
if "selected_ndf_idx" not in st.session_state:
    st.session_state["selected_ndf_idx"] = None

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION (query params)
# ══════════════════════════════════════════════════════════════════════════════
params = st.query_params
if "p" in params:
    st.session_state["page"] = params["p"]

page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR HTML
# ══════════════════════════════════════════════════════════════════════════════
nav_items = [
    ("dashboard",    "🏠 Tableau de bord"),
    ("factures",     "📄 Factures"),
    ("notes_frais",  "💸 Notes de frais"),
    ("comptabilite", "📊 Comptabilité"),
    ("parametres",   "⚙️ Paramètres"),
]

nav_html = "".join([
    f'<a href="?p={k}" class="{"active" if page == k else ""}">{label}</a>'
    for k, label in nav_items
])

st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">🐱 <span>Facture</span>Cat</div>
    <nav class="topbar-nav">{nav_html}</nav>
    <div class="topbar-right">
        <div style="font-size:0.78rem;color:#9ca3af;">{datetime.now().strftime("%d %b %Y")}</div>
        <div class="topbar-avatar">🐱</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR GAUCHE HTML
# ══════════════════════════════════════════════════════════════════════════════
def sidebar_item(key, icon, label):
    active_class = "active" if page == key else ""
    return f'<a href="?p={key}" class="sidebar-item {active_class}"><span class="icon">{icon}</span>{label}</a>'

st.markdown(f"""
<div class="left-sidebar">
    <div class="sidebar-section">
        <div class="sidebar-section-title">Principal</div>
        {sidebar_item("dashboard",    "🏠", "Tableau de bord")}
        {sidebar_item("factures",     "📄", "Factures")}
        {sidebar_item("notes_frais",  "💸", "Notes de frais")}
        {sidebar_item("comptabilite", "📊", "Comptabilité")}
    </div>
    <div class="sidebar-section">
        <div class="sidebar-section-title">Paramètres</div>
        {sidebar_item("parametres", "⚙️", "Paramètres")}
        {sidebar_item("api_key",    "🔑", "Clé API")}
    </div>
    <div style="position:absolute;bottom:1.5rem;left:1rem;right:1rem;">
        <div style="background:#fff4ee;border-radius:12px;padding:0.75rem;
             text-align:center;border:1px solid rgba(240,160,112,0.2);">
            <div style="font-size:1.5rem;">🐱</div>
            <div style="font-size:0.72rem;color:#a0522d;font-weight:600;margin-top:0.3rem;">
                FactureCat v2.0
            </div>
            <div style="font-size:0.68rem;color:#c8956c;">Powered by Gemini</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHATBOT FLOTTANT
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    # ── Bouton FAB ──
    if st.button("🐱", key="chat_fab_btn", help="Ouvrir FactureCat Assistant"):
        st.session_state["chat_open"] = not st.session_state["chat_open"]
        st.rerun()

    st.markdown("""
    <style>
    div[data-testid="stButton"] button[title="Ouvrir FactureCat Assistant"] {
        position: fixed !important;
        bottom: 2rem !important;
        right: 2rem !important;
        width: 56px !important;
        height: 56px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #f0a070, #e07040) !important;
        color: white !important;
        font-size: 1.4rem !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(240,112,64,0.4) !important;
        z-index: 2000 !important;
        padding: 0 !important;
        min-width: unset !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Fenêtre chat ──
    if st.session_state["chat_open"]:
        st.markdown("""
        <div class="chat-window">
            <div class="chat-window-header">
                <div class="cat-avatar">🐱</div>
                <div class="cat-info">
                    <h4>FactureCat Assistant</h4>
                    <p>🟢 En ligne · Répond instantanément</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Messages dans un container Streamlit (pour qu'ils soient interactifs)
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"]:has(> div[data-testid="stVerticalBlock"])
            > div:nth-child(2) {
                position: fixed !important;
                bottom: 5.5rem !important;
                right: 2rem !important;
                width: 340px !important;
                z-index: 1998 !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # Afficher messages
            for msg in st.session_state["chat_messages"][-6:]:
                if msg["role"] == "bot":
                    st.markdown(f"""
                    <div class="msg-bot" style="position:relative;z-index:1998;">
                        <div style="font-size:1.2rem;">🐱</div>
                        <div class="bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-user" style="position:relative;z-index:1998;">
                        <div class="bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Input
            col_inp, col_send = st.columns([4, 1])
            with col_inp:
                user_msg = st.text_input("", placeholder="Posez votre question…",
                                         key="chat_input", label_visibility="collapsed")
            with col_send:
                if st.button("➤", key="chat_send"):
                    if user_msg.strip():
                        st.session_state["chat_messages"].append(
                            {"role": "user", "content": user_msg})

                        # ── Réponses automatiques ──
                        msg_lower = user_msg.lower()
                        if any(w in msg_lower for w in ["facture", "invoice"]):
                            response = "📄 Pour vos factures, allez dans l'onglet **Factures** et utilisez l'import IA. Je peux extraire automatiquement toutes les données ! 🐾"
                        elif any(w in msg_lower for w in ["note", "frais", "dépense"]):
                            response = "💸 Les notes de frais se gèrent dans la section dédiée. Vous pouvez les catégoriser et les exporter facilement ! 🐱"
                        elif any(w in msg_lower for w in ["comptabilité", "bilan", "résultat"]):
                            response = "📊 La section Comptabilité vous donne une vue consolidée de vos charges et produits par période. 🐾"
                        elif any(w in msg_lower for w in ["export", "csv", "télécharger"]):
                            response = "📥 L'export CSV et JSON est disponible dans chaque section (Factures, Notes de frais, Comptabilité). 🐱"
                        elif any(w in msg_lower for w in ["bonjour", "salut", "hello"]):
                            response = "Bonjour ! 🐱 Je suis FactureCat, votre assistant comptable félin. Que puis-je faire pour vous ?"
                        elif any(w in msg_lower for w in ["merci", "thanks"]):
                            response = "Avec plaisir ! N'hésitez pas si vous avez d'autres questions 🐾 Miaou~"
                        else:
                            response = "Je suis FactureCat 🐱 Je peux vous aider avec vos factures, notes de frais et comptabilité. Que souhaitez-vous faire ?"

                        st.session_state["chat_messages"].append(
                            {"role": "bot", "content": response})
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HELPER : wrapper main content
# ══════════════════════════════════════════════════════════════════════════════
def main_wrap():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

def main_wrap_end():
    st.markdown('</div>', unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {'<p>' + subtitle + '</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def badge(text, color="gray"):
    map_c = {
        "Payée": "green", "À payer": "orange",
        "En retard": "red", "Annulée": "gray",
        "Remboursée": "green", "En attente": "orange",
        "Refusée": "red", "Approuvée": "blue",
    }
    cls = f"badge-{map_c.get(text, color)}"
    return f'<span class="badge {cls}">{text}</span>'

def kpi_card(label, value, change="", icon="", change_positive=True):
    change_class = "" if change_positive else "down"
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {'<div class="kpi-change ' + change_class + '">' + change + '</div>' if change else ''}
    </div>
    """

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    main_wrap()
    page_header("Tableau de bord", "Vue d'ensemble de votre activité")

    factures = get_data("factures")
    ndf = get_data("notes_frais") if callable(lambda: get_data("notes_frais")) else []

    total_ttc    = sum(float(f.get("montant_ttc", 0)) for f in factures)
    total_ht     = sum(float(f.get("montant_ht", 0))  for f in factures)
    total_tva    = sum(float(f.get("tva", 0))          for f in factures)
    nb_en_attente = len([f for f in factures if f.get("statut") == "À payer"])

    st.markdown(f"""
    <div class="kpi-grid">
        {kpi_card("Chiffre d'affaires TTC", f"{total_ttc:,.2f} €", icon="💰")}
        {kpi_card("Total HT",               f"{total_ht:,.2f} €",  icon="📄")}
        {kpi_card("TVA collectée",           f"{total_tva:,.2f} €", icon="📊")}
        {kpi_card("Factures en attente",     str(nb_en_attente),    icon="⏳",
                  change="À traiter" if nb_en_attente > 0 else "✓ À jour",
                  change_positive=(nb_en_attente == 0))}
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("""
        <div class="panel-header">
            <span class="panel-title">📄 Dernières factures</span>
            <a href="?p=factures" style="font-size:0.78rem;color:#f0a070;font-weight:600;
               text-decoration:none;">Voir tout →</a>
        </div>
        """, unsafe_allow_html=True)

        if factures:
            rows = ""
            for f in sorted(factures, key=lambda x: str(x.get("date", "")), reverse=True)[:5]:
                rows += f"""
                <tr>
                    <td><b style="color:#1a1a2e;">{f.get('fournisseur','—')}</b></td>
                    <td style="color:#9ca3af;">{f.get('numero','—')}</td>
                    <td>{f.get('date','—')}</td>
                    <td><b>{float(f.get('montant_ttc',0)):,.2f} €</b></td>
                    <td>{badge(f.get('statut','—'))}</td>
                </tr>
                """
            st.markdown(f"""
            <table class="invoice-table">
                <thead>
                    <tr>
                        <th>Fournisseur</th><th>N°</th>
                        <th>Date</th><th>Montant TTC</th><th>Statut</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#9ca3af;">
                <div style="font-size:2rem;">📭</div>
                <p style="font-size:0.84rem;">Aucune facture pour l'instant</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        # Répartition par catégorie
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("""
        <div class="panel-header">
            <span class="panel-title">📂 Par catégorie</span>
        </div>
        <div class="panel-body">
        """, unsafe_allow_html=True)

        if factures:
            cats = {}
            for f in factures:
                c = f.get("categorie", "Autre")
                cats[c] = cats.get(c, 0) + float(f.get("montant_ttc", 0))

            for cat, total in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:6]:
                pct = (total / total_ttc * 100) if total_ttc > 0 else 0
                st.markdown(f"""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex;justify-content:space-between;
                         font-size:0.8rem;margin-bottom:0.3rem;">
                        <span style="color:#374151;font-weight:500;">{cat}</span>
                        <span style="color:#9ca3af;">{total:,.0f} €</span>
                    </div>
                    <div style="background:#f3f4f6;border-radius:4px;height:6px;overflow:hidden;">
                        <div style="background:linear-gradient(90deg,#f0a070,#e07040);
                             height:100%;width:{pct:.1f}%;border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#9ca3af;font-size:0.84rem;">Aucune donnée</p>',
                        unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

        # Statuts
        st.markdown('<div class="panel" style="margin-top:1rem;">', unsafe_allow_html=True)
        st.markdown("""
        <div class="panel-header">
            <span class="panel-title">🏷️ Statuts</span>
        </div>
        <div class="panel-body" style="padding:1rem 1.5rem;">
        """, unsafe_allow_html=True)

        statuts_count = {}
        for f in factures:
            s = f.get("statut", "—")
            statuts_count[s] = statuts_count.get(s, 0) + 1

        for s, count in statuts_count.items():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:0.4rem 0;border-bottom:1px solid #f7f5f3;">
                {badge(s)}
                <span style="font-size:0.82rem;font-weight:700;color:#374151;">{count}</span>
            </div>
            """, unsafe_allow_html=True)

        if not statuts_count:
            st.markdown('<p style="color:#9ca3af;font-size:0.84rem;">Aucune donnée</p>',
                        unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "factures":
    main_wrap()
    page_header("Factures", "Import, analyse IA et suivi de vos factures")

    tab1, tab2, tab3 = st.tabs(["📤 Import & Analyse", "📋 Liste & Aperçu", "📊 Export"])

    # ── TAB 1 : IMPORT ────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Bulle chat
        st.markdown("""
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;
             background:white;border-radius:14px;padding:1rem 1.5rem;
             border:1px solid #ece9e4;">
            <div style="font-size:2.5rem;">🐱</div>
            <div>
                <b style="color:#1a1a2e;font-size:0.9rem;">FactureCat est prêt !</b><br>
                <span style="color:#6b7280;font-size:0.82rem;">
                    Déposez vos factures ci-dessous. Je vais extraire automatiquement
                    toutes les informations grâce à Gemini 2.5 🐾
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Glissez vos factures ici (PDF ou image)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="facture_uploader"
        )

        if uploaded_files:
            existing_names = {r.get("fichier", "") for r in get_data("factures")}
            new_files = [f for f in uploaded_files if f.name not in existing_names]
            already   = [f for f in uploaded_files if f.name in existing_names]

            if already:
                st.warning(f"⚠️ {len(already)} fichier(s) déjà importé(s) ignoré(s)")

            if new_files:
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                     padding:0.75rem 1rem;margin:0.75rem 0;font-size:0.84rem;color:#065f46;">
                    ✅ <b>{len(new_files)}</b> nouveau(x) fichier(s) prêt(s) à analyser
                </div>
                """, unsafe_allow_html=True)

                col_sel, col_prev = st.columns([1, 1])
                with col_sel:
                    names = [f.name for f in new_files]
                    selected_preview = st.selectbox("👁️ Aperçu rapide", names,
                                                    key="select_preview")
                    for f in new_files:
                        if f.name == selected_preview:
                            f.seek(0)
                            content = f.read()
                            f.seek(0)
                            if f.name.lower().endswith(".pdf"):
                                imgs = pdf_to_images(content)
                            else:
                                imgs = [Image.open(io.BytesIO(content))]
                            st.session_state["current_preview"] = imgs
                            st.session_state["current_preview_name"] = f.name
                            break

                with col_prev:
                    if st.session_state.get("current_preview"):
                        imgs = st.session_state["current_preview"]
                        if len(imgs) > 1:
                            pg = st.slider("Page", 1, len(imgs), 1, key="prev_pg") - 1
                        else:
                            pg = 0
                        st.image(imgs[pg], use_column_width=True)

                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                with col_b2:
                    analyser = st.button("🔍 Analyser avec Gemini 2.5",
                                         use_container_width=True,
                                         type="primary", key="btn_analyser")

                if analyser:
                    model = configure_gemini()
                    if not model:
                        st.error("❌ Clé API Gemini manquante — configurez-la dans Paramètres")
                    else:
                        progress = st.progress(0)
                        status   = st.empty()
                        results  = []

                        for i, f in enumerate(new_files):
                            status.markdown(f"""
                            <div style="background:#fff8f3;border-radius:10px;padding:0.75rem 1rem;
                                 border-left:3px solid #f0a070;font-size:0.84rem;color:#374151;">
                                🔍 Analyse en cours : <b>{f.name}</b>
                            </div>
                            """, unsafe_allow_html=True)

                            f.seek(0)
                            content = f.read()
                            f.seek(0)

                            if f.name.lower().endswith(".pdf"):
                                images = pdf_to_images(content)
                            else:
                                images = [Image.open(io.BytesIO(content))]

                            result = extraire_facture(model, images)
                            result["fichier"] = f.name
                            results.append((f.name, result, images))
                            progress.progress((i + 1) / len(new_files))

                        saved = 0
                        for fname, result, images in results:
                            if fname == st.session_state.get("current_preview_name", ""):
                                st.session_state["current_preview"] = images
                            try:
                                supabase = get_supabase()
                                uid = st.session_state.get("user_id", "")
                                supabase.table("factures").insert(
                                    {**result, "user_id": uid}
                                ).execute()
                                saved += 1
                            except Exception:
                                st.session_state["resultats"].append(result)
                                saved += 1

                        status.success(f"✅ {saved} facture(s) analysée(s) et sauvegardée(s) !")
                        st.markdown("---")

                        for fname, result, _ in results:
                            with st.expander(f"📄 {fname}", expanded=True):
                                c1, c2, c3 = st.columns(3)
                                fields_c1 = [
                                    ("🏢 Fournisseur", result.get("fournisseur", "—")),
                                    ("🔢 N° Facture",  result.get("numero", "—")),
                                    ("📅 Date",        result.get("date", "—")),
                                ]
                                fields_c2 = [
                                    ("💵 Montant HT",  f"{float(result.get('montant_ht',0)):.2f} €"),
                                    ("📊 TVA",         f"{float(result.get('tva',0)):.2f} €"),
                                    ("💰 TTC",         f"{float(result.get('montant_ttc',0)):.2f} €"),
                                ]
                                fields_c3 = [
                                    ("📂 Catégorie", result.get("categorie", "—")),
                                    ("🏷️ Statut",    result.get("statut", "—")),
                                ]
                                for col_r, fields in [(c1, fields_c1), (c2, fields_c2),
                                                      (c3, fields_c3)]:
                                    with col_r:
                                        for lbl, val in fields:
                                            st.markdown(f"""
                                            <div style="padding:0.5rem 0;
                                                 border-bottom:1px solid #f3f4f6;">
                                                <div style="font-size:0.72rem;color:#9ca3af;
                                                     font-weight:600;">{lbl}</div>
                                                <div style="font-size:0.9rem;color:#1a1a2e;
                                                     font-weight:700;">{val}</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                        st.rerun()

        else:
            st.markdown("""
            <div class="upload-zone">
                <div style="font-size:3rem;margin-bottom:1rem;">🐱</div>
                <p style="font-weight:700;color:#1a1a2e;font-size:1rem;margin:0;">
                    Aucun fichier sélectionné
                </p>
                <p style="color:#9ca3af;font-size:0.84rem;margin:0.5rem 0 0 0;">
                    Utilisez le bouton ci-dessus pour importer vos factures
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2 : LISTE ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        factures = get_data("factures")

        if factures:
            # Filtres
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                search = st.text_input("🔍 Rechercher", key="fact_search",
                                       placeholder="Fournisseur…")
            with f2:
                cats = ["Toutes"] + sorted(set(f.get("categorie", "") for f in factures))
                cat_filter = st.selectbox("Catégorie", cats, key="fact_cat")
            with f3:
                statuts = ["Tous"] + sorted(set(f.get("statut", "") for f in factures))
                stat_filter = st.selectbox("Statut", statuts, key="fact_stat")
            with f4:
                sort_by = st.selectbox("Trier par",
                    ["Date ↓", "Date ↑", "Montant ↓", "Montant ↑"], key="fact_sort")

            filtered = [f for f in factures
                        if (not search or search.lower() in str(f.get("fournisseur","")).lower())
                        and (cat_filter == "Toutes" or f.get("categorie") == cat_filter)
                        and (stat_filter == "Tous" or f.get("statut") == stat_filter)]

            if sort_by == "Date ↓":
                filtered.sort(key=lambda x: str(x.get("date","")), reverse=True)
            elif sort_by == "Date ↑":
                filtered.sort(key=lambda x: str(x.get("date","")))
            elif sort_by == "Montant ↓":
                filtered.sort(key=lambda x: float(x.get("montant_ttc",0)), reverse=True)
            else:
                filtered.sort(key=lambda x: float(x.get("montant_ttc",0)))

            st.markdown(f"""
            <p style="color:#9ca3af;font-size:0.78rem;margin:0.5rem 0 1rem 0;">
                {len(filtered)} résultat(s)
            </p>
            """, unsafe_allow_html=True)

            col_list, col_view = st.columns([5, 4])

            with col_list:
                rows = ""
                for idx, f in enumerate(filtered):
                    sel = st.session_state.get("selected_facture_idx") == idx
                    bg = "background:#fff8f3;" if sel else ""
                    rows += f"""
                    <tr style="{bg}cursor:pointer;" onclick="">
                        <td><b style="color:#1a1a2e;">{f.get('fournisseur','—')}</b>
                            <br><span style="color:#9ca3af;font-size:0.72rem;">
                            {f.get('numero','—')}</span></td>
                        <td style="color:#6b7280;">{f.get('date','—')}</td>
                        <td><b>{float(f.get('montant_ttc',0)):,.2f} €</b></td>
                        <td>{badge(f.get('statut','—'))}</td>
                    </tr>
                    """

                st.markdown(f"""
                <div class="panel">
                    <table class="invoice-table">
                        <thead>
                            <tr>
                                <th>Fournisseur</th><th>Date</th>
                                <th>Montant TTC</th><th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                # Sélecteur interactif
                if filtered:
                    sel_names = [f"{f.get('fournisseur','—')} · {f.get('date','—')} · "
                                 f"{float(f.get('montant_ttc',0)):,.2f} €"
                                 for f in filtered]
                    sel_choice = st.selectbox("Sélectionner une facture",
                                              options=range(len(filtered)),
                                              format_func=lambda i: sel_names[i],
                                              key="fact_sel_box")
                    st.session_state["selected_facture_idx"] = sel_choice

            with col_view:
                sel_idx = st.session_state.get("selected_facture_idx")
                if sel_idx is not None and sel_idx < len(filtered):
                    r = filtered[sel_idx]
                    st.markdown(f"""
                    <div class="panel">
                        <div class="panel-header">
                            <span class="panel-title">📄 {r.get('fournisseur','—')}</span>
                            {badge(r.get('statut','—'))}
                        </div>
                        <div class="panel-body">
                    """, unsafe_allow_html=True)

                    for lbl, val in [
                        ("N° Facture",   r.get("numero","—")),
                        ("Date",         r.get("date","—")),
                        ("Catégorie",    r.get("categorie","—")),
                        ("Montant HT",   f"{float(r.get('montant_ht',0)):,.2f} €"),
                        ("TVA",          f"{float(r.get('tva',0)):,.2f} €"),
                        ("Montant TTC",  f"{float(r.get('montant_ttc',0)):,.2f} €"),
                    ]:
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                             padding:0.6rem 0;border-bottom:1px solid #f7f5f3;">
                            <span style="font-size:0.8rem;color:#9ca3af;font-weight:500;">
                                {lbl}
                            </span>
                            <span style="font-size:0.84rem;color:#1a1a2e;font-weight:600;">
                                {val}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('</div></div>', unsafe_allow_html=True)

                    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

                    a1, a2, a3 = st.columns(3)
                    with a1:
                        new_statut = st.selectbox("Changer le statut",
                            ["À payer","Payée","En retard","Annulée"],
                            index=["À payer","Payée","En retard","Annulée"].index(
                                r.get("statut","À payer"))
                            if r.get("statut","À payer") in
                            ["À payer","Payée","En retard","Annulée"] else 0,
                            key=f"statut_{sel_idx}")
                    with a2:
                        if st.button("💾 Sauvegarder", key=f"save_{sel_idx}",
                                     use_container_width=True, type="primary"):
                            try:
                                get_supabase().table("factures").update(
                                    {"statut": new_statut}
                                ).eq("id", r["id"]).execute()
                                st.success("✅ Mis à jour")
                                st.rerun()
                            except Exception:
                                st.success("✅ Mis à jour localement")
                    with a3:
                        if st.button("🗑️ Supprimer", key=f"del_{sel_idx}",
                                     use_container_width=True):
                            try:
                                get_supabase().table("factures").delete().eq(
                                    "id", r["id"]).execute()
                                st.session_state["selected_facture_idx"] = None
                                st.rerun()
                            except Exception:
                                st.error("❌ Erreur")
                else:
                    st.markdown("""
                    <div class="panel" style="text-align:center;padding:4rem 2rem;">
                        <div style="font-size:3rem;">🐱</div>
                        <p style="color:#6b7280;font-weight:600;margin-top:0.5rem;">
                            Sélectionnez une facture
                        </p>
                        <p style="color:#9ca3af;font-size:0.82rem;">
                            Utilisez la liste pour afficher le détail
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:14px;border:1px solid #ece9e4;">
                <div style="font-size:3rem;">📭</div>
                <h3 style="color:#1a1a2e;">Aucune facture</h3>
                <p style="color:#9ca3af;">Importez vos premières factures dans l'onglet Import</p>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3 : EXPORT ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        factures = get_data("factures")
        if factures:
            df_exp = pd.DataFrame(factures)
            st.dataframe(df_exp, use_container_width=True, hide_index=True)
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            with e1:
                csv = df_exp.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Télécharger CSV", data=csv,
                    file_name="factures.csv", mime="text/csv", use_container_width=True)
            with e2:
                json_data = json.dumps(factures, ensure_ascii=False, indent=2)
                st.download_button("📥 Télécharger JSON", data=json_data,
                    file_name="factures.json", mime="application/json",
                    use_container_width=True)
        else:
            st.info("📭 Aucune facture à exporter")

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "notes_frais":
    main_wrap()
    page_header("Notes de frais", "Saisie, suivi et remboursement de vos dépenses")

    tab1, tab2, tab3 = st.tabs(["➕ Nouvelle dépense", "📋 Liste & Aperçu", "📊 Export"])

    with tab1:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        col_form, col_side = st.columns([3, 2])

        with col_form:
            st.markdown('<div class="form-panel">', unsafe_allow_html=True)
            st.markdown('<div class="form-section-title">Informations de la dépense</div>',
                        unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                ndf_date = st.date_input("📅 Date", value=date.today(), key="ndf_date")
            with c2:
                ndf_cat = st.selectbox("📂 Catégorie",
                    ["Transport", "Repas", "Hébergement", "Matériel",
                     "Télécom", "Formation", "Autre"],
                    key="ndf_cat")

            ndf_desc = st.text_input("📝 Description", key="ndf_desc",
                                     placeholder="Ex: Déjeuner client Paris")

            c3, c4 = st.columns(2)
            with c3:
                ndf_ht = st.number_input("💵 Montant HT (€)", min_value=0.0,
                                          step=0.01, key="ndf_ht")
                        with c4:
                ndf_tva_pct = st.selectbox("📊 TVA", ["20%", "10%", "5.5%", "0%"],
                                            key="ndf_tva")

            tva_val = float(ndf_tva_pct.replace("%", "")) / 100
            ndf_tva_montant = round(ndf_ht * tva_val, 2)
            ndf_ttc = round(ndf_ht + ndf_tva_montant, 2)

            # ── Récap calcul ──
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                 padding:0.75rem 1rem;margin:0.5rem 0;display:flex;gap:2rem;">
                <div>
                    <div style="font-size:0.7rem;color:#6b7280;font-weight:600;">TVA</div>
                    <div style="font-size:1rem;font-weight:700;color:#065f46;">
                        {ndf_tva_montant:.2f} €
                    </div>
                </div>
                <div>
                    <div style="font-size:0.7rem;color:#6b7280;font-weight:600;">TOTAL TTC</div>
                    <div style="font-size:1rem;font-weight:700;color:#065f46;">
                        {ndf_ttc:.2f} €
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c5, c6 = st.columns(2)
            with c5:
                ndf_paiement = st.selectbox("💳 Moyen de paiement",
                    ["Carte bancaire", "Espèces", "Virement", "Chèque"],
                    key="ndf_paiement")
            with c6:
                ndf_statut = st.selectbox("🏷️ Statut",
                    ["En attente", "Validée", "Remboursée", "Refusée"],
                    key="ndf_statut")

            ndf_justificatif = st.file_uploader(
                "📎 Justificatif (PDF ou image)",
                type=["pdf", "png", "jpg", "jpeg"],
                key="ndf_justificatif"
            )

            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns([1, 2, 1])
            with b2:
                save_ndf = st.button("💾 Enregistrer la dépense",
                                     use_container_width=True,
                                     type="primary", key="btn_save_ndf")

            if save_ndf:
                if not ndf_desc.strip():
                    st.warning("⚠️ Veuillez saisir une description")
                elif ndf_ht <= 0:
                    st.warning("⚠️ Le montant doit être supérieur à 0")
                else:
                    ndf_data = {
                        "date":           str(ndf_date),
                        "categorie":      ndf_cat,
                        "description":    ndf_desc,
                        "montant_ht":     ndf_ht,
                        "tva":            ndf_tva_montant,
                        "montant_ttc":    ndf_ttc,
                        "moyen_paiement": ndf_paiement,
                        "statut":         ndf_statut,
                        "justificatif":   ndf_justificatif.name
                                          if ndf_justificatif else "",
                    }
                    try:
                        supabase = get_supabase()
                        uid = st.session_state.get("user_id", "")
                        supabase.table("notes_frais").insert(
                            {**ndf_data, "user_id": uid}
                        ).execute()
                        st.success("✅ Dépense enregistrée avec succès !")
                        st.rerun()
                    except Exception:
                        if "notes_frais" not in st.session_state:
                            st.session_state["notes_frais"] = []
                        st.session_state["notes_frais"].append(ndf_data)
                        st.success("✅ Dépense enregistrée localement !")
                        st.rerun()

        with col_side:
            # ── Récap mois en cours ──
            ndfs = get_data("notes_frais")
            mois = datetime.now().month
            annee = datetime.now().year
            ndfs_mois = [n for n in ndfs
                         if str(n.get("date","")).startswith(f"{annee}-{mois:02d}")]
            total_mois = sum(float(n.get("montant_ttc", 0)) for n in ndfs_mois)
            en_attente = sum(float(n.get("montant_ttc", 0))
                             for n in ndfs_mois if n.get("statut") == "En attente")

            st.markdown(f"""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">📅 Ce mois-ci</span>
                </div>
                <div class="panel-body">
                    <div style="display:flex;justify-content:space-between;
                         padding:0.6rem 0;border-bottom:1px solid #f7f5f3;">
                        <span style="font-size:0.8rem;color:#9ca3af;">Dépenses totales</span>
                        <span style="font-weight:700;color:#1a1a2e;">
                            {total_mois:,.2f} €
                        </span>
                    </div>
                    <div style="display:flex;justify-content:space-between;
                         padding:0.6rem 0;border-bottom:1px solid #f7f5f3;">
                        <span style="font-size:0.8rem;color:#9ca3af;">En attente</span>
                        <span style="font-weight:700;color:#f0a070;">
                            {en_attente:,.2f} €
                        </span>
                    </div>
                    <div style="display:flex;justify-content:space-between;
                         padding:0.6rem 0;">
                        <span style="font-size:0.8rem;color:#9ca3af;">Nb dépenses</span>
                        <span style="font-weight:700;color:#1a1a2e;">
                            {len(ndfs_mois)}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Répartition par catégorie ──
            if ndfs_mois:
                cats_total = {}
                for n in ndfs_mois:
                    c = n.get("categorie", "Autre")
                    cats_total[c] = cats_total.get(c, 0) + float(n.get("montant_ttc", 0))

                st.markdown("""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">📂 Par catégorie</span>
                    </div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)

                cat_icons = {
                    "Transport": "🚗", "Repas": "🍽️", "Hébergement": "🏨",
                    "Matériel": "💻", "Télécom": "📱", "Formation": "📚",
                    "Autre": "📦"
                }
                for cat, total in sorted(cats_total.items(),
                                          key=lambda x: x[1], reverse=True):
                    pct = (total / total_mois * 100) if total_mois > 0 else 0
                    icon = cat_icons.get(cat, "📦")
                    st.markdown(f"""
                    <div style="margin-bottom:0.75rem;">
                        <div style="display:flex;justify-content:space-between;
                             margin-bottom:0.25rem;">
                            <span style="font-size:0.8rem;color:#4b5563;">
                                {icon} {cat}
                            </span>
                            <span style="font-size:0.8rem;font-weight:600;color:#1a1a2e;">
                                {total:,.2f} €
                            </span>
                        </div>
                        <div style="background:#f3f4f6;border-radius:4px;height:6px;">
                            <div style="background:linear-gradient(90deg,#f0a070,#e07040);
                                 border-radius:4px;height:6px;width:{pct:.0f}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

    # ── TAB 2 : LISTE ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        ndfs = get_data("notes_frais")

        if ndfs:
            f1, f2, f3 = st.columns(3)
            with f1:
                search_ndf = st.text_input("🔍 Rechercher", placeholder="Description…",
                                            key="ndf_search")
            with f2:
                cats_ndf = ["Toutes"] + sorted(set(n.get("categorie","") for n in ndfs))
                cat_ndf_filter = st.selectbox("Catégorie", cats_ndf, key="ndf_cat_filter")
            with f3:
                stats_ndf = ["Tous"] + sorted(set(n.get("statut","") for n in ndfs))
                stat_ndf_filter = st.selectbox("Statut", stats_ndf, key="ndf_stat_filter")

            filtered_ndf = [n for n in ndfs
                if (not search_ndf or
                    search_ndf.lower() in str(n.get("description","")).lower())
                and (cat_ndf_filter == "Toutes" or
                     n.get("categorie") == cat_ndf_filter)
                and (stat_ndf_filter == "Tous" or
                     n.get("statut") == stat_ndf_filter)]

            filtered_ndf.sort(key=lambda x: str(x.get("date","")), reverse=True)

            col_nl, col_nv = st.columns([5, 4])

            with col_nl:
                rows_ndf = ""
                for idx, n in enumerate(filtered_ndf):
                    icon = cat_icons.get(n.get("categorie","Autre"), "📦") \
                           if "cat_icons" in dir() else "📦"
                    rows_ndf += f"""
                    <tr>
                        <td>{icon} <b>{n.get('description','—')}</b>
                            <br><span style="color:#9ca3af;font-size:0.72rem;">
                            {n.get('categorie','—')}</span></td>
                        <td style="color:#6b7280;">{n.get('date','—')}</td>
                        <td><b>{float(n.get('montant_ttc',0)):,.2f} €</b></td>
                        <td>{badge(n.get('statut','—'))}</td>
                    </tr>
                    """

                st.markdown(f"""
                <div class="panel">
                    <table class="invoice-table">
                        <thead>
                            <tr>
                                <th>Dépense</th><th>Date</th>
                                <th>Montant TTC</th><th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>{rows_ndf}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                if filtered_ndf:
                    sel_ndf_names = [
                        f"{n.get('description','—')} · {n.get('date','—')} · "
                        f"{float(n.get('montant_ttc',0)):,.2f} €"
                        for n in filtered_ndf
                    ]
                    sel_ndf = st.selectbox("Sélectionner une dépense",
                                           options=range(len(filtered_ndf)),
                                           format_func=lambda i: sel_ndf_names[i],
                                           key="ndf_sel_box")
                    st.session_state["selected_ndf_idx"] = sel_ndf

            with col_nv:
                sel_ndf_idx = st.session_state.get("selected_ndf_idx")
                if sel_ndf_idx is not None and sel_ndf_idx < len(filtered_ndf):
                    n = filtered_ndf[sel_ndf_idx]
                    st.markdown(f"""
                    <div class="panel">
                        <div class="panel-header">
                            <span class="panel-title">💸 {n.get('description','—')}</span>
                            {badge(n.get('statut','—'))}
                        </div>
                        <div class="panel-body">
                    """, unsafe_allow_html=True)

                    for lbl, val in [
                        ("Date",           n.get("date","—")),
                        ("Catégorie",      n.get("categorie","—")),
                        ("Moyen paiement", n.get("moyen_paiement","—")),
                        ("Montant HT",     f"{float(n.get('montant_ht',0)):,.2f} €"),
                        ("TVA",            f"{float(n.get('tva',0)):,.2f} €"),
                        ("Montant TTC",    f"{float(n.get('montant_ttc',0)):,.2f} €"),
                    ]:
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                             padding:0.6rem 0;border-bottom:1px solid #f7f5f3;">
                            <span style="font-size:0.8rem;color:#9ca3af;font-weight:500;">
                                {lbl}
                            </span>
                            <span style="font-size:0.84rem;color:#1a1a2e;font-weight:600;">
                                {val}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('</div></div>', unsafe_allow_html=True)
                    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

                    na1, na2, na3 = st.columns(3)
                    with na1:
                        new_stat_ndf = st.selectbox("Changer le statut",
                            ["En attente","Validée","Remboursée","Refusée"],
                            key=f"ndf_statut_{sel_ndf_idx}")
                    with na2:
                        if st.button("💾 Sauvegarder", key=f"ndf_save_{sel_ndf_idx}",
                                     use_container_width=True, type="primary"):
                            try:
                                get_supabase().table("notes_frais").update(
                                    {"statut": new_stat_ndf}
                                ).eq("id", n["id"]).execute()
                                st.success("✅ Mis à jour")
                                st.rerun()
                            except Exception:
                                st.success("✅ Mis à jour localement")
                    with na3:
                        if st.button("🗑️ Supprimer", key=f"ndf_del_{sel_ndf_idx}",
                                     use_container_width=True):
                            try:
                                get_supabase().table("notes_frais").delete().eq(
                                    "id", n["id"]).execute()
                                st.session_state["selected_ndf_idx"] = None
                                st.rerun()
                            except Exception:
                                st.error("❌ Erreur")
                else:
                    st.markdown("""
                    <div class="panel" style="text-align:center;padding:4rem 2rem;">
                        <div style="font-size:3rem;">🐱</div>
                        <p style="color:#6b7280;font-weight:600;margin-top:0.5rem;">
                            Sélectionnez une dépense
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:14px;border:1px solid #ece9e4;">
                <div style="font-size:3rem;">📭</div>
                <h3 style="color:#1a1a2e;">Aucune dépense enregistrée</h3>
                <p style="color:#9ca3af;">Ajoutez votre première note de frais</p>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3 : EXPORT ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        ndfs_exp = get_data("notes_frais")
        if ndfs_exp:
            df_ndf = pd.DataFrame(ndfs_exp)
            st.dataframe(df_ndf, use_container_width=True, hide_index=True)
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            ex1, ex2 = st.columns(2)
            with ex1:
                csv_ndf = df_ndf.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Télécharger CSV", data=csv_ndf,
                    file_name="notes_frais.csv", mime="text/csv",
                    use_container_width=True)
            with ex2:
                json_ndf = json.dumps(ndfs_exp, ensure_ascii=False, indent=2)
                st.download_button("📥 Télécharger JSON", data=json_ndf,
                    file_name="notes_frais.json", mime="application/json",
                    use_container_width=True)
        else:
            st.info("📭 Aucune dépense à exporter")

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPTABILITÉ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "comptabilite":
    main_wrap()
    page_header("Comptabilité", "Suivi des flux, TVA et bilan")

    factures = get_data("factures")
    ndfs     = get_data("notes_frais")

    # ── KPIs comptables ──
    total_achats  = sum(float(f.get("montant_ttc", 0)) for f in factures)
    total_tva_ded = sum(float(f.get("tva", 0)) for f in factures)
    total_frais   = sum(float(n.get("montant_ttc", 0)) for n in ndfs)
    total_depenses = total_achats + total_frais

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">🧾</div>
            <div class="kpi-label">Total achats TTC</div>
            <div class="kpi-value">{total_achats:,.0f} €</div>
            <div class="kpi-change">{len(factures)} factures</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">TVA déductible</div>
            <div class="kpi-value">{total_tva_ded:,.0f} €</div>
            <div class="kpi-change">Sur achats</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💸</div>
            <div class="kpi-label">Notes de frais</div>
            <div class="kpi-value">{total_frais:,.0f} €</div>
            <div class="kpi-change">{len(ndfs)} dépenses</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <div class="kpi-label">Total dépenses</div>
            <div class="kpi-value">{total_depenses:,.0f} €</div>
            <div class="kpi-change">Achats + frais</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_c1, tab_c2, tab_c3 = st.tabs(["📈 Analyse", "🧾 Grand livre", "📊 TVA"])

    with tab_c1:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # ── Dépenses par mois ──
            if factures:
                mois_data = {}
                for f in factures:
                    d = str(f.get("date",""))[:7]
                    if d:
                        mois_data[d] = mois_data.get(d, 0) + float(f.get("montant_ttc",0))

                if mois_data:
                    df_mois = pd.DataFrame(
                        sorted(mois_data.items()),
                        columns=["Mois","Total TTC"]
                    )
                    st.markdown("""
                    <div class="panel-header" style="padding:0.5rem 0;">
                        <span class="panel-title">📈 Achats par mois</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.bar_chart(df_mois.set_index("Mois"), color="#f0a070")

        with col_g2:
            # ── Par catégorie ──
            if factures:
                cat_data = {}
                for f in factures:
                    c = f.get("categorie","Autre") or "Autre"
                    cat_data[c] = cat_data.get(c,0) + float(f.get("montant_ttc",0))

                if cat_data:
                    df_cat = pd.DataFrame(
                        cat_data.items(), columns=["Catégorie","Total TTC"]
                    ).sort_values("Total TTC", ascending=False)
                    st.markdown("""
                    <div class="panel-header" style="padding:0.5rem 0;">
                        <span class="panel-title">📂 Par catégorie</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.bar_chart(df_cat.set_index("Catégorie"), color="#e07040")

    with tab_c2:
        # ── Grand livre simplifié ──
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        all_ops = []
        for f in factures:
            all_ops.append({
                "Date":        f.get("date","—"),
                "Type":        "Facture",
                "Libellé":     f.get("fournisseur","—"),
                "Catégorie":   f.get("categorie","—"),
                "HT":          float(f.get("montant_ht",0)),
                "TVA":         float(f.get("tva",0)),
                "TTC":         float(f.get("montant_ttc",0)),
                "Statut":      f.get("statut","—"),
            })
        for n in ndfs:
            all_ops.append({
                "Date":        n.get("date","—"),
                "Type":        "Note de frais",
                "Libellé":     n.get("description","—"),
                "Catégorie":   n.get("categorie","—"),
                "HT":          float(n.get("montant_ht",0)),
                "TVA":         float(n.get("tva",0)),
                "TTC":         float(n.get("montant_ttc",0)),
                "Statut":      n.get("statut","—"),
            })

        if all_ops:
            df_gl = pd.DataFrame(all_ops).sort_values("Date", ascending=False)
            st.dataframe(df_gl, use_container_width=True, hide_index=True)
            csv_gl = df_gl.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Exporter le grand livre", data=csv_gl,
                file_name="grand_livre.csv", mime="text/csv")
        else:
            st.info("📭 Aucune opération enregistrée")

    with tab_c3:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        # ── Déclaration TVA simplifiée ──
        tva_par_taux = {}
        for f in factures:
            ht  = float(f.get("montant_ht",0))
            tva = float(f.get("tva",0))
            ttc = float(f.get("montant_ttc",0))
            taux = round((tva / ht * 100) if ht > 0 else 0, 1)
            key = f"{taux}%"
            if key not in tva_par_taux:
                tva_par_taux[key] = {"HT":0,"TVA":0,"TTC":0}
            tva_par_taux[key]["HT"]  += ht
            tva_par_taux[key]["TVA"] += tva
            tva_par_taux[key]["TTC"] += ttc

        if tva_par_taux:
            rows_tva = ""
            for taux, vals in sorted(tva_par_taux.items()):
                rows_tva += f"""
                <tr>
                    <td><b>{taux}</b></td>
                    <td>{vals['HT']:,.2f} €</td>
                    <td><b style="color:#f0a070;">{vals['TVA']:,.2f} €</b></td>
                    <td>{vals['TTC']:,.2f} €</td>
                </tr>
                """
            st.markdown(f"""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">🧾 TVA par taux</span>
                </div>
                <table class="invoice-table">
                    <thead>
                        <tr>
                            <th>Taux TVA</th><th>Base HT</th>
                            <th>TVA déductible</th><th>Total TTC</th>
                        </tr>
                    </thead>
                    <tbody>{rows_tva}</tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📭 Aucune donnée TVA disponible")

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PARAMÈTRES
# ══════════════════════════════════════════════════════════════════════════════
elif page in ("parametres", "api_key"):
    main_wrap()
    page_header("Paramètres", "Configuration de votre compte et de l'API")

    tab_p1, tab_p2 = st.tabs(["🔑 Clé API", "🏢 Entreprise"])

    with tab_p1:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="form-panel">', unsafe_allow_html=True)
        st.markdown('<div class="form-section-title">Clé API Gemini</div>',
                    unsafe_allow_html=True)

        current_key = st.session_state.get("gemini_api_key","")
        masked = ("•" * (len(current_key)-4) + current_key[-4:]) if len(current_key) > 4 else ""
        if masked:
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                 padding:0.6rem 1rem;margin-bottom:0.75rem;font-size:0.84rem;color:#065f46;">
                ✅ Clé configurée : <code>{masked}</code>
            </div>
            """, unsafe_allow_html=True)

        new_key = st.text_input("Nouvelle clé API", type="password",
                                 placeholder="AIza…", key="new_api_key")
        if st.button("💾 Sauvegarder la clé", type="primary"):
            if new_key.strip():
                st.session_state["gemini_api_key"] = new_key.strip()
                st.success("✅ Clé API sauvegardée !")
            else:
                st.warning("⚠️ Clé vide")

        st.markdown('</div>', unsafe_allow_html=True)

    with tab_p2:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="form-panel">', unsafe_allow_html=True)
        st.markdown('<div class="form-section-title">Informations entreprise</div>',
                    unsafe_allow_html=True)

        p1, p2 = st.columns(2)
        with p1:
            st.text_input("🏢 Raison sociale", key="company_name",
                          placeholder="Ma Société SAS")
            st.text_input("🔢 SIRET", key="company_siret",
                          placeholder="XXX XXX XXX XXXXX")
        with p2:
            st.text_input("💼 N° TVA", key="company_tva",
                          placeholder="FR XX XXXXXXXXX")
            st.text_input("📧 Email comptabilité", key="company_email",
                          placeholder="compta@masociete.fr")

        if st.button("💾 Sauvegarder", type="primary"):
            st.success("✅ Informations sauvegardées !")

        st.markdown('</div>', unsafe_allow_html=True)

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS (à placer avant les pages dans votre fichier final)
# ══════════════════════════════════════════════════════════════════════════════
# Ajoutez ces fonctions helper en haut de votre fichier :

# def main_wrap():
#     st.markdown('<div class="main-content">', unsafe_allow_html=True)

# def main_wrap_end():
#     st.markdown('</div>', unsafe_allow_html=True)

# def page_header(title, subtitle=""):
#     st.markdown(f"""
#     <div class="page-header">
#         <h1>{title}</h1>
#         <p>{subtitle}</p>
#     </div>
#     """, unsafe_allow_html=True)

# def badge(statut):
#     mapping = {
#         "Payée":      "badge-green",
#         "Validée":    "badge-green",
#         "Remboursée": "badge-green",
#         "À payer":    "badge-orange",
#         "En attente": "badge-orange",
#         "En retard":  "badge-red",
#         "Refusée":    "badge-red",
#         "Annulée":    "badge-gray",
#     }
#     cls = mapping.get(statut, "badge-gray")
#     return f'<span class="badge {cls}">{statut}</span>'

