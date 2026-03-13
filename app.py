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

# ─── ASCII ART ───────────────────────────────────────────────────────────
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

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
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
    api_key = st.text_input("🔑 Clé API Gemini", type="password", placeholder="AIza...")
    
    st.markdown("---")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    now = datetime.now()
    mois_choisi = mois_list[now.month - 1]
    annee_choisie = now.year
    st.markdown("""
    <div class="card">
        <p style="color:#a0522d; font-weight:700; margin:0 0 0.5rem 0;">📖 Guide rapide</p>
        <p style="color:#c8956c; font-size:0.85rem; margin:0;">
        1. 🔑 Entrez votre clé API<br>
        2. 📁 Uploadez vos factures<br>
        3. 🚀 Lancez l'extraction<br>
        4. ✏️ Vérifiez les données<br>
        5. 📥 Exportez en Excel
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align:center; margin-top:1rem;">
        <div class="cat-ascii" style="font-size:0.9rem !important;">{ascii_to_html(CAT_ASCII_PETIT)}</div>
        <p style="color:#d4a882; font-size:0.75rem; margin-top:0.3rem;">
            Miaouu~ je veille sur vos factures
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0;">
    <div style="font-size:4rem;">🐱</div>
    <h1 style="margin:0;">FactureCat</h1>
    <p style="color:#c8956c; margin:0.5rem 0 0 0; font-size:1.1rem;">
        Extraction intelligente de factures 🐾
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── MASCOTTE ACCUEIL ────────────────────────────────────────────────────────
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

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
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

# ─── FONCTIONS ───────────────────────────────────────────────────────────────
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

# ─── BOUTON EXTRACTION ───────────────────────────────────────────────────────
if fichiers and api_key:

    # ← NOUVEAU : détection des changements de fichiers
    noms_actuels = sorted([f.name for f in fichiers])
    noms_precedents = sorted(st.session_state.get("fichiers_extraits", []))
    fichiers_ont_change = noms_actuels != noms_precedents

    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        lancer = st.button("🐾 Lancer l'extraction !", type="primary", use_container_width=True)

    # ← NOUVEAU : avertissement si nouvelles factures détectées
    if fichiers_ont_change and "resultats" in st.session_state:
        st.warning("⚠️ De nouvelles factures ont été ajoutées. Clique sur **Lancer l'extraction** pour les analyser !")

    # ← NOUVEAU : condition corrigée
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
            st.session_state["fichiers_extraits"] = noms_actuels  # ← NOUVEAU
            st.session_state["scroll_to_dashboard"] = True
            st.rerun()

        # ─── RÉSULTATS ───────────────────────────────────────────────────────
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
                "fichier": "Fichier",
                "date": "Date",
                "fournisseur": "Fournisseur",
                "numero_facture": "N° Facture",
                "montant_ht": "Montant HT (€)",
                "tva": "TVA (€)",
                "montant_ttc": "Montant TTC (€)",
                "description": "Description",
                "categorie": "Catégorie",
                "statut": "Statut"
            })

            df["Mois"] = mois_rapide
            df["Année"] = annee_rapide

            colonnes_ordre = ["Fichier", "Date", "Mois", "Année", "Fournisseur",
                              "N° Facture", "Montant HT (€)", "TVA (€)",
                              "Montant TTC (€)", "Catégorie", "Description", "Statut"]
            df = df[colonnes_ordre]

            df_edit = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸", "À vérifier 🐱", "Erreur 🙀", "En attente 😺"]
                    ),
                    "Catégorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=["Transport","Repas","Hébergement",
                                 "Fournitures","Services","Autres"]
                    )
                }
            )

            # ─── SCROLL AUTOMATIQUE ───────────────────────────────────────────
            if st.session_state.get("scroll_to_dashboard"):
                components.html(
                    "<script>"
                    "setTimeout(() => {"
                    "  try {"
                    "    window.location.hash = 'dashboard';"
                    "  } catch (e) {}"
                    "  try {"
                    "    const el = document.getElementById('dashboard');"
                    "    if (el) el.scrollIntoView({behavior:'smooth'});"
                    "  } catch (e) {}"
                    "  try {"
                    "    const pel = window.parent.document.getElementById('dashboard');"
                    "    if (pel) pel.scrollIntoView({behavior:'smooth'});"
                    "  } catch (e) {}"
                    "}, 150);"
                    "</script>",
                    height=0,
                )
                st.session_state["scroll_to_dashboard"] = False

            # ─── STATS ───────────────────────────────────────────────────────
            st.markdown("### 📊 Tableau de bord")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">🐱</div>
                    <div style="font-size:2rem; font-weight:800; color:#a0522d;">{len(df_edit)}</div>
                    <div style="color:#c8956c;">Factures traitées</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                nb_valides = len(df_edit[df_edit["Statut"] == "Validé 😸"])
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">😸</div>
                    <div style="font-size:2rem; font-weight:800; color:#2d6b4a;">{nb_valides}</div>
                    <div style="color:#c8956c;">Validées</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                nb_erreurs = len(df_edit[df_edit["Statut"] == "Erreur 🙀"])
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">🙀</div>
                    <div style="font-size:2rem; font-weight:800; color:#c0392b;">{nb_erreurs}</div>
                    <div style="color:#c8956c;">Erreurs</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                try:
                    total = df_edit["Montant TTC (€)"].replace('', '0').astype(float).sum()
                    total_str = f"{total:,.2f} €"
                except:
                    total_str = "N/A"
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">💰</div>
                    <div style="font-size:1.5rem; font-weight:800; color:#a0522d;">{total_str}</div>
                    <div style="color:#c8956c;">Total TTC</div>
                </div>
                """, unsafe_allow_html=True)

            # ─── VISUALISATION DES FACTURES ───────────────────────────────────
            st.markdown("### 📄 Visualisation des Factures")
            for idx, fichier in enumerate(fichiers):
                with st.expander(f"Voir {fichier.name}", expanded=(idx == 0)):
                    fichier.seek(0)
                    if fichier.type == "application/pdf":
                        images = pdf_to_images(fichier.read())
                        st.image(images[0], use_container_width=True)
                        if len(images) > 1:
                            st.caption(f"📄 {len(images)} page(s)")
                    else:
                        st.image(Image.open(fichier), use_container_width=True)
            
            # ─── EXPORT ──────────────────────────────────────────────────────
            st.markdown("---")
            buffer = io.BytesIO()
            df_edit.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            
            col_dl = st.columns([1, 2, 1])
            with col_dl[1]:
                st.download_button(
                    label="📥 Télécharger Excel 🐾",
                    data=buffer,
                    file_name=f"factures_{mois_rapide}_{annee_rapide}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # ─── FOOTER ──────────────────────────────────────────────────────
            st.markdown("---")
            st.markdown(f"""
            <div style="text-align:center; padding: 1rem 0;">
                <div class="cat-ascii">{ascii_to_html(CAT_ASCII_GRAND)}</div>
                <p style="color:#a0522d; font-weight:700; margin-top:0.8rem;">
                    Purrrfait travail ! 🐾
                </p>
                <p style="color:#c8956c; font-size:0.85rem;">
                    FactureCat — Votre comptable félin 🐱
                </p>
            </div>
            """, unsafe_allow_html=True)

elif fichiers and not api_key:
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:2.5rem;">🙀</div>
        <div class="chat-bubble">
            <span style="color:#a0522d; font-weight:700;">
                Miaou ! J'ai besoin de ta clé API pour travailler... 🔑
            </span><br>
            <span style="color:#c8956c;">Entre-la dans le menu à gauche !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif not fichiers:
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 0;">
        <div class="cat-ascii" style="font-size:1.2rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
        <p style="font-size:1.2rem; font-weight:700; color:#a0522d; margin-top:1rem;">
            Uploadez vos factures pour commencer !
        </p>
        <p style="color:#c8956c;">Je suis prêt à analyser vos documents 🐾</p>
    </div>
    """, unsafe_allow_html=True)
