import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io

st.set_page_config(page_title="Extracteur de Factures", page_icon="🧾", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f0f4ff; }
    [data-testid="stSidebar"] {
        background-color: #e8eeff;
        border-right: 2px solid #c5cfff;
    }
    h1 { color: #5b6abf; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    h2, h3 { color: #7b8fd4; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #a8b8ff, #c5b8ff);
        color: white; border: none; border-radius: 12px;
        padding: 0.6rem 2rem; font-size: 1rem; font-weight: 600;
        box-shadow: 0 4px 15px rgba(168,184,255,0.4);
        transition: all 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(168,184,255,0.6);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #b8f0c8, #a8e8d8);
        color: #2d6b4a; border: none; border-radius: 12px;
        padding: 0.6rem 2rem; font-weight: 600;
        box-shadow: 0 4px 15px rgba(168,232,200,0.4);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover { transform: translateY(-2px); }
    .card {
        background: white; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(91,106,191,0.1);
        margin-bottom: 1rem; border: 1px solid #e0e6ff;
    }
    [data-testid="stFileUploader"] {
        background: white; border-radius: 16px;
        padding: 1rem; border: 2px dashed #a8b8ff;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #a8b8ff, #c5b8ff, #f0b8ff);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    api_key = st.text_input("🔑 Clé API Gemini", type="password", placeholder="AIza...")
    st.markdown("---")
    st.markdown("### 📅 Période")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    mois_choisi = st.selectbox("Mois", mois_list, index=pd.Timestamp.now().month - 1)
    annee_choisie = st.selectbox("Année", list(range(2023, 2031)),
                                 index=list(range(2023, 2031)).index(pd.Timestamp.now().year))
    st.markdown("---")
    st.markdown("### 📖 Guide")
    st.markdown("""
    1. 🔑 Entrez votre clé API Gemini  
    2. 📅 Choisissez la période  
    3. 📤 Uploadez vos factures  
    4. 🚀 Cliquez sur Analyser  
    5. ✏️ Corrigez si besoin  
    6. 📥 Exportez en Excel  
    """)

# ─── TITRE ───────────────────────────────────────────────────────────────────
st.markdown("# 🧾 Extracteur de Factures")
st.markdown("---")

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
fichiers = st.file_uploader(
    "📤 Déposez vos factures ici (PDF ou images)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

# ─── BOUTON ANALYSER ─────────────────────────────────────────────────────────
if fichiers and api_key:
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        analyser = st.button("🚀 Analyser les factures", type="primary", width='stretch')

    if analyser:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        resultats = []
        progress = st.progress(0)
        status_text = st.empty()

        for i, fichier in enumerate(fichiers):
            status_text.markdown(f"⏳ Analyse de **{fichier.name}**...")
            try:
                if fichier.type == "application/pdf":
                    pdf = fitz.open(stream=fichier.read(), filetype="pdf")
                    page = pdf[0]
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                else:
                    img = Image.open(fichier)

                prompt = """Analyse cette facture et retourne UNIQUEMENT ce JSON, rien d'autre, pas de texte avant ou après :
{
  "fournisseur_client": "nom du fournisseur ou client",
  "numero_facture": "numéro de facture",
  "type": "Facture",
  "montant_facture": "montant TTC en chiffres uniquement exemple 1250.00",
  "date_facture": "date au format JJ/MM/AAAA",
  "statut": "À valider"
}
Si une information est introuvable, mets "Non trouvé"."""

                response = model.generate_content([prompt, img])
                texte = response.text.strip()

                # Debug
                st.code(texte, language="json")

                # Nettoyage
                texte = texte.replace("```json", "").replace("```", "").strip()
                debut = texte.find("{")
                fin = texte.rfind("}") + 1
                if debut != -1 and fin > debut:
                    texte = texte[debut:fin]

                data = json.loads(texte)
                data["fichier"] = fichier.name
                resultats.append(data)

            except Exception as e:
                st.error(f"Erreur sur {fichier.name} : {e}")
                resultats.append({
                    "fournisseur_client": "Erreur",
                    "numero_facture": "",
                    "type": "",
                    "montant_facture": "",
                    "date_facture": "",
                    "statut": f"❌ {str(e)}",
                    "fichier": fichier.name
                })

            progress.progress((i + 1) / len(fichiers))

        status_text.markdown("✅ **Analyse terminée !**")

        # ─── TABLEAU ─────────────────────────────────────────────────────────
        df = pd.DataFrame(resultats)

        col_order = ["fichier", "fournisseur_client", "numero_facture",
                     "type", "montant_facture", "date_facture", "statut"]
        for col in col_order:
            if col not in df.columns:
                df[col] = ""
        df = df[col_order]

        df.columns = ["Fichier", "Fournisseur/Client", "N° Facture",
                      "Type", "Montant TTC", "Date", "Statut"]

        st.markdown("### 📊 Résultats")

        df_edit = st.data_editor(
            df,
            width='stretch',
            hide_index=True,
            column_config={
                "Statut": st.column_config.SelectboxColumn(
                    "Statut",
                    options=["À valider", "Validé ✅", "❌ Erreur", "En attente ⏳"]
                )
            }
        )

        # ─── STATISTIQUES ────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;">🧾</div>
                <div style="font-size:1.8rem; font-weight:700; color:#5b6abf;">{len(df_edit)}</div>
                <div style="color:#9aa0c4;">Factures traitées</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            nb_valides = len(df_edit[df_edit["Statut"] == "Validé ✅"])
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;">✅</div>
                <div style="font-size:1.8rem; font-weight:700; color:#2d6b4a;">{nb_valides}</div>
                <div style="color:#9aa0c4;">Validées</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            nb_erreurs = len(df_edit[df_edit["Statut"].str.startswith("❌", na=False)])
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;">❌</div>
                <div style="font-size:1.8rem; font-weight:700; color:#c0392b;">{nb_erreurs}</div>
                <div style="color:#9aa0c4;">Erreurs</div>
            </div>
            """, unsafe_allow_html=True)

        # ─── EXPORT EXCEL ────────────────────────────────────────────────────
        buffer = io.BytesIO()
        df_edit.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        col_dl = st.columns([1, 2, 1])
        with col_dl[1]:
            st.download_button(
                label=f"📥 Télécharger Excel — {mois_choisi} {annee_choisie}",
                data=buffer,
                file_name=f"factures_{mois_choisi}_{annee_choisie}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
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
