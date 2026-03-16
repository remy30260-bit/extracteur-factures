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

# ─── INITIALISATION PAGE ──────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "factures"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 70px !important;
        max-width: 70px !important;
    }
    [data-testid="stSidebar"] .stButton button {
        width: 45px;
        height: 45px;
        border-radius: 12px;
        font-size: 1.5rem;
        padding: 0;
        border: 2px solid transparent;
        background: transparent;
        transition: all 0.2s ease;
        margin: 3px auto;
        display: block;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #f5e6d8;
        border-color: #f0a070;
        transform: scale(1.1);
    }
    [data-testid="stSidebar"] p { display: none; }
    </style>
    """, unsafe_allow_html=True)

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

                # ── Vos métriques ici ──

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

                st.markdown("---")
                st.markdown(f"""
                <div style="text-align:center; padding: 1rem 0;">
                    <div class="cat-ascii">{ascii_to_html(CAT_ASCII_GRAND)}</div>
                    <p style="color:#a0522d; font-weight:700; margin-top:0.8rem;">Purrrfait travail ! 🐾</p>
                    <p style="color:#c8956c; font-size:0.85rem;">FactureCat — Votre comptable félin 🐱</p>
                </div>
                """, unsafe_allow_html=True)

    elif fichiers and not api_key:
        st.markdown("""
        <div class="cat-container">
            <div style="font-size:2.5rem;">🙀</div>
            <div class="chat-bubble">
                <span style="color:#a0522d; font-weight:700;">Miaou ! J'ai besoin de ta clé API... 🔑</span><br>
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

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "notes_frais":

    st.markdown("""
    <div style="text-align:center; padding: 1.5rem 0;">
        <div style="font-size:4rem;">💰</div>
        <h1 style="margin:0;">Notes de Frais</h1>
        <p style="color:#c8956c; margin:0.5rem 0 0 0; font-size:1.1rem;">
            Gérez vos dépenses professionnelles 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3.5rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Ajoutez une dépense 🐾</strong><br>
            <span style="color:#c8956c;">Remplissez le formulaire et joignez votre justificatif !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_note_frais", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            nf_date = st.date_input("📅 Date", value=datetime.now())
            nf_employe = st.text_input("👤 Employé / Nom")
            nf_categorie = st.selectbox("📂 Catégorie", [
                "Transport 🚗", "Repas 🍽️", "Hébergement 🏨",
                "Fournitures 📦", "Formation 🎓", "Client 🤝", "Autres"
            ])
            nf_description = st.text_area("📝 Description", height=80)

        with col2:
            nf_montant_ht = st.number_input("💶 Montant HT (€)", min_value=0.0, step=0.01, format="%.2f")
            nf_tva = st.selectbox("📊 TVA", ["20%", "10%", "5.5%", "0%"])

            tva_pct = float(nf_tva.replace("%", "")) / 100
            nf_montant_tva = round(nf_montant_ht * tva_pct, 2)
            nf_montant_ttc = round(nf_montant_ht + nf_montant_tva, 2)

            st.markdown(f"""
            <div class="card" style="padding:1rem; margin-top:0.5rem;">
                <p style="margin:0; color:#c8956c; font-size:0.85rem;">Calcul automatique :</p>
                <p style="margin:0.2rem 0; color:#a0522d;">TVA : <strong>{nf_montant_tva:.2f} €</strong></p>
                <p style="margin:0; color:#a0522d; font-size:1.1rem;">TTC : <strong>{nf_montant_ttc:.2f} €</strong></p>
            </div>
            """, unsafe_allow_html=True)

            nf_moyen_paiement = st.selectbox("💳 Moyen de paiement", [
                "Carte bancaire", "Espèces", "Virement", "Chèque"
            ])
            nf_justificatif = st.file_uploader("📎 Justificatif", type=["pdf", "jpg", "jpeg", "png"])

        submitted = st.form_submit_button("➕ Ajouter la dépense", use_container_width=True)

        if submitted:
            if not nf_employe:
                st.error("❌ Veuillez saisir un nom d'employé !")
            elif nf_montant_ht <= 0:
                st.error("❌ Le montant doit être supérieur à 0 !")
            else:
                nouvelle_note = {
                    "Date": nf_date.strftime("%d/%m/%Y"),
                    "Employé": nf_employe,
                    "Catégorie": nf_categorie,
                    "Description": nf_description,
                    "Montant HT (€)": nf_montant_ht,
                    "TVA": nf_tva,
                    "Montant TVA (€)": nf_montant_tva,
                    "Montant TTC (€)": nf_montant_ttc,
                    "Moyen de paiement": nf_moyen_paiement,
                    "Justificatif": nf_justificatif.name if nf_justificatif else "—",
                    "Statut": "En attente 😺"
                }
                st.session_state["notes_frais"].append(nouvelle_note)
                st.success("✅ Dépense ajoutée avec succès ! 🐾")
                st.rerun()

    if st.session_state["notes_frais"]:
        df_nf = pd.DataFrame(st.session_state["notes_frais"])
        st.dataframe(df_nf, use_container_width=True, hide_index=True)

        col_act1, col_act2, col_act3 = st.columns(3)

        with col_act1:
            buffer_nf = io.BytesIO()
            df_nf.to_excel(buffer_nf, index=False, engine="openpyxl")
            buffer_nf.seek(0)
            st.download_button(
                label="📥 Exporter Excel 🐾",
                data=buffer_nf,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_act2:
            csv_nf = df_nf.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Exporter CSV",
                data=csv_nf,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_act3:
            if st.button("🗑️ Effacer tout", use_container_width=True):
                st.session_state["notes_frais"] = []
                st.rerun()

    else:
        st.markdown(f"""
        <div style="text-align:center; padding: 3rem 0;">
            <div class="cat-ascii" style="font-size:1.2rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
            <p style="font-size:1.2rem; font-weight:700; color:#a0522d; margin-top:1rem;">
                Aucune note de frais pour l'instant !
            </p>
            <p style="color:#c8956c;">Ajoutez votre première dépense avec le formulaire ci-dessus 🐾</p>
        </div>
        """, unsafe_allow_html=True)
