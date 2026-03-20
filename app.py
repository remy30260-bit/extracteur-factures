import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime

st.set_page_config(page_title="FactureCat", page_icon="🐱", layout="wide", initial_sidebar_state="expanded")

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
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: #f5f6fa !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { max-width: 460px !important; margin: 0 auto !important; padding-top: 5rem !important; }
    .stButton > button {
        background: #1CC88A !important; color: white !important;
        border: none !important; border-radius: 6px !important;
        font-weight: 600 !important; height: 42px !important;
        font-size: 0.9rem !important;
    }
    .stButton > button:hover { background: #17a974 !important; }
    .stTextInput > div > div > input {
        border: 1.5px solid #e2e8f0 !important; border-radius: 6px !important;
        height: 42px !important; font-size: 0.9rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
        <div style="width:56px;height:56px;background:#1CC88A;border-radius:12px;
             display:inline-flex;align-items:center;justify-content:center;
             font-size:1.8rem;margin-bottom:1rem;">🐱</div>
        <h2 style="color:#1a1a2e;font-weight:700;margin:0;font-size:1.4rem;">FactureCat</h2>
        <p style="color:#718096;font-size:0.85rem;margin:0.3rem 0 0 0;">Connectez-vous pour continuer</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("", ["Se connecter", "Créer un compte"], horizontal=True, label_visibility="collapsed")
    email = st.text_input("Email", placeholder="votre@email.com")
    password = st.text_input("Mot de passe", type="password", placeholder="••••••••")

    if mode == "Créer un compte":
        password2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="••••••••")
        if st.button("Créer mon compte", use_container_width=True):
            if password != password2:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(password) < 6:
                st.error("Minimum 6 caractères.")
            else:
                try:
                    res = get_supabase().auth.sign_up({"email": email, "password": password})
                    if res.user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    else:
        if st.button("Se connecter", use_container_width=True):
            try:
                res = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.rerun()
            except Exception:
                st.error("Email ou mot de passe incorrect.")
    return False

if not check_password():
    st.stop()

# ─── STYLES PENNYLANE ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }

/* ── GLOBAL ── */
.stApp { background: #f5f6fa !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    width: 240px !important;
}
[data-testid="stSidebar"] * { color: #4a5568 !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── HEADER ── */
header[data-testid="stHeader"] { display: none !important; }

/* ── BOUTONS PRINCIPAUX ── */
.stButton > button {
    background: #1CC88A !important;
    color: white !important; border: none !important;
    border-radius: 6px !important; font-weight: 600 !important;
    font-size: 0.875rem !important; height: 38px !important;
    transition: background 0.2s !important;
    box-shadow: none !important;
}
.stButton > button:hover { background: #17a974 !important; transform: none !important; }

/* ── BOUTON DANGER ── */
.btn-danger > button {
    background: white !important; color: #e53e3e !important;
    border: 1.5px solid #e53e3e !important;
}
.btn-danger > button:hover { background: #fff5f5 !important; }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: white !important; color: #1CC88A !important;
    border: 1.5px solid #1CC88A !important;
    border-radius: 6px !important; font-weight: 600 !important;
    font-size: 0.875rem !important; height: 38px !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover { background: #f0fdf9 !important; transform: none !important; }

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 6px !important;
    font-size: 0.875rem !important;
    background: white !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #1CC88A !important;
    box-shadow: 0 0 0 3px rgba(28,200,138,0.1) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: white !important; border-radius: 8px !important;
    border: 2px dashed #e2e8f0 !important; padding: 0.5rem !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e2e8f0 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem !important; font-weight: 500 !important;
    color: #718096 !important; padding: 0.6rem 1.2rem !important;
    border: none !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #1CC88A !important; border-bottom: 2px solid #1CC88A !important;
    font-weight: 600 !important;
}

/* ── DATA EDITOR / TABLE ── */
[data-testid="stDataFrame"], .stDataEditor {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: #1CC88A !important; border-radius: 4px !important;
}

/* ── ALERTS ── */
.stSuccess { border-left: 4px solid #1CC88A !important; }
.stError { border-left: 4px solid #e53e3e !important; }
.stWarning { border-left: 4px solid #f6ad55 !important; }

/* ── KPI CARD ── */
.kpi-card {
    background: white; border-radius: 8px;
    border: 1px solid #e2e8f0; padding: 1.25rem 1.5rem;
    margin-bottom: 0;
}
.kpi-label { font-size: 0.75rem; font-weight: 600; color: #718096;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.kpi-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
.kpi-sub { font-size: 0.78rem; color: #a0aec0; margin-top: 0.3rem; }

/* ── BADGE ── */
.badge {
    display: inline-flex; align-items: center;
    padding: 0.2rem 0.65rem; border-radius: 4px;
    font-size: 0.72rem; font-weight: 600;
}
.badge-green  { background: #f0fdf9; color: #1CC88A; border: 1px solid #bbf7e0; }
.badge-orange { background: #fffaf0; color: #dd6b20; border: 1px solid #fbd38d; }
.badge-red    { background: #fff5f5; color: #e53e3e; border: 1px solid #fed7d7; }
.badge-gray   { background: #f7fafc; color: #718096; border: 1px solid #e2e8f0; }

/* ── SECTION HEADER ── */
.section-header {
    font-size: 0.7rem; font-weight: 700; color: #a0aec0;
    text-transform: uppercase; letter-spacing: 0.08em;
    padding: 1rem 0 0.5rem 0.75rem; margin: 0;
}

/* ── PANEL ── */
.panel {
    background: white; border-radius: 8px;
    border: 1px solid #e2e8f0; overflow: hidden;
    margin-bottom: 1.5rem;
}
.panel-header {
    padding: 1rem 1.25rem; border-bottom: 1px solid #f7fafc;
    display: flex; align-items: center; justify-content: space-between;
}
.panel-title { font-size: 0.875rem; font-weight: 600; color: #2d3748; }
.panel-body { padding: 1.25rem; }

/* ── PAGE TITLE ── */
.page-title {
    font-size: 1.25rem; font-weight: 700; color: #1a1a2e; margin: 0 0 0.25rem 0;
}
.page-subtitle { font-size: 0.85rem; color: #718096; margin: 0 0 1.5rem 0; }

/* ── INVOICE TABLE ── */
.inv-table { width:100%; border-collapse:collapse; font-size:0.83rem; }
.inv-table th {
    padding: 0.65rem 1rem; text-align:left; color:#a0aec0;
    font-size: 0.72rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.05em; border-bottom: 1px solid #edf2f7; background:#fafafa;
}
.inv-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #f7fafc; color:#4a5568; }
.inv-table tr:last-child td { border-bottom: none; }
.inv-table tr:hover td { background: #fafffe; }

/* ── RADIO SIDEBAR ── */
div[data-testid="stRadio"] label {
    display: flex !important; align-items: center !important;
    padding: 0.5rem 0.75rem !important; border-radius: 6px !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    cursor: pointer !important; transition: background 0.15s !important;
    color: #4a5568 !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #f0fdf9 !important; color: #1CC88A !important;
    font-weight: 600 !important;
}
div[data-testid="stRadio"] > div { gap: 0.15rem !important; }
div[data-testid="stRadio"] input[type="radio"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
now = datetime.now()

def badge_html(statut: str) -> str:
    m = {
        "Validé 😸": "badge-green", "Validé": "badge-green",
        "En attente 😺": "badge-orange", "En attente": "badge-orange",
        "À vérifier 🐱": "badge-orange", "À vérifier": "badge-orange",
        "Erreur 🙀": "badge-red", "Refusé 🙀": "badge-red",
    }
    return f'<span class="badge {m.get(statut, "badge-gray")}">{statut}</span>'

def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def extraire_facture(fichier, model, mois, annee):
    fichier.seek(0)
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
  "montant_ht": "montant HT (nombre, ex: 100.00)",
  "tva": "montant TVA (nombre)",
  "montant_ttc": "montant TTC (nombre)",
  "description": "courte description",
  "categorie": "Transport/Repas/Hébergement/Fournitures/Services/Autres"
}}"""
    response = model.generate_content([prompt, image])
    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return json.loads(text.strip())

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding: 1.25rem 0.75rem 0.5rem 0.75rem; display:flex; align-items:center; gap:0.6rem;">
        <div style="width:32px;height:32px;background:#1CC88A;border-radius:8px;
             display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🐱</div>
        <span style="font-size:1rem;font-weight:700;color:#1a1a2e !important;">FactureCat</span>
    </div>
    <div style="height:1px;background:#e2e8f0;margin:0.5rem 0.75rem 0.25rem 0.75rem;"></div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown('<p class="section-header">Menu</p>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["📄 Factures", "💰 Notes de frais"],
        label_visibility="collapsed"
    )

    st.markdown('<div style="height:1px;background:#e2e8f0;margin:0.75rem;"></div>', unsafe_allow_html=True)

    # Guide contextuel
    st.markdown('<p class="section-header">Guide rapide</p>', unsafe_allow_html=True)
    if page == "📄 Factures":
        steps = ["Uploadez vos factures", "Lancez l'extraction IA", "Vérifiez les données", "Exportez en Excel"]
    else:
        steps = ["Ajoutez une dépense", "Joignez le justificatif", "Vérifiez les données", "Exportez en Excel"]
    for i, s in enumerate(steps, 1):
        st.markdown(f'<p style="font-size:0.8rem;color:#718096;padding:0.2rem 0.75rem;margin:0;">{i}. {s}</p>', unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:#e2e8f0;margin:0.75rem;"></div>', unsafe_allow_html=True)

    # Utilisateur connecté
    email_display = st.session_state.get("user_email", "")
    st.markdown(f"""
    <div style="padding:0.75rem;margin:0 0 0.5rem 0;">
        <p style="font-size:0.72rem;color:#a0aec0;margin:0 0 0.2rem 0;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Compte</p>
        <p style="font-size:0.8rem;color:#4a5568;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email_display}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        if st.button("Déconnexion", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
if page == "📄 Factures":
    api_key = st.secrets["GEMINI_API_KEY"]

    st.markdown('<h1 class="page-title">Factures</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Import, extraction IA et suivi de vos factures fournisseurs</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Import & Extraction", "Visualisation"])

    with tab1:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        # Zone upload
        fichiers = st.file_uploader(
            "Glissez vos factures ici — PDF, JPG, PNG acceptés",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Formats acceptés : PDF, JPG, PNG"
        )

        if fichiers:
            st.markdown(f"""
            <div style="background:#f0fdf9;border:1px solid #bbf7e0;border-radius:6px;
                 padding:0.7rem 1rem;margin:0.75rem 0;font-size:0.85rem;color:#276749;">
                ✓ <strong>{len(fichiers)}</strong> fichier(s) chargé(s) et prêt(s) à l'analyse
            </div>
            """, unsafe_allow_html=True)

            noms_actuels = sorted([f.name for f in fichiers])
            noms_precedents = sorted(st.session_state.get("fichiers_extraits", []))
            fichiers_ont_change = noms_actuels != noms_precedents

            if fichiers_ont_change and "resultats" in st.session_state:
                st.warning("Nouveaux fichiers détectés — relancez l'extraction pour les inclure.")

            col_b1, col_b2, col_b3 = st.columns([1, 1.5, 1])
            with col_b2:
                lancer = st.button("Lancer l'extraction IA", type="primary", use_container_width=True)

            doit_extraire = lancer and ("resultats" not in st.session_state or fichiers_ont_change)

            if doit_extraire:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                progress = st.progress(0)
                resultats = []
                for i, fichier in enumerate(fichiers):
                    fichier.seek(0)
                    with st.spinner(f"Analyse de {fichier.name}…"):
                        try:
                            data = extraire_facture(fichier, model, mois_list[now.month-1], now.year)
                            data["fichier"] = fichier.name
                            data["statut"] = "Validé 😸"
                            resultats.append(data)
                        except Exception as e:
                            resultats.append({
                                "fichier": fichier.name, "date": "", "fournisseur": "",
                                "numero_facture": "", "montant_ht": "", "tva": "",
                                "montant_ttc": "", "description": str(e),
                                "categorie": "", "statut": "Erreur 🙀"
                            })
                    progress.progress(int((i + 1) / len(fichiers) * 100))
                progress.empty()
                st.session_state["resultats"] = resultats
                st.session_state["fichiers_extraits"] = noms_actuels
                st.rerun()

            if "resultats" in st.session_state and not fichiers_ont_change:
                resultats = st.session_state["resultats"]
                mois_choisi = mois_list[now.month - 1]
                annee_choisie = now.year

                st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
                st.success(f"✓ {len(resultats)} facture(s) analysée(s) avec succès")

                # KPIs
                col1, col2, col3, col4 = st.columns(4)
                try:
                    vals = [float(str(r.get("montant_ttc","0")).replace(",",".") or 0) for r in resultats]
                    total = sum(vals)
                    total_str = f"{total:,.2f} €"
                except:
                    total_str = "—"
                nb_ok  = sum(1 for r in resultats if r.get("statut") == "Validé 😸")
                nb_err = sum(1 for r in resultats if r.get("statut") == "Erreur 🙀")

                for col, icon, label, val, sub in [
                    (col1, "🧾", "FACTURES",   str(len(resultats)), "fichiers traités"),
                    (col2, "✓",  "VALIDÉES",    str(nb_ok),          "sans erreur"),
                    (col3, "⚠", "ERREURS",     str(nb_err),         "à vérifier"),
                    (col4, "€",  "TOTAL TTC",   total_str,           "toutes factures"),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value">{val}</div>
                            <div class="kpi-sub">{sub}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown('<div style="height:1.25rem"></div>', unsafe_allow_html=True)

                # Tableau éditable
                df = pd.DataFrame(resultats).rename(columns={
                    "fichier":"Fichier","date":"Date","fournisseur":"Fournisseur",
                    "numero_facture":"N° Facture","montant_ht":"Montant HT (€)",
                    "tva":"TVA (€)","montant_ttc":"Montant TTC (€)",
                    "description":"Description","categorie":"Catégorie","statut":"Statut"
                })
                col_p1, col_p2 = st.columns([1,1])
                with col_p1:
                    mois_rapide = st.selectbox("Mois", mois_list, index=now.month-1)
                with col_p2:
                    annee_rapide = st.selectbox("Année", list(range(2023, 2031)), index=list(range(2023,2031)).index(now.year))
                df["Mois"] = mois_rapide
                df["Année"] = annee_rapide
                cols_ordre = ["Fichier","Date","Mois","Année","Fournisseur","N° Facture",
                              "Montant HT (€)","TVA (€)","Montant TTC (€)","Catégorie","Description","Statut"]
                df = df[[c for c in cols_ordre if c in df.columns]]

                df_edit = st.data_editor(
                    df, use_container_width=True, hide_index=True,
                    column_config={
                        "Statut": st.column_config.SelectboxColumn("Statut",
                            options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]),
                        "Catégorie": st.column_config.SelectboxColumn("Catégorie",
                            options=["Transport","Repas","Hébergement","Fournitures","Services","Autres"])
                    }
                )

                st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
                col_dl1, col_dl2, _ = st.columns([1, 1, 2])
                buf = io.BytesIO()
                df_edit.to_excel(buf, index=False, engine="openpyxl"); buf.seek(0)
                with col_dl1:
                    st.download_button("Exporter Excel", data=buf,
                        file_name=f"factures_{mois_rapide}_{annee_rapide}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
                with col_dl2:
                    st.download_button("Exporter CSV", data=df_edit.to_csv(index=False).encode(),
                        file_name=f"factures_{mois_rapide}_{annee_rapide}.csv",
                        mime="text/csv", use_container_width=True)
        else:
            st.markdown("""
            <div style="background:white;border:2px dashed #e2e8f0;border-radius:8px;
                 padding:3rem 2rem;text-align:center;margin-top:1rem;">
                <div style="font-size:2rem;margin-bottom:0.75rem;color:#a0aec0;">📄</div>
                <p style="font-weight:600;color:#4a5568;margin:0;font-size:0.9rem;">
                    Aucun fichier sélectionné
                </p>
                <p style="color:#a0aec0;font-size:0.82rem;margin:0.4rem 0 0 0;">
                    Utilisez le sélecteur ci-dessus pour importer vos factures
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        if "resultats" in st.session_state and fichiers:
            st.markdown('<p style="font-size:0.875rem;font-weight:600;color:#2d3748;margin-bottom:0.75rem;">Aperçu des fichiers</p>', unsafe_allow_html=True)
            for idx, fichier in enumerate(fichiers):
                with st.expander(fichier.name, expanded=(idx == 0)):
                    fichier.seek(0)
                    if fichier.type == "application/pdf":
                        imgs = pdf_to_images(fichier.read())
                        st.image(imgs[0], use_container_width=True)
                        if len(imgs) > 1:
                            st.caption(f"{len(imgs)} pages")
                    else:
                        st.image(Image.open(fichier), use_container_width=True)
        else:
            st.info("Importez et analysez des factures d'abord (onglet Import & Extraction).")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    st.markdown('<h1 class="page-title">Notes de frais</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Saisissez et gérez vos dépenses professionnelles</p>', unsafe_allow_html=True)

    tab_add, tab_list = st.tabs(["Nouvelle dépense", "Toutes les dépenses"])

    with tab_add:
        st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
        with st.form("form_note_frais", clear_on_submit=True):
            st.markdown('<p style="font-size:0.875rem;font-weight:600;color:#2d3748;margin-bottom:1rem;">Informations de la dépense</p>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                nf_date       = st.date_input("Date", value=datetime.now())
                nf_employe    = st.text_input("Employé", placeholder="Prénom Nom")
                nf_categorie  = st.selectbox("Catégorie", [
                    "Transport 🚗","Repas 🍽️","Hébergement 🏨",
                    "Fournitures 📦","Formation 🎓","Client 🤝","Autres"])
                nf_description = st.text_area("Description", height=90, placeholder="Objet de la dépense…")
            with col2:
                nf_montant_ht = st.number_input("Montant HT (€)", min_value=0.0, step=0.01, format="%.2f")
                nf_tva_pct    = st.selectbox("Taux de TVA", ["20%","10%","5.5%","0%"])
                tva_val       = float(nf_tva_pct.replace("%","")) / 100
                tva_montant   = round(nf_montant_ht * tva_val, 2)
                ttc           = round(nf_montant_ht + tva_montant, 2)
                st.markdown(f"""
                <div style="background:#f0fdf9;border:1px solid #bbf7e0;border-radius:6px;
                     padding:0.9rem 1rem;margin:0.5rem 0 1rem 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.8rem;color:#718096;">TVA ({nf_tva_pct})</span>
                        <span style="font-size:0.875rem;font-weight:600;color:#2d3748;">{tva_montant:.2f} €</span>
                    </div>
                    <div style="height:1px;background:#d1fae5;margin:0.5rem 0;"></div>
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.85rem;font-weight:600;color:#1a1a2e;">Total TTC</span>
                        <span style="font-size:1rem;font-weight:700;color:#1CC88A;">{ttc:.2f} €</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                nf_paiement     = st.selectbox("Moyen de paiement", [
                    "Carte entreprise","Espèces","Carte personnelle","Virement"])
                nf_justificatif = st.file_uploader("Justificatif (optionnel)",
                    type=["pdf","jpg","jpeg","png"], key="just_upload")

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            col_s1, col_s2, col_s3 = st.columns([1,1,1])
            with col_s2:
                submitted = st.form_submit_button("Ajouter la dépense", use_container_width=True, type="primary")

            if submitted:
                if not nf_employe:
                    st.error("Veuillez saisir un nom d'employé.")
                elif nf_montant_ht <= 0:
                    st.error("Le montant doit être supérieur à 0.")
                else:
                    st.session_state["notes_frais"].append({
                        "Date": nf_date.strftime("%d/%m/%Y"), "Employé": nf_employe,
                        "Catégorie": nf_categorie, "Description": nf_description,
                        "Montant HT (€)": nf_montant_ht, "TVA": nf_tva_pct,
                        "Montant TVA (€)": tva_montant, "Montant TTC (€)": ttc,
                        "Moyen de paiement": nf_paiement,
                        "Justificatif": nf_justificatif.name if nf_justificatif else "—",
                        "Statut": "En attente 😺"
                    })
                    st.success("Dépense ajoutée avec succès.")
                    st.rerun()

    with tab_list:
        st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])

            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            nb_val = len(df_nf[df_nf["Statut"]=="Validé 😸"])
            nb_att = len(df_nf[df_nf["Statut"]=="En attente 😺"])
            total_ttc = df_nf["Montant TTC (€)"].sum()
            for col, icon, label, val, sub in [
                (col1, "📝", "DÉPENSES",    str(len(df_nf)),   "total saisies"),
                (col2, "✓",  "VALIDÉES",    str(nb_val),        "approuvées"),
                (col3, "⏳", "EN ATTENTE",  str(nb_att),        "à traiter"),
                (col4, "€",  "TOTAL TTC",   f"{total_ttc:,.2f} €", "toutes dépenses"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{val}</div>
                        <div class="kpi-sub">{sub}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

            # Filtres
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtre_emp = st.text_input("Rechercher un employé", "")
            with col_f2:
                filtre_cat = st.selectbox("Catégorie", ["Toutes"] + list(df_nf["Catégorie"].unique()))
            with col_f3:
                filtre_sta = st.selectbox("Statut", ["Tous","En attente 😺","Validé 😸","Refusé 🙀"])

            df_f = df_nf.copy()
            if filtre_emp: df_f = df_f[df_f["Employé"].str.contains(filtre_emp, case=False)]
            if filtre_cat != "Toutes": df_f = df_f[df_f["Catégorie"] == filtre_cat]
            if filtre_sta != "Tous": df_f = df_f[df_f["Statut"] == filtre_sta]

            df_nf_edit = st.data_editor(
                df_f, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn("Statut",
                        options=["En attente 😺","Validé 😸","Refusé 🙀","À vérifier 🐱"]),
                    "Catégorie": st.column_config.SelectboxColumn("Catégorie",
                        options=["Transport 🚗","Repas 🍽️","Hébergement 🏨",
                                 "Fournitures 📦","Formation 🎓","Client 🤝","Autres"]),
                    "Montant HT (€)":  st.column_config.NumberColumn(format="%.2f €"),
                    "Montant TVA (€)": st.column_config.NumberColumn(format="%.2f €"),
                    "Montant TTC (€)": st.column_config.NumberColumn(format="%.2f €"),
                }
            )

            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            col_a1, col_a2, col_a3, _ = st.columns([1,1,1,1])
            buf_nf = io.BytesIO()
            df_nf.to_excel(buf_nf, index=False, engine="openpyxl"); buf_nf.seek(0)
            with col_a1:
                st.download_button("Exporter Excel", data=buf_nf,
                    file_name=f"notes_frais_{now.strftime('%Y%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with col_a2:
                st.download_button("Exporter CSV", data=df_nf.to_csv(index=False).encode(),
                    file_name=f"notes_frais_{now.strftime('%Y%m')}.csv",
                    mime="text/csv", use_container_width=True)
            with col_a3:
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                if st.button("Tout supprimer", use_container_width=True):
                    st.session_state["notes_frais"] = []
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:8px;
                 padding:3rem 2rem;text-align:center;margin-top:0.5rem;">
                <div style="font-size:2rem;color:#a0aec0;margin-bottom:0.75rem;">📋</div>
                <p style="font-weight:600;color:#4a5568;margin:0;font-size:0.9rem;">Aucune note de frais</p>
                <p style="color:#a0aec0;font-size:0.82rem;margin:0.4rem 0 0 0;">
                    Ajoutez votre première dépense via l'onglet "Nouvelle dépense"
                </p>
            </div>
            """, unsafe_allow_html=True)
