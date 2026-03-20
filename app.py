import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FactureCat",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #FAFAF8;
}

[data-testid="stSidebar"] {
    background: #1a1a2e;
    border-right: 1px solid #2d2d44;
}

[data-testid="stSidebar"] * {
    color: #e8e8e8 !important;
}

.main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 0.5rem;
}

.subtitle {
    font-size: 1rem;
    color: #888;
    margin-bottom: 2rem;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f0;
    margin-bottom: 1rem;
}

.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-left: 4px solid #FF6B35;
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a2e;
}

.metric-label {
    font-size: 0.85rem;
    color: #888;
    margin-top: 0.25rem;
}

.stButton > button {
    background: linear-gradient(135deg, #FF6B35, #FF8C5A);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    transition: all 0.3s;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(255,107,53,0.4);
}

.success-box {
    background: #e8f5e9;
    border: 1px solid #a5d6a7;
    border-radius: 10px;
    padding: 1rem;
    color: #2e7d32;
}

.error-box {
    background: #ffebee;
    border: 1px solid #ef9a9a;
    border-radius: 10px;
    padding: 1rem;
    color: #c62828;
}

.cat-bubble {
    background: linear-gradient(135deg, #1a1a2e, #2d2d44);
    color: white;
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0;
    max-width: 80%;
}

.user-bubble {
    background: linear-gradient(135deg, #FF6B35, #FF8C5A);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 80%;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONNEXION SUPABASE
# ============================================================

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ============================================================
# CONNEXION GEMINI
# ============================================================

def init_gemini():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

# ============================================================
# SESSION STATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================
# IMPORT DES PAGES
# ============================================================

from pages_auth import show_auth
from pages_dashboard import show_dashboard
from pages_factures import show_factures
from pages_notes import show_notes
from pages_compta import show_compta
from pages_chat import show_chat
from pages_settings import show_settings

# ============================================================
# ROUTING
# ============================================================

def show_sidebar():
    with st.sidebar:
        st.markdown("## 🐱 FactureCat")
        st.markdown("---")
        
        pages = {
            "dashboard": "📊 Dashboard",
            "factures": "🧾 Factures",
            "notes": "📝 Notes de frais",
            "compta": "📈 Comptabilité",
            "chat": "💬 Assistant",
            "settings": "⚙️ Paramètres"
        }
        
        for key, label in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()
        
        st.markdown("---")
        
        user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
        st.markdown(f"👤 `{user_email}`")
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

def main():
    if not st.session_state.authenticated:
        show_auth(supabase)
    else:
        show_sidebar()
        
        page = st.session_state.page
        
        if page == "dashboard":
            show_dashboard(supabase)
        elif page == "factures":
            show_factures(supabase)
        elif page == "notes":
            show_notes(supabase)
        elif page == "compta":
            show_compta(supabase)
        elif page == "chat":
            show_chat(supabase)
        elif page == "settings":
            show_settings(supabase)

if __name__ == "__main__":
    main()
