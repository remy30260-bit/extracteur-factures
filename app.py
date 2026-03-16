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
from supabase import create_client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = ""

    if st.session_state["authenticated"]:
        return True

    st.markdown("""
    <div style="max-width:400px; margin:5rem auto; text-align:center;">
        <div style="font-size:4rem;">🐱</div>
        <h2 style="color:#a0522d;">FactureCat</h2>
        <p style="color:#c8956c;">Connexion requise 🔐</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])
    with col[1]:
        mode = st.radio(
            "Mode",
            ["🔑 Se connecter", "✨ Créer un compte"],
            horizontal=True,
            label_visibility="collapsed"
        )
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Mot de passe", type="password")

    return False

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
        min-width: 70px !important;
        max-width: 70px !important;
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
    .card-green {
        background: white; border-radius: 20px; padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(127,200,127,0.15);
        margin-bottom: 1rem; border: 2px solid #d5f0d5;
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
        border-radius: 16px; overflow: hidden;
        border: 2px solid #f5e6d8;
    }
    .stSelectbox > div > div {
        background: white; border-radius: 12px;
        border: 2px solid #f0d5c0;
    }
    .chat-bubble {
        background: white; border-radius: 20px 20px 20px 4px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 15px rgba(200,149,108,0.2);
        border: 2px solid #f5e6d8;
        display: inline-block; margin-left: 1rem;
    }
    .cat-container { display: flex; align-items: center; margin: 1rem 0; }
    pre.cat-ascii {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 1.1rem !important; line-height: 1.2 !important;
        color: #c8956c !important; white-space: pre !important;
        word-break: normal !important; overflow-wrap: normal !important;
        background: none !important; border: none !important;
        padding: 0.5rem 1rem !important; margin: 0.5rem auto !important;
        display: block !important; text-align: center !important;
        width: fit-content !important; max-width: 100% !important;
    }

    /* ── SIDEBAR ICÔNES ── */
    [data-testid="stSidebar"] .stButton button {
        width: 45px !important;
        height: 45px !important;
        border-radius: 12px !important;
        font-size: 1.5rem !important;
        padding: 0 !important;
        border: 2px solid transparent !important;
        background: #fff8f3 !important;
        color: inherit !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        margin: 3px auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #f5e6d8 !important;
        border-color: #f0a070 !important;
        transform: scale(1.1) !important;
        box-shadow: none !important;
    }
    /* Cache uniquement les paragraphes markdown de la sidebar, PAS les emojis des boutons */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        display: none !important;
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

# ─── INITIALISATION ───────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "factures"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.button("📄", help="Factures — Extraction intelligente"):
        st.session_state["page"] = "factures"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("💰", help="Notes de frais — Gestion des dépenses"):
        st.session_state["page"] = "notes_frais"
        st.rerun()

    st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

    if st.button("🚪", help="Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["page"] == "factures":

    st.markdown("---")

    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3.5rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Bonjour ! Je suis FactureCat 🐾</strong><br>
            <span style="color:#c8956c;">
                Déposez vos factures ci-dessous et je m'occupe de tout extraire pour vous !
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── CONFIGURATION ────────────────────────────────────────────────────────
    with st.expander("⚙️ Configuration", expanded=not st.session_state.get("api_key")):
        api_key = st.text_input("🔑 Clé API Gemini", type="password",
                                value=st.session_state.get("api_key", ""),
                                help="Obtenez votre clé sur https://makersuite.google.com/")
        if api_key:
            st.session_state["api_key"] = api_key

        col_m, col_a = st.columns(2)
        mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                     "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
        with col_m:
            mois_choisi = st.selectbox("📅 Mois", mois_list,
                                       index=datetime.now().month - 1)
        with col_a:
            annee_choisie = st.selectbox("📅 Année", list(range(2023, 2031)),
                                         index=list(range(2023, 2031)).index(datetime.now().year))

    api_key = st.session_state.get("api_key", "")

    fichiers = st.file_uploader(
        "🐾 Glissez vos factures ici",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Formats acceptés : PDF, JPG, PNG"
    )

    if fichiers:
        st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #fff8f3, #fdf0e8);">
            <span style="color:#a0522d; font-weight:700;">
                🐱 Miaou ! {len(fichiers)} fichier(s) détecté(s) et prêt(s) à être analysé(s) 🐾
            </span>
        </div>
        """, unsafe_allow_html=True)

    def pdf_to_images(pdf_bytes):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images

    def extraire_facture(fichier, model, mois, annee):
        if fichier.type == "application/pdf":
            images = pdf_to_images(fichier.read())
            image = images[0]
        else:
            image = Image.open(fichier)

        prompt = f"""Analyse cette facture et extrais les informations en JSON.
Période comptable : {mois} {annee}

Retourne UNIQUEMENT ce JSON brut, sans markdown, sans backticks :
{{
  "date": "JJ/MM/AAAA ou vide",
  "fournisseur": "nom du fournisseur",
  "numero_facture": "numéro ou vide",
  "montant_ht": "montant HT en euros (nombre uniquement, ex: 100.00)",
  "tva": "montant TVA en euros (nombre uniquement)",
  "montant_ttc": "montant TTC en euros (nombre uniquement)",
  "description": "courte description du contenu",
  "categorie": "Transport/Repas/Hébergement/Fournitures/Services/Autres"
}}
IMPORTANT: Réponds UNIQUEMENT avec le JSON, rien d'autre."""

        response = model.generate_content([prompt, image])
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        return json.loads(text)

    if fichiers and api_key:
        noms_actuels = sorted([f.name for f in fichiers])
        noms_precedents = sorted(st.session_state.get("fichiers_extraits", []))
        fichiers_ont_change = noms_actuels != noms_precedents

        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            lancer = st.button("🐾 Lancer l'extraction !", type="primary", use_container_width=True)

        if fichiers_ont_change and "resultats" in st.session_state:
            st.warning("⚠️ De nouvelles factures ont été ajoutées. Clique sur **Lancer l'extraction** pour les analyser !")

        doit_extraire = lancer and ("resultats" not in st.session_state or fichiers_ont_change)

        if doit_extraire or ("resultats" in st.session_state and not fichiers_ont_change):

            if doit_extraire:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")

                st.markdown("""
                <div class="cat-container">
                    <div style="font-size:2.5rem;">😺</div>
                    <div class="chat-bubble">
                        <span style="color:#a0522d; font-weight:700;">
                            Je suis sur le coup ! Analyse en cours... 🐾
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                progress = st.progress(0)
                resultats = []

                for i, fichier in enumerate(fichiers):
                    fichier.seek(0)
                    status_cats = ["😺", "🐱", "😸", "🙀", "😻"]
                    cat = status_cats[i % len(status_cats)]
                    with st.spinner(f"{cat} Analyse de {fichier.name}..."):
                        try:
                            data = extraire_facture(fichier, model, mois_choisi, annee_choisie)
                            data["fichier"] = fichier.name
                            data["statut"] = "Validé 😸"
                            resultats.append(data)
                        except Exception as e:
                            resultats.append({
                                "fichier": fichier.name,
                                "date": "", "fournisseur": "", "numero_facture": "",
                                "montant_ht": "", "tva": "", "montant_ttc": "",
                                "description": str(e), "categorie": "",
                                "statut": "Erreur 🙀"
                            })
                    progress.progress(int((i + 1) / len(fichiers) * 100))

                progress.progress(100)
                progress.empty()
                st.session_state["resultats"] = resultats
                st.session_state["mois"] = mois_choisi
                st.session_state["annee"] = annee_choisie
                st.session_state["fichiers_extraits"] = noms_actuels
                st.session_state["scroll_to_dashboard"] = True
                st.rerun()

            if "resultats" in st.session_state:
                resultats = st.session_state["resultats"]

                st.markdown("""
                <div class="cat-container">
                    <div style="font-size:2.5rem;">😻</div>
                    <div class="chat-bubble">
                        <span style="color:#a0522d; font-weight:700;">
                            Purrrfect ! Voici ce que j'ai trouvé 🐾
                        </span><br>
                        <span style="color:#c8956c;">Vous pouvez modifier directement dans le tableau !</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div id="dashboard"></div>', unsafe_allow_html=True)

                col_p1, col_p2, col_p3 = st.columns([2, 2, 4])
                with col_p1:
                    mois_rapide = st.selectbox("📅 Mois", mois_list,
                        index=mois_list.index(st.session_state.get("mois", mois_choisi)))
                with col_p2:
                    annee_rapide = st.selectbox("📅 Année", list(range(2023, 2031)),
                        index=list(range(2023, 2031)).index(st.session_state.get("annee", annee_choisie)))

                df = pd.DataFrame(resultats)
                df = df.rename(columns={
                    "fichier": "Fichier", "date": "Date",
                    "fournisseur": "Fournisseur", "numero_facture": "N° Facture",
                    "montant_ht": "Montant HT (€)", "tva": "TVA (€)",
                    "montant_ttc": "Montant TTC (€)", "description": "Description",
                    "categorie": "Catégorie", "statut": "Statut"
                })
                df["Mois"] = mois_rapide
                df["Année"] = annee_rapide
                colonnes_ordre = ["Fichier", "Date", "Mois", "Année", "Fournisseur",
                                  "N° Facture", "Montant HT (€)", "TVA (€)",
                                  "Montant TTC (€)", "Catégorie", "Description", "Statut"]
                df = df[colonnes_ordre]

                df_edit = st.data_editor(
                    df, use_container_width=True, hide_index=True,
                    column_config={
                        "Statut": st.column_config.SelectboxColumn(
                            "Statut",
                            options=["Validé 😸", "À vérifier 🐱", "Erreur 🙀", "En attente 😺"]
                        ),
                        "Catégorie": st.column_config.SelectboxColumn(
                            "Catégorie",
                            options=["Transport","Repas","Hébergement","Fournitures","Services","Autres"]
                        )
                    }
                )

                if st.session_state.get("scroll_to_dashboard"):
                    components.html(
                        "<script>setTimeout(() => {"
                        "try { window.location.hash = 'dashboard'; } catch(e){}"
                        "try { const el = document.getElementById('dashboard');"
                        "if(el) el.scrollIntoView({behavior:'smooth'}); } catch(e){}"
                        "try { const pel = window.parent.document.getElementById('dashboard');"
                        "if(pel) pel.scrollIntoView({behavior:'smooth'}); } catch(e){}"
                        "}, 150);</script>", height=0,
                    )
                    st.session_state["scroll_to_dashboard"] = False

                st.markdown("### 📊 Tableau de bord")
                col1, col2, col3, col4 = st.columns(4)

                try:
                    total_ttc = sum(float(str(r.get("montant_ttc","0")).replace(",",".")
