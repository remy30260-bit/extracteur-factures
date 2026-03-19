import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE & GEMINI
# ═══════════════════════════════════════════════════════════════════════════════
def get_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def configure_gemini():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel("gemini-2.5-flash")
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL + TOPBAR
# ═══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif !important; }

    /* Cache sidebar */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Background */
    .main, .block-container {
        background: linear-gradient(135deg, #fff8f0 0%, #fdf0e8 100%) !important;
        padding-top: 0 !important;
        max-width: 100% !important;
    }
    .block-container { padding: 0 2rem 2rem !important; }

    /* ── TOP NAV ── */
    .topnav {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 9999;
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(240,160,112,0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2rem;
        height: 64px;
        box-shadow: 0 4px 24px rgba(240,160,112,0.12);
    }
    .topnav-logo {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        text-decoration: none;
    }
    .topnav-logo-icon {
        font-size: 1.8rem;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }
    .topnav-logo-text {
        font-size: 1.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f0a070, #e8856a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .topnav-links {
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    .topnav-link {
        padding: 0.5rem 1.1rem;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #a0522d;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
        background: transparent;
        text-decoration: none;
        white-space: nowrap;
    }
    .topnav-link:hover {
        background: rgba(240,160,112,0.15);
        color: #e8856a;
    }
    .topnav-link.active {
        background: linear-gradient(135deg, #f0a070, #e8856a);
        color: white !important;
        box-shadow: 0 4px 12px rgba(240,160,112,0.4);
    }
    .topnav-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .topnav-user {
        background: rgba(240,160,112,0.1);
        border: 1px solid rgba(240,160,112,0.3);
        border-radius: 20px;
        padding: 0.35rem 1rem;
        font-size: 0.82rem;
        color: #a0522d;
        font-weight: 500;
    }

    /* Espace sous la topnav */
    .page-content { margin-top: 80px; }

    /* ── HERO BANNER ── */
    .hero {
        background: linear-gradient(135deg, #f0a070 0%, #e8856a 50%, #d4694f 100%);
        border-radius: 28px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 12px 40px rgba(240,160,112,0.35);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 400px; height: 400px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
    }
    .hero::after {
        content: '';
        position: absolute;
        bottom: -60%; right: 10%;
        width: 300px; height: 300px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }
    .hero h1 { margin: 0; font-size: 2.2rem; font-weight: 800; }
    .hero p  { margin: 0.5rem 0 0; opacity: 0.9; font-size: 1rem; }

    /* ── METRIC CARDS ── */
    .metric-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(240,160,112,0.15);
        box-shadow: 0 4px 20px rgba(240,160,112,0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #f0a070, #e8856a);
        border-radius: 20px 20px 0 0;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(240,160,112,0.18);
    }

    /* ── DATA CARDS ── */
    .data-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(240,160,112,0.15);
        box-shadow: 0 4px 16px rgba(240,160,112,0.08);
        transition: all 0.25s ease;
    }
    .data-card:hover {
        transform: translateX(4px);
        border-left: 4px solid #f0a070;
        box-shadow: 0 8px 28px rgba(240,160,112,0.15);
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg, #f0a070, #e8856a) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(240,160,112,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(240,160,112,0.45) !important;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        border-radius: 14px !important;
        border: 2px solid rgba(240,160,112,0.25) !important;
        background: #fffaf7 !important;
        transition: border 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #f0a070 !important;
        box-shadow: 0 0 0 3px rgba(240,160,112,0.15) !important;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 14px !important;
        border: 2px solid rgba(240,160,112,0.2) !important;
        font-weight: 600 !important;
        color: #a0522d !important;
    }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(240,160,112,0.4) !important;
        border-radius: 20px !important;
        background: #fffaf7 !important;
        padding: 1rem !important;
    }

    /* ── FLOATING CHAT ── */
    .chat-widget {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 9998;
    }
    .chat-bubble {
        width: 60px; height: 60px;
        background: linear-gradient(135deg, #f0a070, #e8856a);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem;
        cursor: pointer;
        box-shadow: 0 8px 25px rgba(240,160,112,0.5);
        transition: all 0.3s;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%,100% { box-shadow: 0 8px 25px rgba(240,160,112,0.5); }
        50% { box-shadow: 0 8px 40px rgba(240,160,112,0.8); }
    }
    .chat-bubble:hover { transform: scale(1.1); }

    /* ── BADGE STATUT ── */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-green { background: #f0fff4; color: #276749; border: 1px solid #9ae6b4; }
    .badge-orange { background: #fff8f0; color: #c05621; border: 1px solid #f0a070; }
    .badge-red { background: #fff5f5; color: #c53030; border: 1px solid #fc8181; }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #fff8f0; }
    ::-webkit-scrollbar-thumb { background: #f0a070; border-radius: 3px; }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(240,160,112,0.2) !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 14px;
        padding: 0.3rem;
        border: 1px solid rgba(240,160,112,0.2);
        gap: 0.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 500 !important;
        color: #a0522d !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #f0a070, #e8856a) !important;
        color: white !important;
    }

    /* ── PROGRESS ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #f0a070, #e8856a) !important;
        border-radius: 10px !important;
    }

    /* ── ALERTS ── */
    .stSuccess { border-radius: 14px !important; border-left: 4px solid #68d391 !important; }
    .stError   { border-radius: 14px !important; border-left: 4px solid #fc8181 !important; }
    .stWarning { border-radius: 14px !important; border-left: 4px solid #f0a070 !important; }

    </style>
    """, unsafe_allow_html=True)


def render_topnav(current_page):
    """Barre de navigation fixe en haut"""
    pages = ["🏠 Dashboard", "📄 Factures", "🧾 Notes de frais", "🤖 Assistant IA"]
    user_email = st.session_state.get("user_email", "")

    # On génère les boutons via Streamlit (invisible) pour garder la logique de navigation
    st.markdown(f"""
    <div class="topnav">
        <div class="topnav-logo">
            <span class="topnav-logo-icon">🐱</span>
            <span class="topnav-logo-text">FactureCat</span>
        </div>
        <div class="topnav-links" id="topnav-links">
        </div>
        <div class="topnav-right">
            <div class="topnav-user">👤 {user_email}</div>
        </div>
    </div>
    <div class="page-content"></div>
    """, unsafe_allow_html=True)

    # Navigation via colonnes cachées (astuce Streamlit)
    cols = st.columns([2, 1, 1, 1, 1, 1, 2])
    nav_map = {
        1: "🏠 Dashboard",
        2: "📄 Factures",
        3: "🧾 Notes de frais",
        4: "🤖 Assistant IA",
        5: "logout"
    }
    with cols[1]:
        if st.button("🏠 Dashboard", key="nav_dash",
                     type="primary" if current_page == "🏠 Dashboard" else "secondary",
                     use_container_width=True):
            st.session_state["page"] = "🏠 Dashboard"
            st.rerun()
    with cols[2]:
        if st.button("📄 Factures", key="nav_fact",
                     type="primary" if current_page == "📄 Factures" else "secondary",
                     use_container_width=True):
            st.session_state["page"] = "📄 Factures"
            st.rerun()
    with cols[3]:
        if st.button("🧾 Notes", key="nav_notes",
                     type="primary" if current_page == "🧾 Notes de frais" else "secondary",
                     use_container_width=True):
            st.session_state["page"] = "🧾 Notes de frais"
            st.rerun()
    with cols[4]:
        if st.button("🤖 IA", key="nav_ia",
                     type="primary" if current_page == "🤖 Assistant IA" else "secondary",
                     use_container_width=True):
            st.session_state["page"] = "🤖 Assistant IA"
            st.rerun()
    with cols[5]:
        if st.button("🚪", key="nav_logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = ""
            try:
                get_supabase().auth.sign_out()
            except:
                pass
            st.rerun()

    # Style pour les boutons de nav (secondaire = transparent)
    st.markdown("""
    <style>
    /* Boutons secondaires nav = style pill transparent */
    [data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #a0522d !important;
        box-shadow: none !important;
        border: none !important;
        font-weight: 500 !important;
    }
    [data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"]:hover {
        background: rgba(240,160,112,0.12) !important;
        transform: none !important;
    }
    /* Bouton actif nav */
    [data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #f0a070, #e8856a) !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(240,160,112,0.4) !important;
    }
    /* Bouton logout */
    [data-testid="stHorizontalBlock"]:last-child .stButton > button {
        background: rgba(240,100,80,0.1) !important;
        color: #c05621 !important;
        box-shadow: none !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [Image.open(io.BytesIO(p.get_pixmap(dpi=150).tobytes("png"))) for p in doc]

def extraire_facture(model, images):
    prompt = """
Analyse cette facture et extrais les informations en JSON strict :
{
  "fournisseur": "nom",
  "numero": "numéro",
  "date": "YYYY-MM-DD",
  "montant_ht": 0.0,
  "tva": 0.0,
  "montant_ttc": 0.0,
  "categorie": "Informatique|Transport|Repas|Fournitures|Services|Autres",
  "statut": "À payer"
}
Réponds UNIQUEMENT avec le JSON, sans markdown.
"""
    try:
        r = model.generate_content([prompt] + images)
        text = r.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except:
        return {"fournisseur":"Non détecté","numero":"—","date":str(datetime.now().date()),
                "montant_ht":0,"tva":0,"montant_ttc":0,"categorie":"Autres","statut":"À payer"}

def hero(icon, title, subtitle):
    st.markdown(f"""
    <div class="hero">
        <h1>{icon} {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, delta="", icon=""):
    st.markdown(f"""
    <div class="metric-card">
        <p style="color:#c8956c;font-size:0.8rem;font-weight:700;
           text-transform:uppercase;letter-spacing:0.05em;margin:0 0 0.4rem;">
           {icon} {label}
        </p>
        <p style="color:#a0522d;font-size:2rem;font-weight:800;margin:0;line-height:1;">
           {value}
        </p>
        <p style="color:#d4a882;font-size:0.8rem;margin:0.5rem 0 0;">{delta}</p>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FLOATING CHAT
# ═══════════════════════════════════════════════════════════════════════════════
def show_floating_chat():
    if "float_chat_open" not in st.session_state:
        st.session_state["float_chat_open"] = False
    if "float_messages" not in st.session_state:
        st.session_state["float_messages"] = []

    col_spacer, col_chat = st.columns([5, 1])
    with col_chat:
        if st.button("🐱👓", key="float_toggle", help="Assistant FactureCat"):
            st.session_state["float_chat_open"] = not st.session_state["float_chat_open"]

    if st.session_state["float_chat_open"]:
        with st.container():
            st.markdown("""
            <div style="position:fixed;bottom:5rem;right:2rem;width:360px;
                 background:white;border-radius:24px;
                 box-shadow:0 20px 60px rgba(240,160,112,0.35);
                 border:1px solid rgba(240,160,112,0.2);
                 z-index:9997;overflow:hidden;">
                <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
                     padding:1rem 1.2rem;display:flex;align-items:center;gap:0.7rem;">
                    <span style="font-size:1.5rem;">🐱👓</span>
                    <div>
                        <div style="color:white;font-weight:700;font-size:0.95rem;">
                            Assistant FactureCat
                        </div>
                        <div style="color:rgba(255,255,255,0.8);font-size:0.75rem;">
                            ● En ligne
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:300px;overflow-y:auto;padding:1rem;'>",
                        unsafe_allow_html=True)
            for msg in st.session_state["float_messages"][-6:]:
                align = "flex-end" if msg["role"] == "user" else "flex-start"
                bg = "#f0a070" if msg["role"] == "user" else "#fff8f0"
                color = "white" if msg["role"] == "user" else "#a0522d"
                icon = "👤" if msg["role"] == "user" else "🐱"
                st.markdown(f"""
                <div style="display:flex;justify-content:{align};margin:0.4rem 0;">
                    <div style="background:{bg};color:{color};padding:0.6rem 1rem;
                         border-radius:16px;max-width:85%;font-size:0.85rem;
                         box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                        <span style="opacity:0.6;font-size:0.7rem;">{icon}</span>
                        <br>{msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            user_q = st.chat_input("Posez votre question 🐾", key="float_input")
            if user_q:
                st.session_state["float_messages"].append(
                    {"role": "user", "content": user_q}
                )
                model = configure_gemini()
                if model:
                    try:
                        supabase = get_supabase()
                        uid = st.session_state.get("user_id","")
                        factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
                        notes = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
                    except:
                        factures = st.session_state.get("resultats",[])
                        notes = st.session_state.get("notes_frais",[])

                    context = f"""Tu es l'assistant FactureCat 🐱, expert-comptable virtuel sympa.
Factures : {json.dumps(factures, ensure_ascii=False)}
Notes de frais : {json.dumps(notes, ensure_ascii=False)}
Réponds en français, clair et concis. Question : {user_q}"""
                    try:
                        resp = model.generate_content(context)
                        answer = resp.text
                    except Exception as e:
                        answer = f"❌ {e}"
                else:
                    answer = "❌ Clé API manquante"

                st.session_state["float_messages"].append(
                    {"role": "assistant", "content": answer}
                )
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = ""
        st.session_state["user_id"] = ""
        try:
            supabase = get_supabase()
            session = supabase.auth.get_session()
            if session and session.user:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = session.user.email
                st.session_state["user_id"] = session.user.id
        except:
            pass

    if st.session_state["authenticated"]:
        return True

    # Page de login moderne
    st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #fff8f0, #fdf0e8) !important; }
    [data-testid="stSidebar"] { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem;">
            <div style="font-size:5rem;animation:float 3s ease-in-out infinite;">🐱</div>
            <h1 style="background:linear-gradient(135deg,#f0a070,#e8856a);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               font-size:2.5rem;font-weight:800;margin:0.5rem 0 0;">
               FactureCat
            </h1>
            <p style="color:#c8956c;margin:0.3rem 0 2rem;font-size:1rem;">
               Gestion comptable intelligente 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div style="background:white;border-radius:28px;padding:2.5rem;
                 box-shadow:0 20px 60px rgba(240,160,112,0.2);
                 border:1px solid rgba(240,160,112,0.15);">
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                st.markdown("<p style='color:#a0522d;font-weight:700;font-size:1.1rem;margin:0 0 1.5rem;'>Connexion</p>", unsafe_allow_html=True)
                email    = st.text_input("📧 Email", placeholder="votre@email.com")
                password = st.text_input("🔑 Mot de passe", type="password")
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button("🚀 Se connecter", use_container_width=True)

                if submit:
                    try:
                        supabase = get_supabase()
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
                        if res.user:
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"]    = res.user.email
                            st.session_state["user_id"]       = res.user.id
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

            st.markdown("</div>", unsafe_allow_html=True)

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    hero("🏠", "Dashboard", "Vue d'ensemble de votre comptabilité 🐾")

    try:
        supabase = get_supabase()
        uid      = st.session_state.get("user_id","")
        factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        notes    = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
    except:
        factures = st.session_state.get("resultats",[])
        notes    = st.session_state.get("notes_frais",[])

    total_f_ttc = sum(float(r.get("montant_ttc",0)) for r in factures)
    total_f_tva = sum(float(r.get("tva",0)) for r in factures)
    total_n_ttc = sum(float(n.get("montant_ttc",0)) for n in notes)
    total_n_ht  = sum(float(n.get("montant_ht",0)) for n in notes)

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Factures", str(len(factures)), f"TTC : {total_f_ttc:.2f} €", "📄")
    with c2: metric_card("CA Factures", f"{total_f_ttc:.2f} €", f"TVA : {total_f_tva:.2f} €", "💰")
    with c3: metric_card("Notes de frais", str(len(notes)), f"HT : {total_n_ht:.2f} €", "🧾")
    with c4: metric_card("Total dépenses", f"{total_f_ttc+total_n_ttc:.2f} €", "TTC all in", "💸")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:1.5rem;
             border:1px solid rgba(240,160,112,0.15);
             box-shadow:0 4px 20px rgba(240,160,112,0.08);">
            <p style="color:#a0522d;font-weight:700;font-size:1rem;margin:0 0 1rem;">
                📄 Dernières factures
            </p>
        """, unsafe_allow_html=True)

        if factures:
            for f in factures[-4:]:
                statut = f.get("statut","À payer")
                badge_cls = "badge-green" if "Payée" in statut else (
                    "badge-red" if "retard" in statut else "badge-orange")
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                     align-items:center;padding:0.7rem 0;
                     border-bottom:1px solid rgba(240,160,112,0.1);">
                    <div>
                        <div style="color:#a0522d;font-weight:600;font-size:0.9rem;">
                            {f.get('fournisseur','—')}
                        </div>
                        <div style="color:#c8956c;font-size:0.78rem;">{f.get('date','—')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#a0522d;font-weight:700;">
                            {float(f.get('montant_ttc',0)):.2f} €
                        </div>
                        <span class="badge {badge_cls}">{statut}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#c8956c;text-align:center;'>Aucune facture 🐱</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:1.5rem;
             border:1px solid rgba(240,160,112,0.15);
             box-shadow:0 4px 20px rgba(240,160,112,0.08);">
            <p style="color:#a0522d;font-weight:700;font-size:1rem;margin:0 0 1rem;">
                🧾 Dernières notes de frais
            </p>
        """, unsafe_allow_html=True)

        if notes:
            for n in notes[-4:]:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                     align-items:center;padding:0.7rem 0;
                     border-bottom:1px solid rgba(240,160,112,0.1);">
                    <div>
                        <div style="color:#a0522d;font-weight:600;font-size:0.9rem;">
                            {n.get('description','—')[:30]}
                        </div>
                        <div style="color:#c8956c;font-size:0.78rem;">
                            {n.get('categorie','—')} · {n.get('date','—')}
                        </div>
                    </div>
                    <div style="color:#a0522d;font-weight:700;">
                        {float(n.get('montant_ttc',0)):.2f} €
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#c8956c;text-align:center;'>Aucune note 🐱</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Répartition par catégorie
    if factures:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:1.5rem;
             border:1px solid rgba(240,160,112,0.15);
             box-shadow:0 4px 20px rgba(240,160,112,0.08);">
            <p style="color:#a0522d;font-weight:700;font-size:1rem;margin:0 0 1rem;">
                📊 Répartition par catégorie
            </p>
        """, unsafe_allow_html=True)
        df_cat = pd.DataFrame(factures).groupby("categorie")["montant_ttc"].sum().reset_index()
        st.bar_chart(df_cat.set_index("categorie"), color="#f0a070", height=250)
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FACTURES
# ═══════════════════════════════════════════════════════════════════════════════
def show_factures():
    hero("📄", "Gestion des Factures", "Importez et analysez vos factures avec l'IA 🤖")

    if "resultats" not in st.session_state:
        st.session_state["resultats"] = []

    tab1, tab2, tab3 = st.tabs(["📤 Import & Analyse", "📋 Liste", "📊 Export"])

    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Glissez vos factures (PDF ou image)",
            type=["pdf","png","jpg","jpeg"],
            accept_multiple_files=True,
            key="facture_uploader"
        )

        if uploaded_files:
            col_info, col_btn = st.columns([2, 1])
            with col_info:
                st.markdown(f"""
                <div style="background:#fff8f0;border-radius:14px;padding:0.8rem 1.2rem;
                     border:2px solid rgba(240,160,112,0.3);">
                    <span style="color:#a0522d;font-weight:600;">
                        📁 {len(uploaded_files)} fichier(s) prêt(s) à analyser
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                analyser = st.button("🔍 Analyser avec l'IA",
                                     use_container_width=True, key="btn_analyser")

            if analyser:
                model = configure_gemini()
                if not model:
                    st.error("❌ Clé API Gemini manquante")
                else:
                    progress = st.progress(0)
                    status   = st.empty()
                    for i, f in enumerate(uploaded_files):
                        status.markdown(f"""
                        <div style="background:#fff8f0;border-radius:12px;padding:0.8rem;
                             border-left:4px solid #f0a070;">
                            🔍 Analyse de <b>{f.name}</b>…
                        </div>
                        """, unsafe_allow_html=True)
                        content = f.read()
                        images  = pdf_to_images(content) if f.name.lower().endswith(".pdf") \
                                  else [Image.open(io.BytesIO(content))]
                        result = extraire_facture(model, images)
                        result["fichier"] = f.name

                        try:
                            supabase = get_supabase()
                            uid = st.session_state.get("user_id","")
                            supabase.table("factures").insert({**result,"user_id":uid}).execute()
                        except:
                            st.session_state["resultats"].append(result)

                        progress.progress((i+1)/len(uploaded_files))

                    status.success(f"✅ {len(uploaded_files)} facture(s) analysée(s) !")
                    st.rerun()

    with tab2:
        try:
            supabase = get_supabase()
            uid = st.session_state.get("user_id","")
            factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        except:
            factures = st.session_state.get("resultats",[])

        if factures:
            # Filtres
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                search = st.text_input("🔍 Rechercher", placeholder="Fournisseur…", key="fact_search")
            with col_f2:
                cats = ["Toutes"] + list(set(f.get("categorie","") for f in factures))
                cat_filter = st.selectbox("📂 Catégorie", cats, key="fact_cat")
            with col_f3:
                statuts = ["Tous"] + list(set(f.get("statut","") for f in factures))
                stat_filter = st.selectbox("🏷️ Statut", statuts, key="fact_stat")

            filtered = [f for f in factures
                        if (not search or search.lower() in str(f.get("fournisseur","")).lower())
                        and (cat_filter == "Toutes" or f.get("categorie") == cat_filter)
                        and (stat_filter == "Tous" or f.get("statut") == stat_filter)]

            st.markdown(f"<p style='color:#c8956c;font-size:0.85rem;'>{len(filtered)} résultat(s)</p>",
                        unsafe_allow_html=True)

            for idx, r in enumerate(filtered):
                statut = r.get("statut","À payer")
                badge_cls = "badge-green" if "Payée" in statut else (
                    "badge-red" if "retard" in statut else "badge-orange")
                with st.expander(
                    f"🏢 {r.get('fournisseur','—')} · {r.get('date','—')} · "
                    f"{float(r.get('montant_ttc',0)):.2f} €", expanded=False
                ):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">N° Facture</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">{r.get('numero','—')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">Montant HT</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">
                                {float(r.get('montant_ht',0)):.2f} €
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">Montant TTC</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">
                                {float(r.get('montant_ttc',0)):.2f} €
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                    col_s, col_d = st.columns(2)
                    with col_s:
                        new_statut = st.selectbox(
                            "Statut", ["À payer","Payée ✅","En retard ⚠️"],
                            index=["À payer","Payée ✅","En retard ⚠️"].index(statut)
                            if statut in ["À payer","Payée ✅","En retard ⚠️"] else 0,
                            key=f"statut_{idx}"
                        )
                    with col_d:
                        if st.button("🗑️ Supprimer", key=f"del_fact_{idx}"):
                            try:
                                supabase = get_supabase()
                                supabase.table("factures").delete().eq("id",r.get("id")).execute()
                            except:
                                st.session_state["resultats"].pop(idx)
                            st.rerun()

                    if new_statut != statut:
                        try:
                            supabase = get_supabase()
                            supabase.table("factures").update({"statut":new_statut})\
                                    .eq("id",r.get("id")).execute()
                            st.rerun()
                        except:
                            pass
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:24px;border:2px dashed #f0d5c0;">
                <div style="font-size:4rem;">🐱</div>
                <h3 style="color:#a0522d;">Aucune facture</h3>
                <p style="color:#c8956c;">Importez vos premières factures 🐾</p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        try:
            supabase = get_supabase()
            uid = st.session_state.get("user_id","")
            factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        except:
            factures = st.session_state.get("resultats",[])

        if factures:
            df = pd.DataFrame(factures)
            st.dataframe(df, use_container_width=True, height=400)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 CSV", df.to_csv(index=False).encode(),
                    f"factures_{datetime.now().strftime('%Y_%m')}.csv", "text/csv",
                    use_container_width=True, key="dl_csv_fact")
            with c2:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    df.to_excel(w, index=False, sheet_name="Factures")
                st.download_button("📊 Excel", buf.getvalue(),
                    f"factures_{datetime.now().strftime('%Y_%m')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_xl_fact")


# ═══════════════════════════════════════════════════════════════════════════════
# NOTES DE FRAIS
# ═══════════════════════════════════════════════════════════════════════════════
def show_notes():
    hero("🧾", "Notes de Frais", "Gérez vos dépenses professionnelles 💼")

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    tab1, tab2 = st.tabs(["➕ Nouvelle note", "📋 Historique"])

    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        with st.container():
            st.markdown("""
            <div style="background:white;border-radius:20px;padding:2rem;
                 border:1px solid rgba(240,160,112,0.15);
                 box-shadow:0 4px 20px rgba(240,160,112,0.08);">
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                date_note   = st.date_input("📅 Date", datetime.now(), key="note_date")
                categorie   = st.selectbox("📂 Catégorie",
                    ["Transport","Repas","Hébergement","Fournitures","Informatique","Autres"],
                    key="note_cat")
                montant_ht  = st.number_input("💵 Montant HT (€)", 0.0, step=0.01, key="note_ht")
            with col2:
                description = st.text_area("📝 Description", key="note_desc", height=100)
                taux_tva    = st.selectbox("📊 Taux TVA", [20.0, 10.0, 5.5, 0.0], key="note_tva")
                justificatif = st.file_uploader("📎 Justificatif", key="note_file",
                    type=["pdf","png","jpg","jpeg"])

            tva = round(montant_ht * taux_tva / 100, 2)
            montant_ttc = round(montant_ht + tva, 2)

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fff8f0,#fdf0e8);
                 border-radius:14px;padding:1rem;margin:1rem 0;
                 border:2px solid rgba(240,160,112,0.2);
                 display:flex;gap:2rem;">
                <div><span style="color:#c8956c;font-size:0.8rem;">HT</span>
                     <br><b style="color:#a0522d;">{montant_ht:.2f} €</b></div>
                <div><span style="color:#c8956c;font-size:0.8rem;">TVA {taux_tva}%</span>
                     <br><b style="color:#a0522d;">{tva:.2f} €</b></div>
                <div><span style="color:#c8956c;font-size:0.8rem;">TTC</span>
                     <br><b style="color:#a0522d;font-size:1.2rem;">{montant_ttc:.2f} €</b></div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✅ Ajouter la note", use_container_width=True, key="btn_add_note"):
                if description and montant_ht > 0:
                    note = {
                        "date": str(date_note), "description": description,
                        "categorie": categorie, "montant_ht": montant_ht,
                        "tva": tva, "montant_ttc": montant_ttc, "taux_tva": taux_tva,
                        "justificatif": justificatif.name if justificatif else "—"
                    }
                    try:
                        supabase = get_supabase()
                        uid = st.session_state.get("user_id","")
                        supabase.table("notes_frais").insert({**note,"user_id":uid}).execute()
                        st.success("✅ Note sauvegardée !")
                    except Exception as e:
                        st.session_state["notes_frais"].append(note)
                        st.warning(f"⚠️ Local seulement : {e}")
                    st.rerun()
                else:
                    st.error("❌ Description et montant requis")

            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        try:
            supabase = get_supabase()
            uid = st.session_state.get("user_id","")
            notes = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
        except:
            notes = st.session_state.get("notes_frais",[])

        if notes:
            for idx, n in enumerate(notes):
                with st.expander(
                    f"📝 {n.get('description','—')[:40]} · {n.get('date','—')} · "
                    f"{float(n.get('montant_ttc',0)):.2f} €"
                ):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">Catégorie</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">{n.get('categorie','—')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">HT</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">
                                {float(n.get('montant_ht',0)):.2f} €
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""
                        <div class="metric-card" style="padding:1rem;">
                            <p style="color:#c8956c;font-size:0.75rem;margin:0;">TTC</p>
                            <p style="color:#a0522d;font-weight:700;margin:0;">
                                {float(n.get('montant_ttc',0)):.2f} €
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                    if st.button("🗑️ Supprimer", key=f"del_note_{idx}", use_container_width=True):
                        try:
                            supabase = get_supabase()
                            supabase.table("notes_frais").delete().eq("id",n.get("id")).execute()
                        except:
                            st.session_state["notes_frais"].pop(idx)
                        st.rerun()

            # Export
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            df_n = pd.DataFrame(notes)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 CSV", df_n.to_csv(index=False).encode(),
                    f"notes_{datetime.now().strftime('%Y_%m')}.csv", "text/csv",
                    use_container_width=True, key="dl_csv_notes")
            with c2:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    df_n.to_excel(w, index=False, sheet_name="Notes")
                st.download_button("📊 Excel", buf.getvalue(),
                    f"notes_{datetime.now().strftime('%Y_%m')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_xl_notes")
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;
                 border-radius:24px;border:2px dashed #f0d5c0;">
                <div style="font-size:4rem;">🐱</div>
                <h3 style="color:#a0522d;">Aucune note de frais</h3>
                <p style="color:#c8956c;">Ajoutez votre première note 🐾</p>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CHATBOT PLEINE PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_chatbot():
    hero("🐱👓", "Assistant IA", "Posez toutes vos questions comptables 💬")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    try:
        supabase = get_supabase()
        uid = st.session_state.get("user_id","")
        factures_data = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        notes_data    = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
    except:
        factures_data = st.session_state.get("resultats",[])
        notes_data    = st.session_state.get("notes_frais",[])

    # Historique
    chat_container = st.container()
    with chat_container:
        if not st.session_state["chat_messages"]:
            st.markdown("""
            <div style="text-align:center;padding:3rem;background:white;
                 border-radius:24px;border:2px dashed rgba(240,160,112,0.3);">
                <div style="font-size:4rem;">🐱👓</div>
                <h3 style="color:#a0522d;">Bonjour ! Je suis votre assistant comptable</h3>
                <p style="color:#c8956c;">
                    Posez-moi des questions sur vos factures, notes de frais, TVA…
                </p>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state["chat_messages"]:
            align = "flex-end" if msg["role"] == "user" else "flex-start"
            bg    = "linear-gradient(135deg,#f0a070,#e8856a)" if msg["role"] == "user" else "white"
            color = "white" if msg["role"] == "user" else "#a0522d"
            icon  = "👤" if msg["role"] == "user" else "🐱👓"
            st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin:0.6rem 0;">
                <div style="background:{bg};color:{color};padding:1rem 1.2rem;
                     border-radius:20px;max-width:75%;
                     box-shadow:0 4px 16px rgba(240,160,112,0.15);
                     border:1px solid rgba(240,160,112,0.1);font-size:0.9rem;">
                    <span style="opacity:0.6;font-size:0.75rem;">{icon}</span><br>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    user_input = st.chat_input("Posez votre question à FactureCat 🐾")
    if user_input:
        st.session_state["chat_messages"].append({"role":"user","content":user_input})
        model = configure_gemini()
        if model:
            context = f"""Tu es FactureCat 🐱👓, assistant comptable expert et sympa.
Factures : {json.dumps(factures_data, ensure_ascii=False)}
Notes : {json.dumps(notes_data, ensure_ascii=False)}
Réponds en français, clair et professionnel. Question : {user_input}"""
            try:
                resp   = model.generate_content(context)
                answer = resp.text
            except Exception as e:
                answer = f"❌ {e}"
        else:
            answer = "❌ Clé API Gemini manquante"
        st.session_state["chat_messages"].append({"role":"assistant","content":answer})
        st.rerun()
