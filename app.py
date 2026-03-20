# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS — EN PREMIER
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import json
import io
import pandas as pd
from datetime import datetime, date
import base64

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG PAGE — DOIT ÊTRE LE 1ER APPEL ST
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="FactureCat",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
# VOS IMPORTS MÉTIER (inchangés)
# ══════════════════════════════════════════════════════════════════════════════
from supabase import create_client
from PIL import Image
import google.generativeai as genai
# … vos autres imports existants …

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES GLOBALES
# ══════════════════════════════════════════════════════════════════════════════
CAT_ICONS = {
    "Transport":    "🚗",
    "Repas":        "🍽️",
    "Hébergement":  "🏨",
    "Matériel":     "💻",
    "Télécom":      "📱",
    "Formation":    "📚",
    "Autre":        "📦"
}

# ══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp { background: #f7f5f3 !important; }
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }

/* ---- SUPPRIMER TOUT LE VIDE STREAMLIT ---- */
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}
.stApp > div:first-child { padding: 0 !important; }
section.main > div { padding: 0 !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* ---- BOUTONS NAV INVISIBLES MAIS CLIQUABLES ---- */
.nav-btn-row {
    position: fixed; top: 0; left: 180px; right: 140px;
    height: 58px; display: flex; align-items: center;
    gap: 0.25rem; z-index: 1002;
}
.nav-btn-row .stButton > button {
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    box-shadow: none !important;
    height: 36px !important;
    padding: 0 0.9rem !important;
    font-size: 0.82rem !important;
    cursor: pointer !important;
}
.nav-btn-row .stButton > button:hover {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ---- TOPBAR + NAV ----


# ---- TOPBAR + NAV ----
nav_items = [
    ("dashboard",    "🏠 Tableau de bord"),
    ("factures",     "🧾 Factures"),
    ("notes_frais",  "💸 Notes de frais"),
    ("comptabilite", "📊 Comptabilité"),
    ("parametres",   "⚙️ Paramètres"),
]

page = st.session_state.get("page", "dashboard")

# HTML décoratif (pointer-events: none)
nav_html = ""
for k, label in nav_items:
    active = "active" if page == k else ""
    nav_html += f'<a class="{active}">{label}</a>'

# 1. CSS supplémentaire
st.markdown("""
<style>
/* Rend les boutons nav visibles au survol */
.nav-btn-row .stButton > button {
    background: transparent !important;
    border: none !important;
    color: #6b7280 !important;
    box-shadow: none !important;
    height: 36px !important;
    padding: 0 0.9rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
.nav-btn-row .stButton > button:hover {
    background: #f7f5f3 !important;
    color: #1a1a2e !important;
}

/* ---- MAIN CONTENT ---- */
.main-content { margin-top: 58px; padding: 2rem 2.5rem; min-height: calc(100vh - 58px); }
/* ... tout le reste du CSS ... */
</style>
""", unsafe_allow_html=True)

# 2. Topbar HTML décoratif
st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">&#x1F431; Facture<span>Cat</span></div>
    <nav class="topbar-nav">{nav_html}</nav>
    <div class="topbar-right">
        <div class="topbar-avatar">&#x1F431;</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Boutons Streamlit cliquables
st.markdown('<div class="nav-btn-row">', unsafe_allow_html=True)
cols = st.columns(len(nav_items))
for i, (k, label) in enumerate(nav_items):
    with cols[i]:
        if st.button(label, key=f"nav_{k}"):
            st.session_state["page"] = k
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# Boutons Streamlit RÉELS positionnés par-dessus la topbar
st.markdown('<div class="nav-btn-row">', unsafe_allow_html=True)
cols = st.columns(len(nav_items))
for i, (k, label) in enumerate(nav_items):
    with cols[i]:
        if st.button(label, key=f"nav_{k}"):
            st.session_state["page"] = k
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


/* ---- MAIN CONTENT ---- */
.main-content {
    margin-top: 58px;
    padding: 2rem 2.5rem;
    min-height: calc(100vh - 58px);
}

/* ---- PAGE HEADER ---- */
.page-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #ece9e4;
}
.page-header h1 {
    font-size: 1.5rem; font-weight: 800;
    color: #1a1a2e; margin: 0 0 0.25rem 0;
}
.page-header p { color: #6b7280; font-size: 0.84rem; margin: 0; }

/* ---- PANELS ---- */
.panel {
    background: white; border-radius: 14px;
    border: 1px solid #ece9e4;
    overflow: hidden; margin-bottom: 1rem;
}
.panel-header {
    padding: 0.9rem 1.2rem;
    border-bottom: 1px solid #f7f5f3;
    display: flex; align-items: center;
    justify-content: space-between;
}
.panel-title { font-size: 0.88rem; font-weight: 700; color: #1a1a2e; }
.panel-body { padding: 1rem 1.2rem; }

/* ---- KPI GRID ---- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}
.kpi-card {
    background: white; border-radius: 14px;
    border: 1px solid #ece9e4; padding: 1.2rem 1.5rem;
    transition: box-shadow 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
.kpi-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.kpi-label { font-size: 0.75rem; color: #9ca3af; font-weight: 500; margin-bottom: 0.25rem; }
.kpi-value { font-size: 1.6rem; font-weight: 800; color: #1a1a2e; line-height: 1; }
.kpi-change { font-size: 0.72rem; color: #9ca3af; margin-top: 0.35rem; }

/* ---- BADGES ---- */
.badge {
    display: inline-flex; align-items: center;
    padding: 0.2rem 0.6rem; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600;
}
.badge-green  { background: #dcfce7; color: #166534; }
.badge-orange { background: #fff7ed; color: #c2410c; }
.badge-red    { background: #fee2e2; color: #dc2626; }
.badge-gray   { background: #f3f4f6; color: #6b7280; }

/* ---- TABLE ---- */
.invoice-table {
    width: 100%; border-collapse: collapse; font-size: 0.82rem;
}
.invoice-table th {
    padding: 0.6rem 0.8rem; text-align: left;
    color: #9ca3af; font-weight: 600; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.05em;
    border-bottom: 1px solid #f3f4f6;
}
.invoice-table td {
    padding: 0.7rem 0.8rem;
    border-bottom: 1px solid #f9f8f7;
    color: #374151;
}
.invoice-table tr:last-child td { border-bottom: none; }
.invoice-table tr:hover td { background: #fafaf9; }

/* ---- FORM ---- */
.form-panel {
    background: white; border-radius: 14px;
    border: 1px solid #ece9e4; padding: 1.5rem;
    margin-bottom: 1rem;
}
.form-section-title {
    font-size: 0.82rem; font-weight: 700;
    color: #9ca3af; text-transform: uppercase;
    letter-spacing: 0.08em; margin-bottom: 1rem;
}

/* ---- UPLOAD ZONE ---- */
.upload-zone {
    background: white; border-radius: 14px;
    border: 2px dashed #e5e0d8; padding: 3rem 2rem;
    text-align: center; margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHATBOT FLOTTANT
# ══════════════════════════════════════════════════════════════════════════════

# FAB fixé en bas à droite via CSS — bouton Streamlit réel
st.markdown("""
<style>
/* Cache le container du bouton FAB et le repositionne */
div[data-testid="stVerticalBlock"]:has(> div > button[kind="secondary"]#chat_fab_btn) {
    position: fixed !important;
    bottom: 2rem !important;
    right: 2rem !important;
    z-index: 2000 !important;
    width: 56px !important;
}
/* Style du bouton FAB */
button[kind="secondary"]#chat_fab_btn,
div.stButton:has(button[key="chat_fab_btn"]) button {
    width: 56px !important;
    height: 56px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #f0a070, #e07040) !important;
    border: none !important;
    font-size: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(240,112,64,0.4) !important;
    padding: 0 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Conteneur fixe pour le FAB
st.markdown('<div style="position:fixed;bottom:2rem;right:2rem;z-index:2000;">', 
            unsafe_allow_html=True)
if st.button("🐱", key="chat_fab_btn"):
    st.session_state["chat_open"] = not st.session_state.get("chat_open", False)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# Fenêtre chat
if st.session_state.get("chat_open", False):
    st.markdown("""
    <div class="chat-window" style="
        position:fixed; bottom:5.5rem; right:2rem;
        width:340px; height:480px;
        background:white; border-radius:20px;
        box-shadow:0 20px 60px rgba(0,0,0,0.15);
        z-index:1999; display:flex; flex-direction:column;
        border:1px solid #ece9e4; overflow:hidden;">
        <div class="chat-header">
            <div style="font-size:1.5rem;">🐱</div>
            <div>
                <div class="chat-header-title">FactureCat</div>
                <div class="chat-header-sub">Assistant comptable IA 🐾</div>
            </div>
        </div>
        <div class="chat-messages">
    """, unsafe_allow_html=True)

    for msg in st.session_state.get("chat_messages", [])[-8:]:
        if msg["role"] == "bot":
            st.markdown(f"""
            <div class="msg-bot">
                <div style="font-size:1.2rem;">🐱</div>
                <div class="bubble">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-user">
                <div class="bubble">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # fin chat-messages

    col_inp, col_send = st.columns([4, 1])
    with col_inp:
        user_msg = st.text_input("", placeholder="Posez votre question…",
                                 key="chat_input", label_visibility="collapsed")
    with col_send:
        send = st.button("➤", key="chat_send")

    if send and user_msg.strip():
        st.session_state.setdefault("chat_messages", []).append(
            {"role": "user", "content": user_msg})
        # ← votre logique de réponse ici
        response = "Miaou ! Je traite votre question… 🐾"
        st.session_state["chat_messages"].append(
            {"role": "bot", "content": response})
        st.rerun()

   st.markdown('</div>', unsafe_allow_html=True)  # fin chat-window

st.markdown("""
<style>
/* ---- SCROLLBAR ---- */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e5e0d8; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def get_data(table: str) -> list:
    try:
        uid = st.session_state.get("user_id", "")
        res = get_supabase().table(table).select("*").eq("user_id", uid).execute()
        return res.data or []
    except Exception:
        return st.session_state.get(table, [])

def pdf_to_images(content: bytes) -> list:
    """Convertit un PDF en liste d'images PIL — votre fonction existante."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=content, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    return images

def analyse_facture_gemini(images: list, api_key: str) -> dict:
    """Votre fonction d'extraction existante — inchangée."""
    pass  # ← remplacez par votre code existant

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════

def main_wrap():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

def main_wrap_end():
    st.markdown('</div>', unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def badge(statut: str) -> str:
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
    cls = mapping.get(statut, "badge-gray")  # ← indentation corrigée
    return f'<span class="badge {cls}">{statut}</span>'

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
defaults = {
    "page":                  "dashboard",
    "chat_open":             False,
    "chat_messages":         [{"role": "bot",
                               "content": "Bonjour ! Je suis FactureCat 🐱\n"
                                          "Comment puis-je vous aider aujourd'hui ?"}],
    "resultats":             [],
    "current_preview":       None,
    "current_preview_name":  "",
    "selected_facture_idx":  None,
    "selected_ndf_idx":      None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state["page"]

nav_items = [
    ("dashboard",    "🏠 Tableau de bord"),
    ("factures",     "📄 Factures"),
    ("notes_frais",  "💸 Notes de frais"),
    ("comptabilite", "📊 Comptabilité"),
    ("parametres",   "⚙️ Paramètres"),
]

nav_html = "".join(
    f'<a href="#" class="{"active" if page == k else ""}" '
    f'onclick="window.location.href=\'?page={k}\'">{label}</a>'
    for k, label in nav_items
)

st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">🐱 Facture<span>Cat</span></div>
    <nav class="topbar-nav">{nav_html}</nav>
    <div class="topbar-right">
        <div class="topbar-avatar">🐱</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---- Navigation via query params ----
params = st.query_params
if "page" in params:
    st.session_state["page"] = params["page"]
    page = params["page"]

# ---- Boutons nav Streamlit (fallback fiable) ----
with st.sidebar:
    for k, label in nav_items:
        if st.button(label, key=f"nav_{k}", use_container_width=True):
            st.session_state["page"] = k
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHATBOT FLOTTANT
# ══════════════════════════════════════════════════════════════════════════════
col_fab1, col_fab2 = st.columns([10, 1])
with col_fab2:
    if st.button("🐱", key="chat_fab_btn", help="Ouvrir FactureCat"):
        st.session_state["chat_open"] = not st.session_state["chat_open"]
        st.rerun()

if st.session_state["chat_open"]:
    st.markdown("""
    <div class="chat-window">
        <div class="chat-header">
            <div style="font-size:1.5rem;">🐱</div>
            <div>
                <div class="chat-header-title">FactureCat</div>
                <div class="chat-header-sub">Assistant comptable IA 🐾</div>
            </div>
        </div>
        <div class="chat-messages">
    """, unsafe_allow_html=True)

    for msg in st.session_state["chat_messages"][-8:]:
        if msg["role"] == "bot":
            st.markdown(f"""
            <div class="msg-bot">
                <div style="font-size:1.2rem;">🐱</div>
                <div class="bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-user">
                <div class="bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # fin chat-messages

    col_inp, col_send = st.columns([4, 1])
    with col_inp:
        user_msg = st.text_input("", placeholder="Posez votre question…",
                                  key="chat_input", label_visibility="collapsed")
    with col_send:
        send = st.button("➤", key="chat_send")

    if send and user_msg.strip():
        st.session_state["chat_messages"].append(
            {"role": "user", "content": user_msg})

        msg_lower = user_msg.lower()
        if any(w in msg_lower for w in ["facture", "invoice"]):
            response = ("📄 Pour vos factures, allez dans **Factures** "
                        "et utilisez l'import IA. Je peux tout extraire "
                        "automatiquement ! 🐾")
        elif any(w in msg_lower for w in ["note", "frais", "dépense"]):
            response = ("💸 Les notes de frais se gèrent dans la section dédiée. "
                        "Catégorisez et exportez facilement ! 🐱")
        elif any(w in msg_lower for w in ["comptabilité", "bilan", "tva"]):
            response = ("📊 La Comptabilité vous donne une vue consolidée "
                        "des charges, TVA et grand livre 🐾")
        elif any(w in msg_lower for w in ["export", "csv", "json", "télécharger"]):
            response = ("📥 L'export CSV et JSON est disponible dans chaque "
                        "section via l'onglet Export 🐱")
        elif any(w in msg_lower for w in ["bonjour", "salut", "hello", "coucou"]):
            response = ("Bonjour ! 🐱 Je suis FactureCat, votre assistant "
                        "comptable félin. Que puis-je faire pour vous ?")
        elif any(w in msg_lower for w in ["merci", "thanks"]):
            response = "Avec plaisir ! N'hésitez pas 🐾 Miaou~"
        elif any(w in msg_lower for w in ["api", "clé", "gemini"]):
            response = ("🔑 Configurez votre clé Gemini dans **Paramètres > "
                        "Clé API**. Elle sera utilisée pour l'extraction IA !")
        else:
            response = ("🐱 Je ne suis pas sûr de comprendre… "
                        "Essayez de me parler de vos factures, "
                        "notes de frais ou de la comptabilité !")

        st.session_state["chat_messages"].append(
            {"role": "bot", "content": response})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  # fin chat-window

# ══════════════════════════════════════════════════════════════════════════════
# ROUTING PAGES
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    main_wrap()
    page_header("Tableau de bord", "Bienvenue sur FactureCat 🐱")

    factures = get_data("factures")
    ndfs     = get_data("notes_frais")

    total_ttc    = sum(float(f.get("montant_ttc", 0)) for f in factures)
    total_tva    = sum(float(f.get("tva", 0))         for f in factures)
    total_frais  = sum(float(n.get("montant_ttc", 0)) for n in ndfs)
    nb_attente   = sum(1 for f in factures if f.get("statut") in ("À payer", "En attente"))

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">🧾</div>
            <div class="kpi-label">Total factures TTC</div>
            <div class="kpi-value">{total_ttc:,.0f} €</div>
            <div class="kpi-change">{len(factures)} factures</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">TVA déductible</div>
            <div class="kpi-value">{total_tva:,.0f} €</div>
            <div class="kpi-change">Sur toutes factures</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💸</div>
            <div class="kpi-label">Notes de frais</div>
            <div class="kpi-value">{total_frais:,.0f} €</div>
            <div class="kpi-change">{len(ndfs)} dépenses</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⏳</div>
            <div class="kpi-label">En attente</div>
            <div class="kpi-value">{nb_attente}</div>
            <div class="kpi-change">Factures à traiter</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([3, 2])

    with col_d1:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">📄 Dernières factures</span>
            </div>
        """, unsafe_allow_html=True)

        if factures:
            rows = ""
            for f in sorted(factures,
                            key=lambda x: str(x.get("date", "")),
                            reverse=True)[:5]:
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
                        <th>Date</th><th>TTC</th><th>Statut</th>
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

    with col_d2:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">🏷️ Statuts</span>
            </div>
            <div class="panel-body">
        """, unsafe_allow_html=True)

        statuts_count = {}
        for f in factures:
            s = f.get("statut", "—")
            statuts_count[s] = statuts_count.get(s, 0) + 1

        if statuts_count:
            for s, count in statuts_count.items():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                     align-items:center;padding:0.4rem 0;
                     border-bottom:1px solid #f7f5f3;">
                    {badge(s)}
                    <span style="font-size:0.82rem;font-weight:700;
                           color:#374151;">{count}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#9ca3af;font-size:0.84rem;">Aucune donnée</p>',
                        unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

        # ---- Raccourcis rapides ----
        st.markdown("""
        <div class="panel" style="margin-top:1rem;">
            <div class="panel-header">
                <span class="panel-title">⚡ Accès rapide</span>
            </div>
            <div class="panel-body">
        """, unsafe_allow_html=True)

        if st.button("📤 Importer des factures",
                     use_container_width=True, key="dash_import"):
            st.session_state["page"] = "factures"
            st.rerun()
        if st.button("💸 Nouvelle note de frais",
                     use_container_width=True, key="dash_ndf"):
            st.session_state["page"] = "notes_frais"
            st.rerun()
        if st.button("📊 Voir la comptabilité",
                     use_container_width=True, key="dash_compta"):
            st.session_state["page"] = "comptabilite"
            st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "factures":
    main_wrap()
    page_header("Factures", "Import, analyse IA et suivi de vos factures")

    tab1, tab2, tab3 = st.tabs(["📤 Import & Analyse", "📋 Liste & Aperçu", "📊 Export"])

    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

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
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;
                     border-radius:10px;padding:0.75rem 1rem;margin:0.75rem 0;
                     font-size:0.84rem;color:#065f46;">
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
                    if st.session_state["current_preview"]:
                        for img in st.session_state["current_preview"][:2]:
                            st.image(img, use_column_width=True)

                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1, 2, 1])
                with b2:
                    analyse_btn = st.button(
                        "🐱 Analyser avec Gemini IA",
                        use_container_width=True,
                        type="primary",
                        key="btn_analyse"
                    )

                if analyse_btn:
                    api_key = st.session_state.get("gemini_api_key", "")
                    if not api_key:
                        st.error("❌ Clé API Gemini manquante — allez dans Paramètres")
                    else:
                        results = []
                        with st.status("🐱 Analyse en cours…", expanded=True) as status:
                            for f in new_files:
                                st.write(f"📄 Analyse de **{f.name}**…")
                                f.seek(0)
                                content = f.read()
                                f.seek(0)
                                if f.name.lower().endswith(".pdf"):
                                    images = pdf_to_images(content)
                                else:
                                    images = [Image.open(io.BytesIO(content))]
                                result = analyse_facture_gemini(images, api_key)
                                result["fichier"] = f.name
                                results.append((f.name, result, images))

                            saved = 0
                            for fname, result, images in results:
                                if fname == st.session_state.get("current_preview_name",""):
                                    st.session_state["current_preview"] = images
                                try:
                                    uid = st.session_state.get("user_id", "")
                                    get_supabase().table("factures").insert(
                                        {**result, "user_id": uid}
                                    ).execute()
                                    saved += 1
                                except Exception:
                                    st.session_state["resultats"].append(result)
                                    saved += 1

                            status.success(
                                f"✅ {saved} facture(s) analysée(s) et sauvegardée(s) !")

                        st.markdown("---")
                        for fname, result, _ in results:
                            with st.expander(f"📄 {fname}", expanded=True):
                                c1, c2, c3 = st.columns(3)
                                fields_c1 = [
                                    ("🏢 Fournisseur", result.get("fournisseur","—")),
                                    ("🔢 N° Facture",  result.get("numero","—")),
                                    ("📅 Date",        result.get("date","—")),
                                ]
                                fields_c2 = [
                                    ("💵 HT",  f"{float(result.get('montant_ht',0)):.2f} €"),
                                    ("📊 TVA", f"{float(result.get('tva',0)):.2f} €"),
                                    ("💰 TTC", f"{float(result.get('montant_ttc',0)):.2f} €"),
                                ]
                                fields_c3 = [
                                    ("📂 Catégorie", result.get("categorie","—")),
                                    ("🏷️ Statut",    result.get("statut","—")),
                                ]
                                for col_r, fields in [
                                    (c1, fields_c1),
                                    (c2, fields_c2),
                                    (c3, fields_c3)
                                ]:
                                    with col_r:
                                        for lbl, val in fields:
                                            st.markdown(f"""
                                            <div style="margin-bottom:0.5rem;">
                                                <div style="font-size:0.7rem;color:#9ca3af;
                                                     font-weight:600;">{lbl}</div>
                                                <div style="font-size:0.9rem;font-weight:700;
                                                     color:#1a1a2e;">{val}</div>
                                            </div>
                                            """, unsafe_allow_html=True)
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
        else:
            st.markdown("""
            <div class="upload-zone">
                <div style="font-size:3rem;margin-bottom:1rem;">🐱</div>
                <p style="font-weight:700;color:#1a1a2e;font-size:1rem;margin:0;">
                    Glissez vos factures ici
                </p>
                <p style="color:#9ca3af;font-size:0.84rem;margin:0.5rem 0 0 0;">
                    PDF, PNG, JPG, JPEG acceptés
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        factures = get_data("factures")

        if factures:
            f1, f2, f3 = st.columns(3)
            with f1:
                search = st.text_input("🔍 Rechercher",
                                        placeholder="Fournisseur, numéro…",
                                        key="fac_search")
            with f2:
                all_statuts = ["Tous"] + sorted(set(f.get("statut","") for f in factures))
                flt_statut  = st.selectbox("Statut", all_statuts, key="fac_statut")
            with f3:
                all_cats = ["Toutes"] + sorted(set(f.get("categorie","") for f in factures))
                flt_cat  = st.selectbox("Catégorie", all_cats, key="fac_cat")

            filtered = [
                f for f in factures
                if (not search or
                    search.lower() in str(f.get("fournisseur","")).lower() or
                    search.lower() in str(f.get("numero","")).lower())
                and (flt_statut == "Tous" or f.get("statut") == flt_statut)
                and (flt_cat == "Toutes" or f.get("categorie") == flt_cat)
            ]
            
            filtered.sort(key=lambda x: str(x.get("date","")), reverse=True)

            col_list, col_detail = st.columns([5, 4])

            with col_list:
                rows = ""
                for f in filtered:
                    rows += f"""
                    <tr>
                        <td>
                            <b style="color:#1a1a2e;">{f.get('fournisseur','—')}</b><br>
                            <span style="color:#9ca3af;font-size:0.72rem;">
                                {f.get('numero','—')}
                            </span>
                        </td>
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
                                <th>TTC</th><th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                if filtered:
                    sel_names = [
                        f"{f.get('fournisseur','—')} · "
                        f"{f.get('date','—')} · "
                        f"{float(f.get('montant_ttc',0)):,.2f} €"
                        for f in filtered
                    ]
                    sel = st.selectbox(
                        "Sélectionner une facture",
                        options=range(len(filtered)),
                        format_func=lambda i: sel_names[i],
                        key="fac_sel_box"
                    )
                    st.session_state["selected_facture_idx"] = sel

            with col_detail:
                idx = st.session_state.get("selected_facture_idx")
                if idx is not None and idx < len(filtered):
                    r = filtered[idx]
                    st.markdown(f"""
                    <div class="panel">
                        <div class="panel-header">
                            <span class="panel-title">
                                🧾 {r.get('fournisseur','—')}
                            </span>
                            {badge(r.get('statut','—'))}
                        </div>
                        <div class="panel-body">
                    """, unsafe_allow_html=True)

                    for lbl, val in [
                        ("N° Facture",   r.get("numero","—")),
                        ("Date",         r.get("date","—")),
                        ("Fournisseur",  r.get("fournisseur","—")),
                        ("Catégorie",    r.get("categorie","—")),
                        ("Montant HT",   f"{float(r.get('montant_ht',0)):,.2f} €"),
                        ("TVA",          f"{float(r.get('tva',0)):,.2f} €"),
                        ("Montant TTC",  f"{float(r.get('montant_ttc',0)):,.2f} €"),
                    ]:
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                             padding:0.5rem 0;border-bottom:1px solid #f7f5f3;">
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
                        new_statut = st.selectbox("Changer statut",
                            ["À payer","Payée","En retard","Annulée"],
                            key=f"statut_{idx}")
                    with a2:
                        if st.button("💾 Sauvegarder",
                                     key=f"save_{idx}",
                                     use_container_width=True,
                                     type="primary"):
                            try:
                                get_supabase().table("factures").update(
                                    {"statut": new_statut}
                                ).eq("id", r["id"]).execute()
                                st.success("✅ Mis à jour")
                                st.rerun()
                            except Exception:
                                st.error("❌ Erreur")
                    with a3:
                        if st.button("🗑️ Supprimer",
                                     key=f"del_{idx}",
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
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:14px;border:1px solid #ece9e4;">
                <div style="font-size:3rem;">📭</div>
                <h3 style="color:#1a1a2e;">Aucune facture</h3>
                <p style="color:#9ca3af;">
                    Importez vos premières factures dans l'onglet Import
                </p>
            </div>
            """, unsafe_allow_html=True)

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
                    file_name="factures.csv", mime="text/csv",
                    use_container_width=True)
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
                    list(CAT_ICONS.keys()), key="ndf_cat")

            ndf_desc = st.text_input("📝 Description", key="ndf_desc",
                                     placeholder="Ex: Déjeuner client Paris")

            c3, c4 = st.columns(2)
            with c3:
                ndf_ht = st.number_input("💵 Montant HT (€)",
                                          min_value=0.0, step=0.01, key="ndf_ht")
            with c4:
                ndf_tva_pct = st.selectbox("📊 TVA",
                    ["20%", "10%", "5.5%", "0%"], key="ndf_tva")

            tva_val         = float(ndf_tva_pct.replace("%", "")) / 100
            ndf_tva_montant = round(ndf_ht * tva_val, 2)
            ndf_ttc         = round(ndf_ht + ndf_tva_montant, 2)

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
                    <div style="font-size:0.7rem;color:#6b7280;font-weight:600;">
                        TOTAL TTC
                    </div>
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
                        uid = st.session_state.get("user_id", "")
                        get_supabase().table("notes_frais").insert(
                            {**ndf_data, "user_id": uid}
                        ).execute()
                        st.success("✅ Dépense enregistrée !")
                        st.rerun()
                    except Exception:
                        if "notes_frais" not in st.session_state:
                            st.session_state["notes_frais"] = []
                        st.session_state["notes_frais"].append(ndf_data)
                        st.success("✅ Dépense enregistrée localement !")
                        st.rerun()

        with col_side:
            ndfs     = get_data("notes_frais")
            mois     = datetime.now().month
            annee    = datetime.now().year
            ndfs_mois = [
                n for n in ndfs
                if str(n.get("date","")).startswith(f"{annee}-{mois:02d}")
            ]
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
                    <div style="display:flex;justify-content:space-between;padding:0.6rem 0;">
                        <span style="font-size:0.8rem;color:#9ca3af;">Nb dépenses</span>
                        <span style="font-weight:700;color:#1a1a2e;">{len(ndfs_mois)}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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

                for cat, total in sorted(cats_total.items(),
                                          key=lambda x: x[1], reverse=True):
                    pct  = (total / total_mois * 100) if total_mois > 0 else 0
                    icon = CAT_ICONS.get(cat, "📦")
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

    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        ndfs = get_data("notes_frais")

        if ndfs:
            f1, f2, f3 = st.columns(3)
            with f1:
                search_ndf = st.text_input("🔍 Rechercher",
                    placeholder="Description…", key="ndf_search")
            with f2:
                cats_ndf = ["Toutes"] + sorted(set(n.get("categorie","") for n in ndfs))
                cat_ndf_filter = st.selectbox("Catégorie", cats_ndf, key="ndf_cat_filter")
            with f3:
                stats_ndf = ["Tous"] + sorted(set(n.get("statut","") for n in ndfs))
                stat_ndf_filter = st.selectbox("Statut", stats_ndf, key="ndf_stat_filter")

            filtered_ndf = [
                n for n in ndfs
                if (not search_ndf or
                    search_ndf.lower() in str(n.get("description","")).lower())
                and (cat_ndf_filter == "Toutes" or n.get("categorie") == cat_ndf_filter)
                and (stat_ndf_filter == "Tous"  or n.get("statut") == stat_ndf_filter)
            ]
            filtered_ndf.sort(key=lambda x: str(x.get("date", "")), reverse=True)

            col_nl, col_nv = st.columns([5, 4])

            with col_nl:
                rows_ndf = ""
                for n in filtered_ndf:
                    icon = CAT_ICONS.get(n.get("categorie", "Autre"), "📦")
                    rows_ndf += f"""
                    <tr>
                        <td>
                            <b style="color:#1a1a2e;">{icon} {n.get('description','—')}</b><br>
                            <span style="color:#9ca3af;font-size:0.72rem;">
                                {n.get('categorie','—')}
                            </span>
                        </td>
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
                                <th>Description</th><th>Date</th>
                                <th>TTC</th><th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>{rows_ndf}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                if filtered_ndf:
                    sel_ndf_names = [
                        f"{CAT_ICONS.get(n.get('categorie','Autre'),'📦')} "
                        f"{n.get('description','—')} · {n.get('date','—')} · "
                        f"{float(n.get('montant_ttc',0)):,.2f} €"
                        for n in filtered_ndf
                    ]
                    sel_ndf = st.selectbox(
                        "Sélectionner une dépense",
                        options=range(len(filtered_ndf)),
                        format_func=lambda i: sel_ndf_names[i],
                        key="ndf_sel_box"
                    )
                    st.session_state["selected_ndf_idx"] = sel_ndf

            with col_nv:
                sel_ndf_idx = st.session_state.get("selected_ndf_idx")
                if sel_ndf_idx is not None and sel_ndf_idx < len(filtered_ndf):
                    n = filtered_ndf[sel_ndf_idx]
                    icon = CAT_ICONS.get(n.get("categorie", "Autre"), "📦")
                    st.markdown(f"""
                    <div class="panel">
                        <div class="panel-header">
                            <span class="panel-title">
                                {icon} {n.get('description','—')}
                            </span>
                            {badge(n.get('statut','—'))}
                        </div>
                        <div class="panel-body">
                    """, unsafe_allow_html=True)

                    for lbl, val in [
                        ("Date",            n.get("date","—")),
                        ("Catégorie",       n.get("categorie","—")),
                        ("Moyen paiement",  n.get("moyen_paiement","—")),
                        ("Montant HT",      f"{float(n.get('montant_ht',0)):,.2f} €"),
                        ("TVA",             f"{float(n.get('tva',0)):,.2f} €"),
                        ("Montant TTC",     f"{float(n.get('montant_ttc',0)):,.2f} €"),
                        ("Justificatif",    n.get("justificatif","—")),
                    ]:
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                             padding:0.5rem 0;border-bottom:1px solid #f7f5f3;">
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
                        new_ndf_statut = st.selectbox(
                            "Changer statut",
                            ["En attente","Validée","Remboursée","Refusée"],
                            key=f"ndf_statut_{sel_ndf_idx}"
                        )
                    with na2:
                        if st.button("💾 Sauvegarder",
                                     key=f"ndf_save_{sel_ndf_idx}",
                                     use_container_width=True,
                                     type="primary"):
                            try:
                                get_supabase().table("notes_frais").update(
                                    {"statut": new_ndf_statut}
                                ).eq("id", n["id"]).execute()
                                st.success("✅ Mis à jour")
                                st.rerun()
                            except Exception:
                                st.error("❌ Erreur mise à jour")
                    with na3:
                        if st.button("🗑️ Supprimer",
                                     key=f"ndf_del_{sel_ndf_idx}",
                                     use_container_width=True):
                            try:
                                get_supabase().table("notes_frais").delete().eq(
                                    "id", n["id"]).execute()
                                st.session_state["selected_ndf_idx"] = None
                                st.rerun()
                            except Exception:
                                # Suppression locale
                                local = st.session_state.get("notes_frais", [])
                                st.session_state["notes_frais"] = [
                                    x for x in local
                                    if x.get("description") != n.get("description")
                                ]
                                st.session_state["selected_ndf_idx"] = None
                                st.rerun()
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
                <h3 style="color:#1a1a2e;">Aucune note de frais</h3>
                <p style="color:#9ca3af;">
                    Ajoutez votre première dépense dans l'onglet Nouvelle dépense
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        ndfs = get_data("notes_frais")
        if ndfs:
            df_ndf = pd.DataFrame(ndfs)
            st.dataframe(df_ndf, use_container_width=True, hide_index=True)
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            with e1:
                csv_ndf = df_ndf.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Télécharger CSV", data=csv_ndf,
                    file_name="notes_frais.csv", mime="text/csv",
                    use_container_width=True)
            with e2:
                json_ndf = json.dumps(ndfs, ensure_ascii=False, indent=2)
                st.download_button("📥 Télécharger JSON", data=json_ndf,
                    file_name="notes_frais.json", mime="application/json",
                    use_container_width=True)
        else:
            st.info("📭 Aucune note de frais à exporter")

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPTABILITÉ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "comptabilite":
    main_wrap()
    page_header("Comptabilité", "Vue consolidée de vos charges, TVA et grand livre")

    factures = get_data("factures")
    ndfs     = get_data("notes_frais")

    total_fac_ht  = sum(float(f.get("montant_ht",  0)) for f in factures)
    total_fac_tva = sum(float(f.get("tva",          0)) for f in factures)
    total_fac_ttc = sum(float(f.get("montant_ttc",  0)) for f in factures)
    total_ndf_ttc = sum(float(n.get("montant_ttc",  0)) for n in ndfs)
    total_charges = total_fac_ttc + total_ndf_ttc

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">📥</div>
            <div class="kpi-label">Total charges HT</div>
            <div class="kpi-value">{total_fac_ht:,.0f} €</div>
            <div class="kpi-change">Factures fournisseurs</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🧾</div>
            <div class="kpi-label">TVA déductible</div>
            <div class="kpi-value">{total_fac_tva:,.0f} €</div>
            <div class="kpi-change">À récupérer</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💸</div>
            <div class="kpi-label">Notes de frais</div>
            <div class="kpi-value">{total_ndf_ttc:,.0f} €</div>
            <div class="kpi-change">{len(ndfs)} dépenses</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Total charges TTC</div>
            <div class="kpi-value">{total_charges:,.0f} €</div>
            <div class="kpi-change">Factures + frais</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_c1, tab_c2, tab_c3 = st.tabs(["📈 Graphiques", "📒 Grand livre", "🧾 TVA"])

    with tab_c1:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Répartition par catégorie
            cats_fac = {}
            for f in factures:
                c = f.get("categorie", "Autre")
                cats_fac[c] = cats_fac.get(c, 0) + float(f.get("montant_ht", 0))

            if cats_fac:
                df_cats = pd.DataFrame(
                    list(cats_fac.items()), columns=["Catégorie", "Montant HT"]
                ).sort_values("Montant HT", ascending=False)

                st.markdown("""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">📂 Charges par catégorie</span>
                    </div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)
                st.bar_chart(df_cats.set_index("Catégorie"), use_container_width=True)
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("📭 Aucune donnée")

        with col_g2:
            # Évolution mensuelle
            monthly = {}
            for f in factures:
                d = str(f.get("date", ""))
                if len(d) >= 7:
                    mois_key = d[:7]
                    monthly[mois_key] = monthly.get(mois_key, 0) + float(
                        f.get("montant_ttc", 0))

            if monthly:
                df_monthly = pd.DataFrame(
                    sorted(monthly.items()), columns=["Mois", "TTC"]
                )
                st.markdown("""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">📅 Évolution mensuelle TTC</span>
                    </div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)
                st.line_chart(df_monthly.set_index("Mois"), use_container_width=True)
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("📭 Aucune donnée mensuelle")

        # Répartition statuts
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            statuts_count = {}
            for f in factures:
                s = f.get("statut", "Inconnu")
                statuts_count[s] = statuts_count.get(s, 0) + 1
            if statuts_count:
                df_statuts = pd.DataFrame(
                    list(statuts_count.items()), columns=["Statut", "Nombre"]
                )
                st.markdown("""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">🏷️ Répartition par statut</span>
                    </div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)
                st.bar_chart(df_statuts.set_index("Statut"), use_container_width=True)
                st.markdown('</div></div>', unsafe_allow_html=True)

        with col_g4:
            # Frais vs factures
            if total_fac_ttc > 0 or total_ndf_ttc > 0:
                df_rep = pd.DataFrame({
                    "Type":    ["Factures", "Notes de frais"],
                    "Montant": [total_fac_ttc, total_ndf_ttc]
                })
                st.markdown("""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">⚖️ Factures vs Notes de frais</span>
                    </div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)
                st.bar_chart(df_rep.set_index("Type"), use_container_width=True)
                st.markdown('</div></div>', unsafe_allow_html=True)

    with tab_c2:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        all_ops = []

        for f in factures:
            all_ops.append({
                "Date":      f.get("date","—"),
                "Type":      "Facture",
                "Libellé":   f.get("fournisseur","—"),
                "Catégorie": f.get("categorie","—"),
                "HT":        float(f.get("montant_ht",0)),
                "TVA":       float(f.get("tva",0)),
                "TTC":       float(f.get("montant_ttc",0)),
                "Statut":    f.get("statut","—"),
            })

        for n in ndfs:
            all_ops.append({
                "Date":      n.get("date","—"),
                "Type":      "Note de frais",
                "Libellé":   n.get("description","—"),
                "Catégorie": n.get("categorie","—"),
                "HT":        float(n.get("montant_ht",0)),
                "TVA":       float(n.get("tva",0)),
                "TTC":       float(n.get("montant_ttc",0)),
                "Statut":    n.get("statut","—"),
            })

        if all_ops:
            all_ops.sort(key=lambda x: str(x.get("Date","")), reverse=True)
            rows_gl = ""
            for op in all_ops:
                type_badge = (
                    '<span class="badge badge-green">Facture</span>'
                    if op["Type"] == "Facture"
                    else '<span class="badge badge-orange">Note de frais</span>'
                )
                rows_gl += f"""
                <tr>
                    <td>{op['Date']}</td>
                    <td>{type_badge}</td>
                    <td><b style="color:#1a1a2e;">{op['Libellé']}</b></td>
                    <td>{op['Catégorie']}</td>
                    <td style="color:#6b7280;">{op['HT']:,.2f} €</td>
                    <td style="color:#f0a070;">{op['TVA']:,.2f} €</td>
                    <td><b>{op['TTC']:,.2f} €</b></td>
                    <td>{badge(op['Statut'])}</td>
                </tr>
                """

            st.markdown(f"""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">📒 Grand livre consolidé</span>
                    <span style="font-size:0.8rem;color:#9ca3af;">
                        {len(all_ops)} opérations
                    </span>
                </div>
                <table class="invoice-table">
                    <thead>
                        <tr>
                            <th>Date</th><th>Type</th><th>Libellé</th>
                            <th>Catégorie</th><th>HT</th><th>TVA</th>
                            <th>TTC</th><th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>{rows_gl}</tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)

            # Export grand livre
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            df_gl = pd.DataFrame(all_ops)
            e1, e2 = st.columns(2)
            with e1:
                csv_gl = df_gl.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Export CSV Grand livre",
                    data=csv_gl, file_name="grand_livre.csv",
                    mime="text/csv", use_container_width=True)
            with e2:
                json_gl = json.dumps(all_ops, ensure_ascii=False, indent=2)
                st.download_button("📥 Export JSON Grand livre",
                    data=json_gl, file_name="grand_livre.json",
                    mime="application/json", use_container_width=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:14px;border:1px solid #ece9e4;">
                <div style="font-size:3rem;">📭</div>
                <h3 style="color:#1a1a2e;">Grand livre vide</h3>
                <p style="color:#9ca3af;">
                    Importez des factures ou ajoutez des notes de frais
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab_c3:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        tva_par_taux = {}
        for f in factures:
            ht  = float(f.get("montant_ht",  0))
            tva = float(f.get("tva",          0))
            ttc = float(f.get("montant_ttc",  0))
            if ht > 0 and tva > 0:
                pct = round((tva / ht) * 100)
                taux_lbl = f"{pct}%"
                if taux_lbl not in tva_par_taux:
                    tva_par_taux[taux_lbl] = {"HT": 0.0, "TVA": 0.0, "TTC": 0.0}
                tva_par_taux[taux_lbl]["HT"]  += ht
                tva_par_taux[taux_lbl]["TVA"] += tva
                tva_par_taux[taux_lbl]["TTC"] += ttc

        # Ajouter TVA des notes de frais
        for n in ndfs:
            ht  = float(n.get("montant_ht", 0))
            tva = float(n.get("tva",         0))
            ttc = float(n.get("montant_ttc", 0))
            if ht > 0 and tva > 0:
                pct = round((tva / ht) * 100)
                taux_lbl = f"{pct}%"
                if taux_lbl not in tva_par_taux:
                    tva_par_taux[taux_lbl] = {"HT": 0.0, "TVA": 0.0, "TTC": 0.0}
                tva_par_taux[taux_lbl]["HT"]  += ht
                tva_par_taux[taux_lbl]["TVA"] += tva
                tva_par_taux[taux_lbl]["TTC"] += ttc

        if tva_par_taux:
            total_tva_all = sum(v["TVA"] for v in tva_par_taux.values())
            total_ht_all  = sum(v["HT"]  for v in tva_par_taux.values())
            total_ttc_all = sum(v["TTC"] for v in tva_par_taux.values())

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
            # Ligne total
            rows_tva += f"""
            <tr style="background:#fff8f3;font-weight:700;">
                <td>TOTAL</td>
                <td>{total_ht_all:,.2f} €</td>
                <td style="color:#f0a070;">{total_tva_all:,.2f} €</td>
                <td>{total_ttc_all:,.2f} €</td>
            </tr>
            """
            st.markdown(f"""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">🧾 Déclaration TVA par taux</span>
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

            # Récap TVA à déclarer
            st.markdown(f"""
            <div style="background:#fff8f3;border:1px solid #fed7aa;border-radius:12px;
                 padding:1.2rem 1.5rem;margin-top:1rem;display:flex;gap:3rem;
                 align-items:center;">
                <div>
                    <div style="font-size:0.72rem;color:#9ca3af;font-weight:600;
                         text-transform:uppercase;letter-spacing:0.05em;">
                        TVA TOTALE À RÉCUPÉRER
                    </div>
                    <div style="font-size:2rem;font-weight:800;color:#f0a070;">
                        {total_tva_all:,.2f} €
                    </div>
                </div>
                <div style="width:1px;background:#fed7aa;height:50px;"></div>
                <div>
                    <div style="font-size:0.72rem;color:#9ca3af;font-weight:600;
                         text-transform:uppercase;letter-spacing:0.05em;">
                        BASE HT TOTALE
                    </div>
                    <div style="font-size:2rem;font-weight:800;color:#1a1a2e;">
                        {total_ht_all:,.2f} €
                    </div>
                </div>
                <div style="width:1px;background:#fed7aa;height:50px;"></div>
                <div>
                    <div style="font-size:0.72rem;color:#9ca3af;font-weight:600;
                         text-transform:uppercase;letter-spacing:0.05em;">
                        TAUX EFFECTIF MOYEN
                    </div>
                    <div style="font-size:2rem;font-weight:800;color:#1a1a2e;">
                        {(total_tva_all/total_ht_all*100) if total_ht_all > 0 else 0:.1f}%
                    </div>
                </div>
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

    tab_p1, tab_p2, tab_p3 = st.tabs(["🔑 Clé API", "🏢 Entreprise", "🗄️ Données"])

    with tab_p1:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="form-panel">', unsafe_allow_html=True)
        st.markdown('<div class="form-section-title">Configuration Gemini API</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#fff8f3;border:1px solid #fed7aa;border-radius:10px;
             padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.82rem;color:#92400e;">
            🔑 Votre clé API Gemini est nécessaire pour l'extraction automatique 
            des factures. Obtenez-la sur 
            <b>https://aistudio.google.com/app/apikey</b>
        </div>
        """, unsafe_allow_html=True)

        current_key = st.session_state.get("api_key", "")
        new_key = st.text_input(
            "🔑 Clé API Gemini",
            value=current_key,
            type="password",
            placeholder="AIza...",
            key="api_key_input"
        )

        p1, p2, p3 = st.columns([1, 2, 1])
        with p2:
            if st.button("💾 Sauvegarder la clé API",
                         type="primary", use_container_width=True):
                if new_key.strip():
                    st.session_state["api_key"] = new_key.strip()
                    st.success("✅ Clé API sauvegardée !")
                else:
                    st.warning("⚠️ Veuillez saisir une clé valide")

        st.markdown('</div>', unsafe_allow_html=True)

        # Test de la clé
        if st.session_state.get("api_key"):
            st.markdown("""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                 padding:0.75rem 1rem;font-size:0.82rem;color:#166534;
                 display:flex;align-items:center;gap:0.5rem;">
                ✅ <b>Clé API configurée</b> — L'extraction IA est disponible
            </div>
            """, unsafe_allow_html=True)

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
            st.text_input("📍 Adresse", key="company_adresse",
                          placeholder="1 rue de la Paix, 75001 Paris")
        with p2:
            st.text_input("💼 N° TVA intracommunautaire", key="company_tva",
                          placeholder="FR XX XXXXXXXXX")
            st.text_input("📧 Email comptabilité", key="company_email",
                          placeholder="compta@masociete.fr")
            st.text_input("☎️ Téléphone", key="company_tel",
                          placeholder="+33 1 XX XX XX XX")

        pp1, pp2, pp3 = st.columns([1, 2, 1])
        with pp2:
            if st.button("💾 Sauvegarder les informations",
                         type="primary", use_container_width=True, key="save_company"):
                st.success("✅ Informations sauvegardées !")

        st.markdown('</div>', unsafe_allow_html=True)

    with tab_p3:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="form-panel">', unsafe_allow_html=True)
        st.markdown('<div class="form-section-title">Gestion des données</div>',
                    unsafe_allow_html=True)

        factures = get_data("factures")
        ndfs     = get_data("notes_frais")

        st.markdown(f"""
        <div style="display:flex;gap:2rem;margin-bottom:1rem;">
            <div style="text-align:center;flex:1;background:#f7f5f3;
                 border-radius:10px;padding:1rem;">
                <div style="font-size:2rem;font-weight:800;color:#1a1a2e;">
                    {len(factures)}
                </div>
                <div style="font-size:0.8rem;color:#9ca3af;">Factures</div>
            </div>
            <div style="text-align:center;flex:1;background:#f7f5f3;
                 border-radius:10px;padding:1rem;">
                <div style="font-size:2rem;font-weight:800;color:#1a1a2e;">
                    {len(ndfs)}
                </div>
                <div style="font-size:0.8rem;color:#9ca3af;">Notes de frais</div>
            </div>
            <div style="text-align:center;flex:1;background:#f7f5f3;
                 border-radius:10px;padding:1rem;">
                <div style="font-size:2rem;font-weight:800;color:#f0a070;">
                    {len(factures) + len(ndfs)}
                </div>
                <div style="font-size:0.8rem;color:#9ca3af;">Total opérations</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
             padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.82rem;color:#dc2626;">
            ⚠️ <b>Attention</b> : La suppression des données est irréversible
        </div>
        """, unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        with d1:
            if st.button("🗑️ Vider les factures locales",
                         use_container_width=True):
                st.session_state["factures"] = []
                st.success("✅ Factures locales supprimées")
                st.rerun()
        with d2:
            if st.button("🗑️ Vider les notes de frais locales",
                         use_container_width=True):
                st.session_state["notes_frais"] = []
                st.success("✅ Notes de frais locales supprimées")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    main_wrap_end()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : INCONNUE (fallback)
# ══════════════════════════════════════════════════════════════════════════════
else:
    main_wrap()
    st.markdown("""
    <div style="text-align:center;padding:6rem 2rem;">
        <div style="font-size:5rem;">🐱</div>
        <h2 style="color:#1a1a2e;margin-top:1rem;">Page introuvable</h2>
        <p style="color:#9ca3af;">Cette page n'existe pas encore… Miaou~</p>
    </div>
    """, unsafe_allow_html=True)
    main_wrap_end()
