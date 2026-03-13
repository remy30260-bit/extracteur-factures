import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io

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
    
    /* Bouton principal */
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
    
    /* Bouton download */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #a8d8a8, #7fc87f);
        color: #2d5a2d; border: none; border-radius: 20px;
        padding: 0.6rem 2rem; font-weight: 700;
        box-shadow: 0 4px 15px rgba(127,200,127,0.4);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover { transform: translateY(-2px); }
    
    /* Cards */
    .card {
        background: white; border-radius: 20px; padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(200,149,108,0.15);
        margin-bottom: 1rem; border: 2px solid #f5e6d8;
    }
    
    /* Upload zone */
    [data-testid="stFileUploader"] {
        background: white; border-radius: 20px;
        padding: 1rem; border: 2px dashed #f0a070;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #f0a070, #e8856a, #c8956c);
        border-radius: 10px;
    }
    
    /* Tableau */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid #f5e6d8;
    }
    
    /* Selectbox & inputs */
    .stSelectbox > div > div {
        background: white;
        border-radius: 12px;
        border: 2px solid #f0d5c0;
    }
    
    /* Alert/warning */
    .stWarning {
        background: #fff8f0;
        border-left: 4px solid #f0a070;
        border-radius: 12px;
    }

    /* Chat bubble style */
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
</style>
""", unsafe_allow_html=True)

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
    st.markdown("### 📅 Période")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    mois_choisi = st.selectbox("Mois", mois_list, index=0)
    annee_choisie = st.selectbox("Année", list(range(2023, 2031)), index=2)
    
    st.markdown("---")
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
    
    st.markdown("""
    <div style="text-align:center; color:#d4a882; font-size:0.75rem; margin-top:1rem;">
        <pre style="color:#c8956c; font-size:0.7rem; line-height:1.2;">
 /\_/\  
( ^.^ ) 
 > 🐾 <
        </pre>
        Miaouu~ je veille sur vos factures
    </div>
    """, unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("""
    <div style="font-size:4rem; text-align:center; margin-top:0.5rem;">🐱</div>
    """, unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <h1 style="margin-bottom:0;">FactureCat</h1>
    <p style="color:#c8956c; margin-top:0; font-size:1.1rem;">
        Extraction intelligente de factures 🐾
    </p>
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

Retourne UNIQUEMENT ce JSON (sans markdown) :
{{
  "date": "JJ/MM/AAAA ou vide",
  "fournisseur": "nom du fournisseur",
  "numero_facture": "numéro ou vide",
  "montant_ht": "montant HT en euros (nombre uniquement)",
  "tva": "montant TVA en euros (nombre uniquement)",
  "montant_ttc": "montant TTC en euros (nombre uniquement)",
  "description": "courte description",
  "categorie": "Transport/Repas/Hébergement/Fournitures/Services/Autres"
}}"""

    response = model.generate_content([prompt, image])
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

# ─── BOUTON EXTRACTION ───────────────────────────────────────────────────────
if fichiers and api_key:
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        lancer = st.button("🐾 Lancer l'extraction !", type="primary", use_container_width=True)

    if lancer or "resultats" in st.session_state:
        
        if lancer:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
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
                
                progress.progress((i + 1) / len(fichiers))
            
            st.session_state["resultats"] = resultats
            st.session_state["mois"] = mois_choisi
            st.session_state["annee"] = annee_choisie

        # ─── RÉSULTATS ───────────────────────────────────────────────────────
        if "resultats" in st.session_state:
            resultats = st.session_state["resultats"]
            
            st.markdown("""
            <div class="cat-container">
                <div style="font-size:2.5rem;">😻</div>
                <div class="chat-bubble">
                    <span style="color:#a0522d; font-weight:700;">
                        Purrrfect ! Voici ce que j'ai trouvé 🐾 Vous pouvez modifier directement dans le tableau !
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Période rapide
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
            
            # ─── STATS ───────────────────────────────────────────────────────
            st.markdown("### 📊 Tableau de bord")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">🐱</div>
                    <div style="font-size:2rem; font-weight:800; color:#a0522d;">
                        {len(df_edit)}
                    </div>
                    <div style="color:#c8956c;">Factures traitées</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                nb_valides = len(df_edit[df_edit["Statut"] == "Validé 😸"])
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">😸</div>
                    <div style="font-size:2rem; font-weight:800; color:#2d6b4a;">
                        {nb_valides}
                    </div>
                    <div style="color:#c8956c;">Validées</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                nb_erreurs = len(df_edit[df_edit["Statut"] == "Erreur 🙀"])
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2.5rem;">🙀</div>
                    <div style="font-size:2rem; font-weight:800; color:#c0392b;">
                        {nb_erreurs}
                    </div>
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
                    <div style="font-size:1.5rem; font-weight:800; color:#a0522d;">
                        {total_str}
                    </div>
                    <div style="color:#c8956c;">Total TTC</div>
                </div>
                """, unsafe_allow_html=True)
            
            # ─── PRÉVISUALISATION ────────────────────────────────────────────
            st.markdown("### 🔍 Prévisualisation des fichiers")
            
            cols_prev = st.columns(min(len(fichiers), 3))
            for idx, fichier in enumerate(fichiers):
                fichier.seek(0)
                with cols_prev[idx % 3]:
                    st.markdown(f"""
                    <div class="card" style="text-align:center;">
                        <p style="color:#a0522d; font-weight:700; 
                           font-size:0.85rem; margin-bottom:0.5rem;">
                            🐾 {fichier.name}
                        </p>
                    """, unsafe_allow_html=True)
                    
                    if fichier.type == "application/pdf":
                        images = pdf_to_images(fichier.read())
                        st.image(images[0], use_container_width=True)
                        if len(images) > 1:
                            st.caption(f"📄 {len(images)} page(s)")
                    else:
                        st.image(Image.open(fichier), use_container_width=True)
                    
                    # Statut de cette facture
                    if idx < len(resultats):
                        statut = resultats[idx].get("statut", "")
                        st.markdown(f"""
                        <p style="text-align:center; margin-top:0.5rem;">
                            {statut}
                        </p>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
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
            
            st.markdown("""
            <div style="text-align:center; color:#c8956c; margin-top:1rem;">
                <pre style="color:#d4a882; font-size:0.8rem; line-height:1.3; display:inline-block;">
 /\_/\  
( ^.^ ) ~  Purrfait travail !
 > 🐾 <
                </pre>
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
    st.markdown("""
    <div style="text-align:center; padding:3
