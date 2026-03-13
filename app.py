import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide")

# ─── ASCII ART ────────────────────────────────────────────────────────────────
CAT_ASCII_GRAND = (
    "&#160;&#160;/\\_____/\\\n"
    "&#160;/&#160;&#160;o&#160;&#160;&#160;o&#160;&#160;\\\n"
    "(&#160;==&#160;&#160;^&#160;&#160;==&#160;)\n"
    "&#160;)&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;(\n"
    "(&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;)\n"
    "(&#160;(&#160;&#160;)&#160;&#160;&#160;(&#160;&#160;)&#160;)\n"
    "(__(__))___(__)__)"
)

CAT_ASCII_PETIT = (
    "&#160;/\\_/\\\n"
    "(&#160;^.^&#160;)\n"
    "&#160;(__)__)"
)

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
        justify-content: center;
        padding: 2rem;
    }

    pre.cat-ascii {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 1.1rem !important;
        line-height: 1.5 !important;
        color: #c8956c !important;
        white-space: pre !important;
        word-break: keep-all !important;
        overflow-wrap: normal !important;
        background: none !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 auto !important;
        display: inline-block !important;
        text-align: left !important;
        width: auto !important;
        max-width: none !important;
    }

    .kpi-box {
        background: white;
        border-radius: 12px;
        padding: 0.6rem 0.8rem;
        border: 2px solid #f5e6d8;
        text-align: center;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ─── FONCTIONS ────────────────────────────────────────────────────────────────

def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def image_to_bytes(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def extraire_json(texte):
    texte = texte.strip()
    if "```" in texte:
        blocs = texte.split("```")
        for b in blocs:
            b2 = b.strip()
            if b2.startswith("json"):
                b2 = b2[4:].strip()
            if b2.startswith("{"):
                texte = b2
                break
    start = texte.find("{")
    end   = texte.rfind("}") + 1
    if start != -1 and end > start:
        texte = texte[start:end]
    return json.loads(texte)

def analyser_facture(fichier, client_genai):
    fichier.seek(0)
    raw = fichier.read()

    if fichier.type == "application/pdf":
        images = pdf_to_images(raw)
        img_bytes = image_to_bytes(images[0])
        mime = "image/png"
    else:
        mime = fichier.type
        img_bytes = raw

    prompt = """Tu es un expert comptable. Analyse cette facture et extrais les informations suivantes en JSON strict :
{
  "date": "JJ/MM/AAAA ou vide",
  "mois": "nom du mois en français ou vide",
  "annee": "AAAA ou vide",
  "fournisseur": "nom du fournisseur",
  "numero_facture": "numéro ou vide",
  "montant_ht": nombre ou 0,
  "tva": nombre ou 0,
  "montant_ttc": nombre ou 0,
  "categorie": "une catégorie parmi: Fournitures, Services, Logiciels, Transport, Restauration, Marketing, Immobilier, Utilities, Autre",
  "description": "description courte en français"
}
Réponds UNIQUEMENT avec le JSON, sans texte autour."""

    model = client_genai.GenerativeModel("gemini-2.5-flash-preview")
    response = model.generate_content([
        {"mime_type": mime, "data": img_bytes},
        prompt
    ])
    
    data = extraire_json(response.text)
    return {
        "Fichier":         fichier.name,
        "Date":            data.get("date", ""),
        "Mois":            data.get("mois", ""),
        "Année":           data.get("annee", ""),
        "Fournisseur":     data.get("fournisseur", ""),
        "N° Facture":      data.get("numero_facture", ""),
        "Montant HT (€)":  data.get("montant_ht", 0),
        "TVA (€)":         data.get("tva", 0),
        "Montant TTC (€)": data.get("montant_ttc", 0),
        "Catégorie":       data.get("categorie", "Autre"),
        "Description":     data.get("description", ""),
        "statut":          "✅ Validé 😸",
    }

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0;">
        <pre class="cat-ascii" style="font-size:0.85rem !important;">{CAT_ASCII_PETIT}</pre>
        <h2 style="color:#a0522d; margin:0.5rem 0;">FactureCat</h2>
        <p style="color:#c8956c; font-size:0.85rem;">Votre comptable félin 🐱</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔑 Configuration")
    api_key = st.text_input("Clé API Gemini", type="password", placeholder="AIza...")

    if api_key and st.sidebar.button("🔍 Modèles dispo"):
    genai.configure(api_key=api_key)
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            st.sidebar.code(m.name)

    
    st.markdown("---")
    st.markdown("### 📂 Filtres")
    
    mois_liste = ["Tous", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    mois_rapide  = st.selectbox("🗓️ Mois", mois_liste)
    annee_rapide = st.selectbox("📆 Année", ["Toutes", "2024", "2025", "2026"])
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;">
        <p style="color:#c8956c; font-size:0.8rem;">
            Formats acceptés :<br>📄 PDF • 🖼️ PNG • JPG
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1rem 0 2rem 0;">
    <h1 style="font-size:2.5rem; margin-bottom:0.2rem;">🐱 FactureCat</h1>
    <p style="color:#c8956c; font-size:1.1rem;">Analysez vos factures avec l'IA en quelques secondes ✨</p>
</div>
""", unsafe_allow_html=True)

# ─── UPLOAD ───────────────────────────────────────────────────────────────────
fichiers = st.file_uploader(
    "📁 Déposez vos factures ici",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if fichiers and api_key:
    
    client_genai = genai.configure(api_key=api_key)

    if st.button("🐾 Analyser les factures", use_container_width=False):
        resultats = []
        progress = st.progress(0)
        status   = st.empty()

        for i, fichier in enumerate(fichiers):
            status.markdown(f"""
            <div class="cat-container">
                <pre class="cat-ascii" style="font-size:0.8rem !important;">{CAT_ASCII_PETIT}</pre>
                <div class="chat-bubble">
                    <span style="color:#a0522d; font-weight:700;">
                        Analyse de {fichier.name}...
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                r = analyser_facture(fichier, genai)
            except Exception as e:
                r = {
                    "Fichier": fichier.name, "Date": "", "Mois": "", "Année": "",
                    "Fournisseur": "", "N° Facture": "", "Montant HT (€)": 0,
                    "TVA (€)": 0, "Montant TTC (€)": 0, "Catégorie": "Autre",
                    "Description": str(e), "statut": "❌ Erreur 🙀",
                }
            resultats.append(r)
            progress.progress((i + 1) / len(fichiers))

        status.empty()
        progress.empty()
        st.session_state["resultats"] = resultats
        st.session_state["fichiers"]  = fichiers

    # ─── RÉSULTATS ────────────────────────────────────────────────────────────
    if "resultats" in st.session_state:
        resultats = st.session_state["resultats"]
        fichiers  = st.session_state["fichiers"]

        df = pd.DataFrame([{k: v for k, v in r.items() if k != "statut"} for r in resultats])

        # Filtres
        df_filtre = df.copy()
        if mois_rapide != "Tous":
            df_filtre = df_filtre[df_filtre["Mois"].str.lower() == mois_rapide.lower()]
        if annee_rapide != "Toutes":
            df_filtre = df_filtre[df_filtre["Année"].astype(str) == annee_rapide]

        # KPIs globaux
        total_ttc = df_filtre["Montant TTC (€)"].sum()
        total_ht  = df_filtre["Montant HT (€)"].sum()
        total_tva = df_filtre["TVA (€)"].sum()
        nb        = len(df_filtre)

        st.markdown("### 📊 Résumé")
        k1, k2, k3, k4 = st.columns(4)
        for col, label, val, emoji in [
            (k1, "Factures",     nb,                      "🐾"),
            (k2, "Total HT",     f"{total_ht:.2f} €",     "💶"),
            (k3, "Total TVA",    f"{total_tva:.2f} €",    "📊"),
            (k4, "Total TTC",    f"{total_ttc:.2f} €",    "💰"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">{emoji}</div>
                    <div style="color:#c8956c; font-size:0.85rem; font-weight:600;">{label}</div>
                    <div style="color:#a0522d; font-size:1.4rem; font-weight:800;">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        # ─── TABLEAU ÉDITABLE ─────────────────────────────────────────────────
        st.markdown("### ✏️ Tableau éditable")
        df_edit = st.data_editor(
            df_filtre.drop(columns=["Fichier"]),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Catégorie": st.column_config.SelectboxColumn(
                    options=["Fournitures","Services","Logiciels","Transport",
                             "Restauration","Marketing","Immobilier","Utilities","Autre"]
                ),
                "Montant HT (€)":  st.column_config.NumberColumn(format="%.2f €"),
                "TVA (€)":         st.column_config.NumberColumn(format="%.2f €"),
                "Montant TTC (€)": st.column_config.NumberColumn(format="%.2f €"),
            }
        )

        # ─── FACTURES CORRÉLÉES ───────────────────────────────────────────────
        st.markdown("### 🔍 Factures & Données extraites")

        def kpi(label, val, emoji):
            return f"""
            <div class="kpi-box">
                <div style="font-size:1.2rem;">{emoji}</div>
                <div style="font-size:0.7rem; color:#c8956c; font-weight:600;">{label}</div>
                <div style="font-size:0.9rem; color:#a0522d; font-weight:800;">{val or "—"}</div>
            </div>"""

        for idx, (fichier, resultat) in enumerate(zip(fichiers, resultats)):
            fichier.seek(0)
            statut  = resultat.get("statut", "")
            couleur = "#e8f5e9" if "Validé" in statut else "#ffeaea" if "Erreur" in statut else "#fff8f3"

            st.markdown(f"""
            <div style="background:{couleur}; border-radius:16px; padding:0.8rem 1rem;
                        border:2px solid #f5e6d8; margin-bottom:0.3rem;">
                <span style="font-size:1.2rem;">🐾</span>
                <span style="color:#a0522d; font-weight:700; margin-left:0.5rem;">{fichier.name}</span>
                <span style="float:right;">{statut}</span>
            </div>
            """, unsafe_allow_html=True)

            col_img, col_data = st.columns([1, 3])

            with col_img:
                fichier.seek(0)
                if fichier.type == "application/pdf":
                    images = pdf_to_images(fichier.read())
                    st.image(images[0], use_container_width=True)
                    if len(images) > 1:
                        st.caption(f"📄 {len(images)} page(s)")
                else:
                    st.image(Image.open(fichier), use_container_width=True)

            with col_data:
                r1c1, r1c2, r1c3, r1c4 = st.columns(4)
                r2c1, r2c2, r2c3, r2c4 = st.columns(4)
                r3c1, r3c2             = st.columns(2)

                with r1c1: st.markdown(kpi("Date",       resultats[idx]["Date"],            "📅"), unsafe_allow_html=True)
                with r1c2: st.markdown(kpi("Mois",       resultats[idx]["Mois"],            "🗓️"), unsafe_allow_html=True)
                with r1c3: st.markdown(kpi("Année",      resultats[idx]["Année"],           "📆"), unsafe_allow_html=True)
                with r1c4: st.markdown(kpi("N° Facture", resultats[idx]["N° Facture"],      "🔢"), unsafe_allow_html=True)

                st.markdown("<div style='margin:0.3rem 0;'></div>", unsafe_allow_html=True)

                with r2c1: st.markdown(kpi("Montant HT",  f"{resultats[idx]['Montant HT (€)']:.2f} €",  "💶"), unsafe_allow_html=True)
                with r2c2: st.markdown(kpi("TVA",         f"{resultats[idx]['TVA (€)']:.2f} €",         "📊"), unsafe_allow_html=True)
                with r2c3: st.markdown(kpi("Montant TTC", f"{resultats[idx]['Montant TTC (€)']:.2f} €", "💰"), unsafe_allow_html=True)
                with r2c4: st.markdown(kpi("Catégorie",   resultats[idx]["Catégorie"],                  "🏷️"), unsafe_allow_html=True)

                st.markdown("<div style='margin:0.3rem 0;'></div>", unsafe_allow_html=True)

                with r3c1: st.markdown(kpi("Fournisseur", resultats[idx]["Fournisseur"],  "🏢"), unsafe_allow_html=True)
                with r3c2: st.markdown(kpi("Description", resultats[idx]["Description"],  "📝"), unsafe_allow_html=True)

            st.markdown("<hr style='border:1px solid #f0d5c0; margin:0.8rem 0;'>", unsafe_allow_html=True)

        # ─── EXPORT ───────────────────────────────────────────────────────────
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

        # ─── FOOTER ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align:center; padding: 1rem 0;">
            <pre class="cat-ascii">{CAT_ASCII_GRAND}</pre>
            <p style="color:#a0522d; font-weight:700; margin-top:0.8rem;">Purrrfait travail ! 🐾</p>
            <p style="color:#c8956c; font-size:0.85rem;">FactureCat — Votre comptable félin 🐱</p>
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
        <pre class="cat-ascii" style="font-size:1.2rem !important;">{CAT_ASCII_GRAND}</pre>
        <p style="font-size:1.2rem; font-weight:700; color:#a0522d; margin-top:1rem;">
            Uploadez vos factures pour commencer !
        </p>
        <p style="color:#c8956c;">Je suis prêt à analyser vos documents 🐾</p>
    </div>
    """, unsafe_allow_html=True)
