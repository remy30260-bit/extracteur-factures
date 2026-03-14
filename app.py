import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide")

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def check_password():
    def password_entered():
        if (st.session_state["username"] == st.secrets["auth"]["username"] and
            st.session_state["password"] == st.secrets["auth"]["password"]):
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.markdown("""
        <div style="max-width:400px; margin:5rem auto; text-align:center;">
            <div style="font-size:4rem;">🐱</div>
            <h2 style="color:#a0522d;">FactureCat</h2>
            <p style="color:#c8956c;">Connexion requise 🔐</p>
        </div>
        """, unsafe_allow_html=True)
        col = st.columns([1, 2, 1])
        with col[1]:
            st.text_input("👤 Utilisateur", key="username")
            st.text_input("🔑 Mot de passe", type="password", key="password")
            st.button("🐾 Se connecter", on_click=password_entered, use_container_width=True)
        return False

    elif not st.session_state["authenticated"]:
        st.markdown("""
        <div style="max-width:400px; margin:5rem auto; text-align:center;">
            <div style="font-size:4rem;">🙀</div>
            <h2 style="color:#a0522d;">FactureCat</h2>
            <p style="color:#c8956c;">Connexion requise 🔐</p>
        </div>
        """, unsafe_allow_html=True)
        col = st.columns([1, 2, 1])
        with col[1]:
            st.text_input("👤 Utilisateur", key="username")
            st.text_input("🔑 Mot de passe", type="password", key="password")
            st.button("🐾 Se connecter", on_click=password_entered, use_container_width=True)
            st.error("❌ Identifiants incorrects, miaou !")
        return False

    return True

if not check_password():
    st.stop()

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
    
    * { font-family: 'Nunito', sans-serif; }
    .stApp { background-color: #fdf6f0; }
    
    [data-testid="stSidebar"] {
        background-color: #fff8f3;
        border-right: 2px solid #f0d5c0;
    }
    
    h1 { color: #a0522d; font-weight: 800; }
    h2, h3 { color: #c8956c; }
    
    .stButton > button {
        background: linear-gradient(135deg, #f0a070, #e8856a);
        color: white; border: none; border-radius: 20px;
        padding: 0.6rem 2rem; font-size: 1rem; font-weight: 700;
        box-shadow: 0 4px 15px rgba(200,149,108,0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(200,149,108,0.6);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #a8d8a8, #7fc87f);
        color: #2d5a2d; border: none; border-radius: 20px;
        padding: 0.6rem 2rem; font-weight: 700;
        box-shadow: 0 4px 15px rgba(127,200,127,0.4);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover { transform: translateY(-2px); }
    
    .card {
        background: white; border-radius: 20px; padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(200,149,108,0.15);
        margin-bottom: 1rem; border: 2px solid #f5e6d8;
    }
    
    [data-testid="stFileUploader"] {
        background: white; border-radius: 20px;
        padding: 1rem; border: 2px dashed #f0a070;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #f0a070, #e8856a, #c8956c);
        border-radius: 10px;
    }
    
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid #f5e6d8;
    }
    
    .stSelectbox > div > div {
        background: white;
        border-radius: 12px;
        border: 2px solid #f0d5c0;
    }

    .chat-bubble {
        background: white;
        border-radius: 20px 20px 20px 4px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 15px rgba(200,149,108,0.2);
        border: 2px solid #f5e6d8;
        display: inline-block;
        margin-left: 1rem;
    }
    
    .cat-container {
        display: flex;
        align-items: center;
        margin: 1rem 0;
    }

    pre.cat-ascii {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 1.1rem !important;
        line-height: 1.2 !important;
        color: #c8956c !important;
        white-space: pre !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        background: none !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        margin: 0.5rem auto !important;
        display: block !important;
        text-align: center !important;
        width: fit-content !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── ASCII ART ────────────────────────────────────────────────────────────────
CAT_ASCII_GRAND = (
    "  /\\\\_____/\\\\\n"
    " /  o   o  \\\\\n"
    "(  ==  ^  == )\n"
    " )          (\n"
    "(            )\n"
    "( (        ) )\n"
    "(__(__))___(__))__)"
)

CAT_ASCII_PETIT = (
    "  /\\\\_/\\\\\n"
    " ( ^.^ )\n"
    "  > 🐾 <"
)

def ascii_to_html(ascii_art: str) -> str:
    return ascii_art.replace("\n", "<br>")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size: 3rem;">🐱</div>
        <h2 style="color:#a0522d; margin:0;">FactureCat</h2>
        <p style="color:#c8956c; font-size:0.85rem;">Votre assistant comptable félin</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    api_key = st.secrets["GEMINI_API_KEY"]
    
    st.markdown("---")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
