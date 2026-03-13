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
    st.markdown("### 📅 Période par défaut")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    mois_choisi = st.selectbox("Mois", mois_list, index=0)
    annee_choisie = st.selectbox("Année", list(range(2023, 2031)), index=2)
    st.markdown("---")
    st.markdown("### 📖 Guide")
    st.markdown("""
    1. Entrez votre clé API
    2. Choisissez la période par défaut
    3. Uploadez vos factures
    4. Cliquez sur Extraire
    5. Modifiez si besoin
    6. Exportez en Excel
    """)
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:1rem;">
        <div style="font-size:3rem;">🐱</div>
        <div style="color:#9aa0c4; font-size:0.8rem;">Votre assistant comptable</div>
    </div>
    """, unsafe_allow_html=True)

# ─── TITRE ───────────────────────────────────────────────────────────────────
st.markdown("<h1>🧾 Extracteur de Factures</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9aa0c4;'>Uploadez vos factures PDF ou images — l'IA extrait tout automatiquement</p>", unsafe_allow_html=True)

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
fichiers = st.file_uploader(
    "📂 Déposez vos factures ici",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

# ─── EXTRACTION ──────────────────────────────────────────────────────────────
if fichiers and api_key:
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        lancer = st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True)

    if lancer:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        resultats = []
        progress = st.progress(0)
        status = st.empty()

        for i, fichier in enumerate(fichiers):
            status.markdown(f"⏳ Traitement : **{fichier.name}** ({i+1}/{len(fichiers)})")
            try:
                if fichier.type == "application/pdf":
                    pdf = fitz.open(stream=fichier.read(), filetype="pdf")
                    page = pdf[0]
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))
                else:
                    image = Image.open(fichier)

                prompt = """Tu es un expert comptable. Analyse cette facture et extrais UNIQUEMENT les informations du FOURNISSEUR (celui qui émet la facture, qui vend le service/produit).

RÈGLES IMPORTANTES :
- Le FOURNISSEUR est l'entreprise qui a émis la facture (son nom/logo est généralement en haut, ses coordonnées bancaires sont présentes, c'est lui qui demande le paiement)
- Le CLIENT est celui qui reçoit la facture et doit payer (à NE PAS mettre dans fournisseur_client)
- Si tu vois "ANTARES", "MIEUXASSURER" ou toute autre société en tant qu'émetteur = c'est le fournisseur
- Le numéro de facture commence souvent par des lettres + chiffres (ex: ANTIT25020037)

Retourne UNIQUEMENT ce JSON (sans markdown, sans ```):
{
  "fournisseur_client": "nom du FOURNISSEUR uniquement",
  "numero_facture": "numéro de la facture",
  "type": "FACTURE ou AVOIR",
  "montant_facture": "montant TTC avec devise",
  "date_facture": "date au format JJ/MM/AAAA",
  "statut": "À valider"
}"""

                response = model.generate_content([prompt, image])
                texte = response.text.strip()

                if "```" in texte:
                    texte = texte.split("```")[1]
                    if texte.startswith("json"):
                        texte = texte[4:]
                texte = texte.strip()

                data = json.loads(texte)
                data["fichier"] = fichier.name
                resultats.append(data)

            except Exception as e:
                resultats.append({
                    "fichier": fichier.name,
                    "fournisseur_client": "Erreur",
                    "numero_facture": "",
                    "type": "",
                    "montant_facture": "",
                    "date_facture": "",
                    "statut": f"❌ {str(e)[:50]}"
                })

            progress.progress((i + 1) / len(fichiers))

        status.success(f"✅ {len(fichiers)} facture(s) traitée(s) !")

        # Construire le DataFrame et le sauvegarder en session_state
        df = pd.DataFrame(resultats)
        col_order = ["fichier", "fournisseur_client", "numero_facture",
                     "type", "montant_facture", "date_facture", "statut"]
        for col in col_order:
            if col not in df.columns:
                df[col] = ""
        df = df[col_order]
        df.columns = ["Fichier", "Fournisseur", "N° Facture",
                      "Type", "Montant TTC", "Date", "Statut"]
        df["Date"] = f"{mois_choisi} {annee_choisie}"

        # ✅ Sauvegarde dans session_state
        st.session_state["df_factures"] = df

# ─── TABLEAU (affiché depuis session_state — résiste aux re-runs) ─────────────
if "df_factures" in st.session_state:
    df = st.session_state["df_factures"].copy()

    st.markdown("### 📊 Résultats — vous pouvez modifier les cellules avant export")

    # Sélecteur de période rapide AU-DESSUS du tableau
    st.markdown("#### 📅 Changer la période pour toutes les lignes")
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        mois_rapide = st.selectbox(
            "Mois",
            mois_list,
            index=mois_list.index(mois_choisi),
            key="mois_rapide"
        )
    with col_p2:
        annee_rapide = st.selectbox(
            "Année",
            list(range(2023, 2031)),
            index=list(range(2023, 2031)).index(annee_choisie),
            key="annee_rapide"
        )

    # Mettre à jour toutes les lignes avec la période choisie
    df["Date"] = f"{mois_rapide} {annee_rapide}"
    st.session_state["df_factures"]["Date"] = df["Date"]

    options_periode = [f"{m} {a}" for a in range(2023, 2031) for m in mois_list]

    df_edit = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fichier": st.column_config.TextColumn("Fichier", disabled=True),
            "Fournisseur": st.column_config.TextColumn("Fournisseur"),
            "N° Facture": st.column_config.TextColumn("N° Facture"),
            "Type": st.column_config.SelectboxColumn(
                "Type",
                options=["FACTURE", "AVOIR"]
            ),
            "Montant TTC": st.column_config.TextColumn("Montant TTC"),
            "Date": st.column_config.SelectboxColumn(
                "📅 Période",
                options=options_periode,
                required=True
            ),
            "Statut": st.column_config.SelectboxColumn(
                "Statut",
                options=["À valider", "Validé ✅", "❌ Erreur", "En attente ⏳"]
            )
        }
    )

    # ─── STATISTIQUES ────────────────────────────────────────────────────────
    st.markdown("### 📈 Statistiques")
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

    # ─── EXPORT EXCEL ────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    df_edit.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    col_dl = st.columns([1, 2, 1])
    with col_dl[1]:
        st.download_button(
            label="📥 Télécharger Excel",
            data=buffer,
            file_name=f"factures_{mois_rapide}_{annee_rapide}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

elif not fichiers:
    st.markdown("""
    <div style="text-align:center; padding:2rem; color:#9aa0c4;">
        <div style="font-size:3rem;">☝️</div>
        <p style="font-size:1.1rem;">Uploadez vos factures ci-dessus pour commencer</p>
    </div>
    """, unsafe_allow_html=True)

elif fichiers and not api_key:
    st.warning("⚠️ Entrez votre clé API Gemini dans le menu à gauche pour démarrer")
