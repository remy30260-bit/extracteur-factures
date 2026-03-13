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
    .stApp {
        background-color: #f0f4ff;
    }
    [data-testid="stSidebar"] {
        background-color: #e8eeff;
        border-right: 2px solid #c5cfff;
    }
    h1 {
        color: #5b6abf;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
    }
    h2, h3 {
        color: #7b8fd4;
    }
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
    .card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(91, 106, 191, 0.1);
        margin-bottom: 1rem;
        border: 1px solid #e0e6ff;
    }
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        border: 2px dashed #a8b8ff;
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
    
    mois_liste = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ]
    mois_choisi = st.selectbox("Mois", mois_liste, index=0)
    annee_choisie = st.number_input("Année", min_value=2020, max_value=2030, value=2026)
    
    st.markdown("---")
    st.markdown("### 📋 Colonnes Excel")
    colonnes_actives = st.multiselect(
        "Choisir les colonnes",
        ["Fournisseur / Client", "N° Facture", "Type", "Montant TTC", "Date", "Statut"],
        default=["Fournisseur / Client", "N° Facture", "Type", "Montant TTC", "Date", "Statut"]
    )

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🧾 Extracteur de Factures")
st.markdown(f"<p style='color:#9aa0c4; font-size:1.1rem;'>Période sélectionnée : <b>{mois_choisi} {annee_choisie}</b></p>", unsafe_allow_html=True)

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
fichiers = st.file_uploader(
    "📂 Déposez vos factures ici (PDF ou images)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ─── TRAITEMENT ──────────────────────────────────────────────────────────────
if fichiers and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if st.button("🚀 Extraire les données", type="primary", use_container_width=True):

        resultats = []
        total = len(fichiers)

        # Barre de progression avec chat
        chat_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()

        messages_chat = [
            "🐱 Je lis vos factures...",
            "🐱 J'analyse les montants...",
            "🐱 Je repère les fournisseurs...",
            "🐱 Presque fini...",
            "🐱 Je finalise tout ça !",
        ]

        for i, fichier in enumerate(fichiers):
            # Message chat animé
            msg_index = min(i, len(messages_chat) - 1)
            chat_placeholder.markdown(f"""
            <div style="background:white; border-radius:16px; padding:1rem; 
                        border:2px solid #e0e6ff; text-align:center;
                        font-size:1.2rem; color:#5b6abf; margin-bottom:0.5rem;">
                {messages_chat[msg_index]}
                <br><small style="color:#9aa0c4;">{fichier.name}</small>
            </div>
            """, unsafe_allow_html=True)

            progress_bar.progress((i + 1) / total)
            status_text.markdown(f"<p style='color:#9aa0c4; text-align:center;'>Fichier {i+1} / {total}</p>", unsafe_allow_html=True)

            try:
                # Lecture fichier
                if fichier.type == "application/pdf":
                    pdf = fitz.open(stream=fichier.read(), filetype="pdf")
                    page = pdf[0]
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                else:
                    img = Image.open(fichier)

                # Prompt Gemini
                prompt = """Analyse cette facture et retourne UNIQUEMENT un JSON avec ces champs :
{
  "fournisseur_client": "nom du fournisseur ou client",
  "numero_facture": "numéro de facture",
  "type": "Facture ou Avoir ou Note de frais",
  "montant_facture": "montant TTC avec symbole €",
  "date_facture": "date au format JJ/MM/AAAA",
  "statut": "À valider"
}
Réponds UNIQUEMENT avec le JSON, sans texte autour."""

                response = model.generate_content([prompt, img])
                texte = response.text.strip()
                texte = texte.replace("```json", "").replace("```", "").strip()
                data = json.loads(texte)
                data["fichier"] = fichier.name
                resultats.append(data)

            except Exception as e:
                resultats.append({
                    "fournisseur_client": "Erreur",
                    "numero_facture": "",
                    "type": "",
                    "montant_facture": "",
                    "date_facture": "",
                    "statut": f"❌ {str(e)}",
                    "fichier": fichier.name
                })

        # Fin
        chat_placeholder.markdown("""
        <div style="background:white; border-radius:16px; padding:1rem; 
                    border:2px solid #b8f0c8; text-align:center;
                    font-size:1.2rem; color:#2d6b4a; margin-bottom:0.5rem;">
            🐱 Terminé ! Voici vos résultats 🎉
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(1.0)

        # ─── DATAFRAME ───────────────────────────────────────────────────────
        df = pd.DataFrame(resultats)

        # Formatage montant
        if "montant_facture" in df.columns:
            df["montant_facture"] = pd.to_numeric(
                df["montant_facture"]
                .astype(str)
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

        # Filtrer colonnes actives
        df = df[[c for c in colonnes_actives if c in df.columns]]

        # ─── ÉDITEUR AVEC DATE MODIFIABLE ────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### 📊 Résultats — {mois_choisi} {annee_choisie}")

        mois_num = {
            "Janvier": "01", "Février": "02", "Mars": "03", "Avril": "04",
            "Mai": "05", "Juin": "06", "Juillet": "07", "Août": "08",
            "Septembre": "09", "Octobre": "10", "Novembre": "11", "Décembre": "12"
        }

        options_dates = [
            f"{m}/{annee_choisie:04d}" for m in [
                "01","02","03","04","05","06",
                "07","08","09","10","11","12"
            ]
        ]

        column_config = {}
        if "Date" in df.columns:
            column_config["Date"] = st.column_config.SelectboxColumn(
                "Date",
                options=options_dates,
                required=False,
                help="Modifiez le mois si besoin"
            )
        if "Statut" in df.columns:
            column_config["Statut"] = st.column_config.SelectboxColumn(
                "Statut",
                options=["À valider", "Validé ✅", "Envoyé 📤", "Refusé ❌"],
                required=False
            )

        colonnes_non_editables = [c for c in df.columns if c not in ["Date", "Statut"]]

        df_edit = st.data_editor(
            df,
            use_container_width=True,
            height=300,
            column_config=column_config,
            disabled=colonnes_non_editables
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ─── MÉTRIQUES ───────────────────────────────────────────────────────
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
            nb_valides = len(df_edit[df_edit.get("Statut", pd.Series()) == "Validé ✅"]) if "Statut" in df_edit.columns else 0
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;">✅</div>
                <div style="font-size:1.8rem; font-weight:700; color:#2d6b4a;">{nb_valides}</div>
                <div style="color:#9aa0c4;">Validées</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            nb_erreurs = len(df_edit[df_edit.get("Statut", pd.Series()).str.startswith("❌", na=False)]) if "Statut" in df_edit.columns else 0
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;">❌</div>
                <div style="font-size:1.8rem; font-weight:700; color:#c0392b;">{nb_erreurs}</div>
                <div style="color:#9aa0c4;">Erreurs</div>
            </div>
            """, unsafe_allow_html=True)

        # ─── EXPORT ──────────────────────────────────────────────────────────
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
