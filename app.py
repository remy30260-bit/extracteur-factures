import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io

st.set_page_config(page_title="Extracteur de Factures", page_icon="🧾", layout="wide")

# ─── CSS PASTEL MODERNE ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fond général */
    .stApp {
        background-color: #f0f4ff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #e8eeff;
        border-right: 2px solid #c5cfff;
    }
    
    /* Titre principal */
    h1 {
        color: #5b6abf;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #7b8fd4;
    }
    
    /* Bouton primaire */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #a8b8ff, #c5b8ff);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(168, 184, 255, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(168, 184, 255, 0.6);
    }
    
    /* Bouton secondaire (download) */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #b8f0c8, #a8e8d8);
        color: #2d6b4a;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(168, 232, 200, 0.4);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Cards / containers */
    .card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(91, 106, 191, 0.1);
        margin-bottom: 1rem;
        border: 1px solid #e0e6ff;
    }
    
    /* Upload zone */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        border: 2px dashed #a8b8ff;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #a8b8ff, #c5b8ff, #f0b8ff);
        border-radius: 10px;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e0e6ff;
    }
    
    /* Info / Warning boxes */
    .stInfo {
        background-color: #eef1ff;
        border-left: 4px solid #a8b8ff;
        border-radius: 8px;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 10px;
        border-color: #c5cfff;
    }
    
    /* Chat animation */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    .chat-bounce {
        animation: bounce 1s infinite;
        display: inline-block;
        font-size: 1.5rem;
    }
    
    /* Badge statut */
    .badge-ok {
        background: #d4f5e2;
        color: #2d6b4a;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-err {
        background: #fde8e8;
        color: #c0392b;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(91, 106, 191, 0.08);
        border: 1px solid #e0e6ff;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #5b6abf;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #9aa0c4;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 1rem 0;">
    <h1 style="font-size:2.5rem;">🧾 Extracteur de Factures</h1>
    <p style="color:#9aa0c4; font-size:1.1rem;">
        Uploadez vos factures PDF ou images — extraction automatique par IA
    </p>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")
    api_key = st.text_input("🔑 Clé API Gemini", type="password", placeholder="Collez votre clé ici...")
    
    if api_key:
        st.success("✅ Clé API configurée")
        genai.configure(api_key=api_key)
    else:
        st.info("ℹ️ Clé API requise pour démarrer")
    
    st.markdown("---")
    st.markdown("### 📅 Mois cible")
    mois_liste = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ]
    mois_choisi = st.selectbox("Sélectionnez le mois", mois_liste, index=0)
    annee_choisie = st.number_input("Année", min_value=2020, max_value=2035, value=2026, step=1)
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; color:#9aa0c4; font-size:0.8rem;">
        Période sélectionnée<br>
        <span style="font-size:1.1rem; font-weight:700; color:#5b6abf;">
            {mois_choisi} {annee_choisie}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ─── FONCTIONS ───────────────────────────────────────────────────────────────
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def extraire_donnees(image, model):
    prompt = """
    Analyse cette facture et extrais les informations suivantes en JSON uniquement.
    Réponds UNIQUEMENT avec le JSON, rien d'autre.
    
    {
        "fournisseur_client": "nom du fournisseur qui ÉMET la facture",
        "numero_facture": "numéro de facture",
        "type": "Facture / Avoir / Note de frais / Facture pro-forma",
        "montant_facture": "montant TTC total (nombre uniquement, sans symbole)",
        "date_facture": "date au format DD/MM/YYYY"
    }
    
    Si une information est absente, mets null.
    """
    response = model.generate_content([prompt, image])
    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)

# ─── ZONE UPLOAD ─────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 📁 Déposez vos factures ici")
fichiers = st.file_uploader(
    "Formats acceptés : PDF, PNG, JPG, JPEG",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if fichiers:
    nb = len(fichiers)
    cols_meta = st.columns(3)
    with cols_meta[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{nb}</div>
            <div class="metric-label">Fichier(s) uploadé(s)</div>
        </div>
        """, unsafe_allow_html=True)
    with cols_meta[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{mois_choisi[:3]}</div>
            <div class="metric-label">Mois sélectionné</div>
        </div>
        """, unsafe_allow_html=True)
    with cols_meta[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{annee_choisie}</div>
            <div class="metric-label">Année</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ─── TRAITEMENT ──────────────────────────────────────────────────────────────
if fichiers and api_key:
    st.markdown("")
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        lancer = st.button("🚀 Extraire les données", type="primary", use_container_width=True)
    
    if lancer:
        model = genai.GenerativeModel("gemini-2.5-flash")
        resultats = []
        
        # Chat + progress
        chat_container = st.empty()
        progress_container = st.empty()
        status_container = st.empty()
        
        messages_chat = [
            "🤔 Je lis vos factures...",
            "🔍 J'analyse les montants...",
            "📋 J'extrais les données...",
            "✨ Presque terminé !",
            "🎉 C'est dans la boîte !"
        ]
        
        for i, fichier in enumerate(fichiers):
            # Animation chat
            msg_idx = min(i, len(messages_chat) - 1)
            chat_container.markdown(f"""
            <div style="
                background: white;
                border-radius: 16px;
                padding: 1rem 1.5rem;
                display: inline-flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 15px rgba(91,106,191,0.1);
                border: 1px solid #e0e6ff;
                margin-bottom: 0.5rem;
            ">
                <span class="chat-bounce">🤖</span>
                <span style="color:#5b6abf; font-weight:500;">{messages_chat[msg_idx]}</span>
                <span style="color:#9aa0c4; font-size:0.85rem;">— {fichier.name}</span>
            </div>
            """, unsafe_allow_html=True)
            
            progress_container.progress((i) / len(fichiers))
            
            try:
                images = []
                if fichier.type == "application/pdf":
                    images = pdf_to_images(fichier.read())
                else:
                    images = [Image.open(fichier)]
                
                donnees = extraire_donnees(images[0], model)
                donnees["fichier"] = fichier.name
                donnees["statut"] = "✅ OK"
                resultats.append(donnees)
                
            except Exception as e:
                resultats.append({
                    "fichier": fichier.name,
                    "statut": f"❌ Erreur: {str(e)}"
                })
            
            progress_container.progress((i + 1) / len(fichiers))
        
        # Message final
        chat_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f0fff4, #e8f5ff);
            border-radius: 16px;
            padding: 1rem 1.5rem;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 15px rgba(91,106,191,0.1);
            border: 1px solid #c5f0d8;
            margin-bottom: 0.5rem;
        ">
            <span style="font-size:1.5rem;">🤖</span>
            <span style="color:#2d6b4a; font-weight:600;">Extraction terminée ! {len(resultats)} facture(s) traitée(s)</span>
        </div>
        """, unsafe_allow_html=True)
        
        progress_container.progress(1.0)
        
        # ─── TABLEAU ─────────────────────────────────────────────────────────
        df = pd.DataFrame(resultats)
        
        cols_order = ["fournisseur_client", "numero_facture", "type", "montant_facture", "date_facture", "statut"]
        cols_order = [c for c in cols_order if c in df.columns]
        df = df[cols_order]
        
        # Formatage montant
        if "montant_facture" in df.columns:
            df["montant_facture"] = pd.to_numeric(
                df["montant_facture"].astype(str)
                .str.replace("€", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors="coerce"
            ).apply(lambda x: f"{x:,.2f} €" if pd.notna(x) else "")
        
        # Formatage date
        if "date_facture" in df.columns:
            df["date_facture"] = pd.to_datetime(
                df["date_facture"], dayfirst=True, errors="coerce"
            ).dt.strftime("%m/%Y").fillna("")
        
        df = df.rename(columns={
            "fournisseur_client": "Fournisseur / Client",
            "numero_facture": "N° Facture",
            "type": "Type",
            "montant_facture": "Montant TTC",
            "date_facture": "Date",
            "statut": "Statut"
        })
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### 📊 Résultats — {mois_choisi} {annee_choisie}")
        st.dataframe(df, use_container_width=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ─── EXPORT ──────────────────────────────────────────────────────────
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        col_dl = st.columns([1, 2, 1])
        with col_dl[1]:
            st.download_button(
                label=f"📥 Télécharger Excel — {mois_choisi} {annee_choisie}",
                data=buffer,
                file_name=f"factures_{mois_choisi}_{annee_choisie}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

elif fichiers and not api_key:
    st.warning("⚠️ Entrez votre clé API Gemini dans le menu à gauche pour démarrer")

elif not fichiers:
    st.markdown("""
    <div style="text-align:center; padding:2rem; color:#9aa0c4;">
        <div style="font-size:3rem;">☝️</div>
        <p style="font-size:1.1rem;">Uploadez vos factures ci-dessus pour commencer</p>
    </div>
    """, unsafe_allow_html=True)
