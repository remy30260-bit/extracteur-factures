import streamlit as st
from supabase import create_client, Client
import os

# ── CONFIG PAGE ───────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceAI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS GLOBAL ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fond général */
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1d2e; border-right: 1px solid #2d2d3d; }
    
    /* Cards */
    .card {
        background: #1e2130;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        border: 1px solid #2d2d3d;
    }
    
    /* Titres */
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
    
    /* Boutons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4a90d9, #7b68ee);
        border: none;
        color: white;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #4a90d9 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d2e;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #aaa;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a90d9 !important;
        color: white !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #1e2130 !important;
        border: 1px solid #2d2d3d !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
    }
    
    /* Dataframe */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    
    /* Divider */
    hr { border-color: #2d2d3d; }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── SUPABASE ──────────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ── AUTH ──────────────────────────────────────────────────────
def show_auth():
    st.markdown("""
    <div style='text-align:center; padding: 3rem 0 1rem 0;'>
        <div style='font-size:3rem;'>💼</div>
        <h1 style='color:#fff; font-size:2.5rem; font-weight:800;'>FinanceAI</h1>
        <p style='color:#888; font-size:1.1rem;'>Gestion financière intelligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="vous@exemple.com")
                password = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button("🔐 Se connecter", use_container_width=True, type="primary")
                
                if submitted:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user.__dict__
                        st.session_state.authenticated = True
                        
                        # Charger clé API depuis profil
                        try:
                            profil = supabase.table("profils").select("gemini_api_key").eq(
                                "user_id", res.user.id
                            ).execute().data
                            if profil and profil[0].get("gemini_api_key"):
                                st.session_state.gemini_api_key = profil[0]["gemini_api_key"]
                        except:
                            pass
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur de connexion : {e}")
        
        with tab_signup:
            with st.form("signup_form"):
                email_s = st.text_input("Email", placeholder="vous@exemple.com", key="signup_email")
                password_s = st.text_input("Mot de passe", type="password", key="signup_pwd")
                password_s2 = st.text_input("Confirmer mot de passe", type="password", key="signup_pwd2")
                submitted_s = st.form_submit_button("📝 S'inscrire", use_container_width=True, type="primary")
                
                if submitted_s:
                    if password_s != password_s2:
                        st.error("❌ Les mots de passe ne correspondent pas.")
                    elif len(password_s) < 6:
                        st.error("❌ Mot de passe trop court (minimum 6 caractères).")
                    else:
                        try:
                            res = supabase.auth.sign_up({"email": email_s, "password": password_s})
                            st.success("✅ Compte créé ! Vérifiez votre email pour confirmer.")
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")

# ── SIDEBAR NAVIGATION ────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0;'>
            <div style='font-size:2rem;'>💼</div>
            <h2 style='color:#fff; margin:0.3rem 0; font-size:1.4rem;'>FinanceAI</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Infos utilisateur
        email = st.session_state.user.get("email", "")
        st.markdown(f"""
        <div style='background:#1e2130; border-radius:8px; padding:0.8rem; margin-bottom:1rem; text-align:center;'>
            <div style='font-size:1.5rem;'>👤</div>
            <div style='color:#aaa; font-size:0.8rem; word-break:break-all;'>{email}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut Gemini
        if st.session_state.get("gemini_api_key"):
            st.markdown("<div style='color:#2ecc71; font-size:0.8rem; text-align:center; margin-bottom:1rem;'>🤖 Gemini AI actif ✅</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#f39c12; font-size:0.8rem; text-align:center; margin-bottom:1rem;'>🤖 Gemini non configuré ⚠️</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Menu
        pages = {
            "🏠 Dashboard": "dashboard",
            "🧾 Factures": "factures",
            "📝 Notes de frais": "notes",
            "📊 Comptabilité": "comptabilite",
            "⚙️ Paramètres": "parametres"
        }
        
        if "page" not in st.session_state:
            st.session_state.page = "dashboard"
        
        for label, key in pages.items():
            is_active = st.session_state.page == key
            btn_style = "primary" if is_active else "secondary"
            if st.button(label, use_container_width=True, type=btn_style, key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()

# ── MAIN ──────────────────────────────────────────────────────
def main():
    if not st.session_state.get("authenticated"):
        show_auth()
        return
    
    show_sidebar()
    
    page = st.session_state.get("page", "dashboard")
    
    if page == "dashboard":
        from pages_dashboard import show_dashboard
        show_dashboard(supabase)
    
    elif page == "factures":
        from pages_factures import show_factures
        show_factures(supabase)
    
    elif page == "notes":
        from pages_notes import show_notes
        show_notes(supabase)
    
    elif page == "comptabilite":
        from pages_comptabilite import show_comptabilite
        show_comptabilite(supabase)
    
    elif page == "parametres":
        from pages_parametres import show_parametres
        show_parametres(supabase)

if __name__ == "__main__":
    main()
