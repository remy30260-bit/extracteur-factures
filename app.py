import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime, date
import calendar

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide", initial_sidebar_state="expanded")

# ─── SUPABASE ─────────────────────────────────────────────────────────────────
from supabase import create_client
def get_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
    * { font-family: 'Nunito', sans-serif; }
    .stApp { background: #fdf6f0 !important; }
    [data-testid="stSidebar"] { display:none !important; }
    header { display:none !important; }
    .block-container { max-width:440px !important; margin:0 auto !important; padding-top:4rem !important; }
    .stButton > button {
        background: linear-gradient(135deg,#f0a070,#e8856a) !important;
        color:white !important; border:none !important; border-radius:20px !important;
        font-weight:700 !important; height:44px !important;
    }
    .stTextInput > div > div > input {
        border:2px solid #f5e6d8 !important; border-radius:12px !important; background:white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <div style="font-size:4rem;">🐱</div>
        <h2 style="color:#a0522d;font-weight:800;margin:0;">FactureCat</h2>
        <p style="color:#c8956c;">Votre assistant comptable félin 🐾</p>
    </div>
    """, unsafe_allow_html=True)
    mode = st.radio("", ["🔑 Se connecter","✨ Créer un compte"], horizontal=True, label_visibility="collapsed")
    email    = st.text_input("📧 Email")
    password = st.text_input("🔑 Mot de passe", type="password")
    if mode == "✨ Créer un compte":
        pw2 = st.text_input("🔑 Confirmer", type="password")
        if st.button("🐾 Créer mon compte", use_container_width=True):
            if password != pw2: st.error("Mots de passe différents !")
            elif len(password) < 6: st.error("Minimum 6 caractères !")
            else:
                try:
                    res = get_supabase().auth.sign_up({"email":email,"password":password})
                    if res.user:
                        st.session_state.update({"authenticated":True,"user_email":email})
                        st.rerun()
                except Exception as e: st.error(f"Erreur : {e}")
    else:
        if st.button("🐾 Se connecter", use_container_width=True):
            try:
                res = get_supabase().auth.sign_in_with_password({"email":email,"password":password})
                if res.user:
                    st.session_state.update({"authenticated":True,"user_email":email})
                    st.rerun()
            except: st.error("Email ou mot de passe incorrect 🙀")
    return False

if not check_password():
    st.stop()

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
* { font-family: 'Nunito', sans-serif; }
.stApp { background: #fdf6f0 !important; }
header[data-testid="stHeader"] { display:none !important; }

[data-testid="stSidebar"] {
    background: #fff8f3 !important;
    border-right: 2px solid #f0d5c0 !important;
}

/* Boutons principaux */
.stButton > button {
    background: linear-gradient(135deg,#f0a070,#e8856a) !important;
    color:white !important; border:none !important; border-radius:20px !important;
    padding:0.5rem 1.5rem !important; font-weight:700 !important; font-size:0.9rem !important;
    box-shadow:0 4px 15px rgba(200,149,108,0.35) !important; transition:all 0.2s !important;
}
.stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 6px 20px rgba(200,149,108,0.5) !important; }

/* Bouton danger */
.btn-danger .stButton > button {
    background:white !important; color:#e53e3e !important;
    border:2px solid #e53e3e !important; box-shadow:none !important;
}
.btn-danger .stButton > button:hover { background:#fff5f5 !important; }

/* Bouton secondaire */
.btn-secondary .stButton > button {
    background:white !important; color:#a0522d !important;
    border:2px solid #f0a070 !important; box-shadow:none !important;
}

/* Download */
.stDownloadButton > button {
    background:linear-gradient(135deg,#a8d8a8,#7fc87f) !important;
    color:#2d5a2d !important; border:none !important; border-radius:20px !important;
    font-weight:700 !important; box-shadow:0 4px 15px rgba(127,200,127,0.35) !important;
}
.stDownloadButton > button:hover { transform:translateY(-2px) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    border:2px solid #f5e6d8 !important; border-radius:12px !important; background:white !important;
}
.stSelectbox > div > div { border:2px solid #f5e6d8 !important; border-radius:12px !important; background:white !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:transparent !important; border-bottom:2px solid #f0d5c0 !important; }
.stTabs [data-baseweb="tab"] { font-weight:700 !important; color:#c8956c !important; }
.stTabs [aria-selected="true"] { color:#a0522d !important; border-bottom:3px solid #f0a070 !important; }

/* File uploader */
[data-testid="stFileUploader"] { background:white !important; border-radius:16px !important; border:2px dashed #f0a070 !important; }

/* Progress */
.stProgress > div > div { background:linear-gradient(90deg,#f0a070,#e8856a) !important; border-radius:10px !important; }

/* DataEditor */
[data-testid="stDataFrame"],.stDataEditor { border-radius:16px !important; border:2px solid #f5e6d8 !important; overflow:hidden !important; }

/* Radio nav sidebar */
div[data-testid="stRadio"] label {
    padding:0.5rem 0.75rem !important; border-radius:10px !important;
    font-weight:600 !important; font-size:0.875rem !important; transition:background 0.15s !important;
}
div[data-testid="stRadio"] label:has(input:checked) { background:#fff0e8 !important; color:#a0522d !important; }
div[data-testid="stRadio"] input[type="radio"] { display:none !important; }
div[data-testid="stRadio"] > div { gap:0.2rem !important; }

/* Cards */
.card {
    background:white; border-radius:16px; padding:1.25rem 1.5rem;
    border:2px solid #f5e6d8; margin-bottom:1rem;
    box-shadow:0 2px 12px rgba(200,149,108,0.1);
}
.card-green {
    background:white; border-radius:16px; padding:1.25rem 1.5rem;
    border:2px solid #d5f0d5; margin-bottom:1rem;
    box-shadow:0 2px 12px rgba(127,200,127,0.1);
}
.card-blue {
    background:white; border-radius:16px; padding:1.25rem 1.5rem;
    border:2px solid #bee3f8; margin-bottom:1rem;
}

/* KPI */
.kpi-card { background:white; border-radius:16px; padding:1.25rem 1.5rem; border:2px solid #f5e6d8; text-align:center; }
.kpi-icon { font-size:2rem; margin-bottom:0.5rem; }
.kpi-val  { font-size:1.8rem; font-weight:800; color:#a0522d; line-height:1; }
.kpi-lbl  { font-size:0.8rem; color:#c8956c; margin-top:0.3rem; }

/* Badge */
.badge { display:inline-flex; align-items:center; padding:0.25rem 0.75rem; border-radius:20px; font-size:0.75rem; font-weight:700; }
.badge-green  { background:#d4edda; color:#155724; }
.badge-orange { background:#fff3cd; color:#856404; }
.badge-red    { background:#f8d7da; color:#721c24; }
.badge-blue   { background:#cce5ff; color:#004085; }
.badge-gray   { background:#e2e8f0; color:#4a5568; }

/* Chat bubble */
.chat-bubble {
    background:white; border-radius:20px 20px 20px 4px;
    padding:1rem 1.5rem; border:2px solid #f5e6d8;
    box-shadow:0 4px 15px rgba(200,149,108,0.15); display:inline-block; margin-left:1rem;
}
.cat-container { display:flex; align-items:center; margin:1rem 0; }

/* Stat row (comptabilité) */
.stat-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:0.6rem 0; border-bottom:1px solid #fdf0e8;
}
.stat-row:last-child { border-bottom:none; }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
now = datetime.now()
CAT_ICONS = {"Transport":"🚗","Repas":"🍽️","Hébergement":"🏨","Fournitures":"📦",
             "Formation":"🎓","Client":"🤝","Services":"💼","Autres":"📎"}

def badge_html(statut):
    m = {"Validé 😸":"badge-green","Validé":"badge-green","Payée":"badge-green","Remboursée":"badge-green",
         "En attente 😺":"badge-orange","En attente":"badge-orange","À vérifier 🐱":"badge-orange",
         "Erreur 🙀":"badge-red","Refusé 🙀":"badge-red","À payer":"badge-orange",
         "En retard":"badge-red","Brouillon":"badge-gray"}
    return f'<span class="badge {m.get(statut,"badge-gray")}">{statut}</span>'

def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [Image.frombytes("RGB",[p.get_pixmap(matrix=fitz.Matrix(2,2)).width,
            p.get_pixmap(matrix=fitz.Matrix(2,2)).height],
            p.get_pixmap(matrix=fitz.Matrix(2,2)).samples) for p in doc]

def extraire_facture(fichier, model, mois, annee):
    fichier.seek(0)
    image = pdf_to_images(fichier.read())[0] if fichier.type=="application/pdf" else Image.open(fichier)
    prompt = f"""Analyse cette facture. Période : {mois} {annee}.
Retourne UNIQUEMENT ce JSON brut :
{{"date":"JJ/MM/AAAA","fournisseur":"nom","numero_facture":"num",
  "montant_ht":"100.00","tva":"20.00","montant_ttc":"120.00",
  "description":"description","categorie":"Transport/Repas/Hébergement/Fournitures/Services/Client/Autres"}}"""
    text = model.generate_content([prompt, image]).text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return json.loads(text.strip())

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {"notes_frais":[],"resultats":[],"fichiers_extraits":[],
             "clients":[],"devis":[],"factures_vente":[]}.items():
    if k not in st.session_state: st.session_state[k] = v

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.25rem 0 0.5rem 0;">
        <div style="font-size:3rem;">🐱</div>
        <h2 style="color:#a0522d;margin:0;font-size:1.2rem;">FactureCat</h2>
        <p style="color:#c8956c;font-size:0.78rem;margin:0.2rem 0 0 0;">Assistant comptable félin</p>
    </div>
    <div style="height:1px;background:#f0d5c0;margin:0.75rem 0;"></div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.7rem;font-weight:800;color:#c8956c;text-transform:uppercase;letter-spacing:0.08em;padding-left:0.5rem;margin:0 0 0.3rem 0;">Menu principal</p>', unsafe_allow_html=True)
    page = st.radio("", [
        "🏠 Tableau de bord",
        "📄 Factures fournisseurs",
        "🧾 Facturation clients",
        "💰 Notes de frais",
        "📊 Comptabilité",
        "👥 Clients & Devis",
    ], label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:#f0d5c0;margin:0.75rem 0;"></div>', unsafe_allow_html=True)
    email_disp = st.session_state.get("user_email","")
    st.markdown(f'<p style="font-size:0.75rem;color:#c8956c;padding-left:0.5rem;margin:0 0 0.5rem 0;">👤 {email_disp}</p>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

api_key = st.secrets["GEMINI_API_KEY"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TABLEAU DE BORD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Tableau de bord":
    st.markdown("""
    <div style="padding:1rem 0 1.5rem 0;">
        <h1 style="color:#a0522d;font-weight:800;margin:0;font-size:1.6rem;">Tableau de bord 🐱</h1>
        <p style="color:#c8956c;margin:0.3rem 0 0 0;">Bonjour ! Voici un résumé de votre activité financière 🐾</p>
    </div>
    """, unsafe_allow_html=True)

    factures_four = st.session_state["resultats"]
    notes         = st.session_state["notes_frais"]
    factures_vte  = st.session_state["factures_vente"]

    # KPIs globaux
    col1,col2,col3,col4,col5 = st.columns(5)
    try: total_achats = sum(float(str(f.get("montant_ttc","0")).replace(",",".") or 0) for f in factures_four)
    except: total_achats = 0
    try: total_frais = sum(float(f.get("Montant TTC (€)",0) or 0) for f in notes)
    except: total_frais = 0
    try: total_ventes = sum(float(str(f.get("montant_ttc","0")).replace(",",".") or 0) for f in factures_vte)
    except: total_ventes = 0
    try: tva_collectee  = sum(float(str(f.get("tva","0")).replace(",",".") or 0) for f in factures_vte)
    except: tva_collectee = 0
    try: tva_deductible = sum(float(str(f.get("tva","0")).replace(",",".") or 0) for f in factures_four)
    except: tva_deductible = 0
    solde_tva = tva_collectee - tva_deductible

    for col,(icon,lbl,val) in zip(
        [col1,col2,col3,col4,col5],
        [("💶","Ventes TTC",f"{total_ventes:,.0f} €"),
         ("🛒","Achats TTC",f"{total_achats:,.0f} €"),
         ("💸","Notes frais",f"{total_frais:,.0f} €"),
         ("📊","TVA à reverser",f"{solde_tva:,.0f} €"),
         ("💰","Résultat net",f"{total_ventes-total_achats-total_frais:,.0f} €")]
    ):
        with col:
            st.markdown(f'''<div class="kpi-card"><div class="kpi-icon">{icon}</div>
            <div class="kpi-val">{val}</div><div class="kpi-lbl">{lbl}</div></div>''', unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([3,2])

    with col_l:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">📄 Dernières factures fournisseurs</p>', unsafe_allow_html=True)
        if factures_four:
            for f in factures_four[-5:][::-1]:
                ttc = float(str(f.get("montant_ttc","0")).replace(",",".") or 0)
                st.markdown(f"""
                <div class="stat-row">
                    <div>
                        <span style="font-weight:700;color:#2d3748;">{f.get("fournisseur","—")}</span>
                        <span style="color:#c8956c;font-size:0.78rem;margin-left:0.5rem;">{f.get("date","")}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:0.75rem;">
                        <span style="font-weight:700;color:#a0522d;">{ttc:,.2f} €</span>
                        {badge_html(f.get("statut","—"))}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#c8956c;font-size:0.85rem;text-align:center;padding:1rem 0;">Aucune facture pour l'instant</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">📊 Répartition TVA</p>', unsafe_allow_html=True)
        for lbl, val, color in [
            ("TVA collectée (ventes)", tva_collectee, "#e8856a"),
            ("TVA déductible (achats)", tva_deductible, "#7fc87f"),
            ("Solde à reverser", solde_tva, "#f0a070"),
        ]:
            st.markdown(f"""
            <div class="stat-row">
                <span style="font-size:0.85rem;color:#4a5568;">{lbl}</span>
                <span style="font-weight:700;color:{color};">{val:,.2f} €</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 0.75rem 0;">⚡ Accès rapide</p>', unsafe_allow_html=True)
        for label, target in [("📄 Importer des factures","📄 Factures fournisseurs"),
                               ("🧾 Créer une facture","🧾 Facturation clients"),
                               ("💰 Saisir une dépense","💰 Notes de frais")]:
            if st.button(label, use_container_width=True, key=f"dash_{target}"):
                st.session_state["_nav"] = target
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("_nav"):
        page = st.session_state.pop("_nav")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES FOURNISSEURS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Factures fournisseurs":
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Factures fournisseurs 🐾</strong><br>
            <span style="color:#c8956c;">Importez vos factures, je les analyse avec Gemini IA !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📤 Import & Extraction", "📋 Liste"])

    with tab1:
        fichiers = st.file_uploader("🐾 Glissez vos factures ici",
            type=["pdf","jpg","jpeg","png"], accept_multiple_files=True)

        if fichiers:
            noms_actuels   = sorted([f.name for f in fichiers])
            noms_precedents = sorted(st.session_state.get("fichiers_extraits",[]))
            changed = noms_actuels != noms_precedents
            if changed and st.session_state["resultats"]:
                st.warning("⚠️ Nouveaux fichiers détectés — relancez l'extraction.")
            st.markdown(f'''<div style="background:#fff8f3;border:2px solid #f0d5c0;border-radius:12px;
                padding:0.75rem 1rem;margin:0.5rem 0;color:#a0522d;font-weight:700;font-size:0.85rem;">
                🐱 {len(fichiers)} fichier(s) prêt(s) à analyser</div>''', unsafe_allow_html=True)

            col_b1,col_b2,col_b3 = st.columns([1,2,1])
            with col_b2:
                lancer = st.button("🐾 Lancer l'extraction IA", use_container_width=True)

            if lancer and (changed or not st.session_state["resultats"]):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                progress = st.progress(0); resultats = []
                for i, f in enumerate(fichiers):
                    with st.spinner(f"Analyse de {f.name}…"):
                        try:
                            data = extraire_facture(f, model, mois_list[now.month-1], now.year)
                            data.update({"fichier":f.name,"statut":"Validé 😸"})
                            resultats.append(data)
                        except Exception as e:
                            resultats.append({"fichier":f.name,"date":"","fournisseur":"",
                                "numero_facture":"","montant_ht":"","tva":"","montant_ttc":"",
                                "description":str(e),"categorie":"","statut":"Erreur 🙀"})
                    progress.progress(int((i+1)/len(fichiers)*100))
                progress.empty()
                st.session_state["resultats"] = resultats
                st.session_state["fichiers_extraits"] = noms_actuels
                st.rerun()

            if st.session_state["resultats"] and not changed:
                resultats = st.session_state["resultats"]
                st.markdown('''<div class="cat-container">
                    <div style="font-size:2rem;">😻</div>
                    <div class="chat-bubble"><span style="color:#a0522d;font-weight:700;">
                    Purrrfect ! Voici ce que j'ai trouvé 🐾</span></div></div>''', unsafe_allow_html=True)

                col_p1,col_p2 = st.columns(2)
                with col_p1: mois_r = st.selectbox("Mois", mois_list, index=now.month-1)
                with col_p2: annee_r = st.selectbox("Année", list(range(2023,2031)), index=list(range(2023,2031)).index(now.year))

                df = pd.DataFrame(resultats).rename(columns={
                    "fichier":"Fichier","date":"Date","fournisseur":"Fournisseur",
                    "numero_facture":"N° Facture","montant_ht":"HT (€)","tva":"TVA (€)",
                    "montant_ttc":"TTC (€)","description":"Description","categorie":"Catégorie","statut":"Statut"})
                df[["Mois","Année"]] = mois_r, annee_r
                df_edit = st.data_editor(df, use_container_width=True, hide_index=True,
                    column_config={
                        "Statut":st.column_config.SelectboxColumn("Statut",
                            options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]),
                        "Catégorie":st.column_config.SelectboxColumn("Catégorie",
                            options=list(CAT_ICONS.keys()))})

                col_d1,col_d2,_ = st.columns([1,1,2])
                buf = io.BytesIO(); df_edit.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
                with col_d1: st.download_button("📥 Excel",data=buf,
                    file_name=f"factures_{mois_r}_{annee_r}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
                with col_d2: st.download_button("📄 CSV",data=df_edit.to_csv(index=False).encode(),
                    file_name=f"factures_{mois_r}_{annee_r}.csv",mime="text/csv",use_container_width=True)

    with tab2:
        resultats = st.session_state["resultats"]
        if resultats:
            col1,col2,col3,col4 = st.columns(4)
            ttcs = [float(str(r.get("montant_ttc","0")).replace(",",".") or 0) for r in resultats]
            for col,(icon,lbl,val) in zip([col1,col2,col3,col4],[
                ("🐱","Factures",str(len(resultats))),
                ("😸","Validées",str(sum(1 for r in resultats if "Validé" in r.get("statut","")))),
                ("🙀","Erreurs",str(sum(1 for r in resultats if "Erreur" in r.get("statut","")))),
                ("💰","Total TTC",f"{sum(ttcs):,.2f} €")]):
                with col: st.markdown(f'<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-val">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            for r in resultats:
                ttc = float(str(r.get("montant_ttc","0")).replace(",",".") or 0)
                st.markdown(f"""<div class="stat-row">
                    <div><span style="font-weight:700;color:#2d3748;">{r.get("fournisseur","—")}</span>
                    <span style="color:#c8956c;font-size:0.78rem;margin-left:0.5rem;">{r.get("date","")}</span></div>
                    <div style="display:flex;align-items:center;gap:0.75rem;">
                        <span style="font-weight:700;color:#a0522d;">{ttc:,.2f} €</span>
                        {badge_html(r.get("statut","—"))}</div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Aucune facture analysée pour l'instant.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURATION CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧾 Facturation clients":
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Facturation clients 🐾</strong><br>
            <span style="color:#c8956c;">Créez et gérez vos factures de vente !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_new, tab_list = st.tabs(["➕ Nouvelle facture", "📋 Mes factures"])

    with tab_new:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
        with st.form("form_facture_vente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fv_numero   = st.text_input("N° Facture", placeholder="FAC-2026-001")
                fv_client   = st.text_input("Client", placeholder="Nom ou entreprise")
                fv_date     = st.date_input("Date d'émission", value=datetime.now())
                fv_echeance = st.date_input("Date d'échéance")
                fv_desc     = st.text_area("Description / Objet", height=80)
            with col2:
                fv_ht  = st.number_input("Montant HT (€)", min_value=0.0, step=0.01, format="%.2f")
                fv_tva_pct = st.selectbox("TVA", ["20%","10%","5.5%","0%"])
                tva_v = float(fv_tva_pct.replace("%",""))/100
                fv_tva_mnt = round(fv_ht * tva_v, 2)
                fv_ttc = round(fv_ht + fv_tva_mnt, 2)
                st.markdown(f"""
                <div class="card-green" style="margin-top:0.5rem;">
                    <div class="stat-row"><span style="color:#4a5568;">TVA ({fv_tva_pct})</span>
                        <strong style="color:#2d6b4a;">{fv_tva_mnt:.2f} €</strong></div>
                    <div class="stat-row"><span style="font-weight:800;color:#1a1a2e;">Total TTC</span>
                        <strong style="color:#2d6b4a;font-size:1.2rem;">{fv_ttc:.2f} €</strong></div>
                </div>
                """, unsafe_allow_html=True)
                fv_statut = st.selectbox("Statut", ["À payer","Payée","En retard","Brouillon"])
                fv_cat = st.selectbox("Catégorie", list(CAT_ICONS.keys()))

            col_s1,col_s2,col_s3 = st.columns([1,2,1])
            with col_s2:
                if st.form_submit_button("➕ Créer la facture 🐾", use_container_width=True, type="primary"):
                    if not fv_client: st.error("Veuillez saisir un client.")
                    elif fv_ht <= 0: st.error("Le montant doit être > 0.")
                    else:
                        st.session_state["factures_vente"].append({
                            "numero":fv_numero,"client":fv_client,
                            "date":fv_date.strftime("%d/%m/%Y"),
                            "echeance":fv_echeance.strftime("%d/%m/%Y"),
                            "description":fv_desc,"montant_ht":fv_ht,
                            "tva_pct":fv_tva_pct,"tva":fv_tva_mnt,
                            "montant_ttc":fv_ttc,"statut":fv_statut,"categorie":fv_cat
                        })
                        st.success("✅ Facture créée !")
                        st.rerun()

    with tab_list:
        fv_list = st.session_state["factures_vente"]
        if fv_list:
            col1,col2,col3,col4 = st.columns(4)
            total_vte  = sum(float(f.get("montant_ttc",0)) for f in fv_list)
            nb_payees  = sum(1 for f in fv_list if f.get("statut")=="Payée")
            nb_attente = sum(1 for f in fv_list if f.get("statut")=="À payer")
            nb_retard  = sum(1 for f in fv_list if f.get("statut")=="En retard")
            for col,(icon,lbl,val) in zip([col1,col2,col3,col4],[
                ("🧾","Factures",str(len(fv_list))),("😸","Payées",str(nb_payees)),
                ("⏳","À payer",str(nb_attente)),("💰","Total TTC",f"{total_vte:,.2f} €")]):
                with col: st.markdown(f'<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-val">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            df_fv = pd.DataFrame(fv_list)
            df_fv_edit = st.data_editor(df_fv, use_container_width=True, hide_index=True,
                column_config={"statut":st.column_config.SelectboxColumn("statut",
                    options=["À payer","Payée","En retard","Brouillon"])})
            col_d1,col_d2,_ = st.columns([1,1,2])
            buf=io.BytesIO(); df_fv_edit.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
            with col_d1: st.download_button("📥 Excel",data=buf,
                file_name="factures_vente.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
            with col_d2: st.download_button("📄 CSV",data=df_fv_edit.to_csv(index=False).encode(),
                file_name="factures_vente.csv",mime="text/csv",use_container_width=True)
        else:
            st.markdown("""<div style="text-align:center;padding:3rem 0;">
                <div style="font-size:3rem;">🐱</div>
                <p style="color:#a0522d;font-weight:700;">Aucune facture client pour l'instant</p>
                <p style="color:#c8956c;font-size:0.85rem;">Créez votre première facture 🐾</p>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Notes de frais 🐾</strong><br>
            <span style="color:#c8956c;">Saisissez et gérez vos dépenses professionnelles !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_add, tab_list = st.tabs(["➕ Nouvelle dépense","📋 Toutes les dépenses"])

    with tab_add:
        with st.form("form_nf", clear_on_submit=True):
            col1,col2 = st.columns(2)
            with col1:
                nf_date  = st.date_input("📅 Date", value=datetime.now())
                nf_emp   = st.text_input("👤 Employé", placeholder="Prénom Nom")
                nf_cat   = st.selectbox("📂 Catégorie", list(CAT_ICONS.keys()))
                nf_desc  = st.text_area("📝 Description", height=80)
            with col2:
                nf_ht  = st.number_input("💶 Montant HT (€)", min_value=0.0, step=0.01, format="%.2f")
                nf_tva = st.selectbox("📊 TVA", ["20%","10%","5.5%","0%"])
                tva_v  = float(nf_tva.replace("%",""))/100
                tva_m  = round(nf_ht * tva_v, 2)
                ttc    = round(nf_ht + tva_m, 2)
                st.markdown(f"""
                <div class="card" style="padding:0.9rem;margin-top:0.5rem;">
                    <div class="stat-row"><span style="color:#c8956c;font-size:0.85rem;">TVA</span>
                        <strong style="color:#a0522d;">{tva_m:.2f} €</strong></div>
                    <div class="stat-row"><span style="font-weight:800;color:#1a1a2e;">Total TTC</span>
                        <strong style="color:#e8856a;font-size:1.1rem;">{ttc:.2f} €</strong></div>
                </div>""", unsafe_allow_html=True)
                nf_pay  = st.selectbox("💳 Paiement", ["Carte entreprise","Espèces","Carte perso","Virement"])
                nf_just = st.file_uploader("📸 Justificatif", type=["pdf","jpg","jpeg","png"], key="just")
            col_s1,col_s2,col_s3 = st.columns([1,2,1])
            with col_s2:
                if st.form_submit_button("➕ Ajouter 🐾", use_container_width=True, type="primary"):
                    if not nf_emp: st.error("Nom d'employé requis !")
                    elif nf_ht<=0: st.error("Montant > 0 !")
                    else:
                        st.session_state["notes_frais"].append({
                            "Date":nf_date.strftime("%d/%m/%Y"),"Employé":nf_emp,
                            "Catégorie":f"{CAT_ICONS.get(nf_cat,'')} {nf_cat}","Description":nf_desc,
                            "Montant HT (€)":nf_ht,"TVA":nf_tva,"Montant TVA (€)":tva_m,
                            "Montant TTC (€)":ttc,"Paiement":nf_pay,
                            "Justificatif":nf_just.name if nf_just else "—","Statut":"En attente 😺"})
                        st.success("✅ Dépense ajoutée 🐾")
                        st.rerun()

    with tab_list:
        notes = st.session_state["notes_frais"]
        if notes:
            df_nf = pd.DataFrame(notes)
            col1,col2,col3,col4 = st.columns(4)
            for col,(icon,lbl,val) in zip([col1,col2,col3,col4],[
                ("📝","Dépenses",str(len(df_nf))),
                ("😸","Validées",str(len(df_nf[df_nf["Statut"]=="Validé 😸"]))),
                ("😺","En attente",str(len(df_nf[df_nf["Statut"]=="En attente 😺"]))),
                ("💰","Total TTC",f'{df_nf["Montant TTC (€)"].sum():,.2f} €')]):
                with col: st.markdown(f'<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-val">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            col_f1,col_f2,col_f3 = st.columns(3)
            with col_f1: fe = st.text_input("🔍 Employé","")
            with col_f2: fc = st.selectbox("Catégorie",["Toutes"]+list(df_nf["Catégorie"].unique()))
            with col_f3: fs = st.selectbox("Statut",["Tous","En attente 😺","Validé 😸","Refusé 🙀"])
            df_f = df_nf.copy()
            if fe: df_f = df_f[df_f["Employé"].str.contains(fe,case=False)]
            if fc!="Toutes": df_f = df_f[df_f["Catégorie"]==fc]
            if fs!="Tous": df_f = df_f[df_f["Statut"]==fs]
            st.data_editor(df_f, use_container_width=True, hide_index=True,
                column_config={"Statut":st.column_config.SelectboxColumn("Statut",
                    options=["En attente 😺","Validé 😸","Refusé 🙀","À vérifier 🐱"])})
            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            col_a1,col_a2,col_a3,_ = st.columns([1,1,1,1])
            buf=io.BytesIO(); df_nf.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
            with col_a1: st.download_button("📥 Excel",data=buf,file_name="notes_frais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
            with col_a2: st.download_button("📄 CSV",data=df_nf.to_csv(index=False).encode(),
                file_name="notes_frais.csv",mime="text/csv",use_container_width=True)
            with col_a3:
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                if st.button("🗑️ Effacer",use_container_width=True):
                    st.session_state["notes_frais"]=[]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div style="text-align:center;padding:3rem 0;">
                <div style="font-size:3rem;">🐱</div>
                <p style="color:#a0522d;font-weight:700;">Aucune note de frais pour l'instant !</p>
                <p style="color:#c8956c;font-size:0.85rem;">Ajoutez votre première dépense 🐾</p>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPTABILITÉ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Comptabilité":
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Comptabilité 🐾</strong><br>
            <span style="color:#c8956c;">Vue consolidée de vos charges, produits et TVA !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    factures_four = st.session_state["resultats"]
    notes         = st.session_state["notes_frais"]
    factures_vte  = st.session_state["factures_vente"]

    tab_bilan, tab_tva, tab_gl = st.tabs(["📈 Bilan simplifié","🧾 Déclaration TVA","📒 Grand livre"])

    with tab_bilan:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
        try: total_achats = sum(float(str(f.get("montant_ttc","0")).replace(",",".") or 0) for f in factures_four)
        except: total_achats=0
        try: total_frais = sum(float(f.get("Montant TTC (€)",0) or 0) for f in notes)
        except: total_frais=0
        try: total_ventes = sum(float(str(f.get("montant_ttc","0")).replace(",",".") or 0) for f in factures_vte)
        except: total_ventes=0
        charges = total_achats + total_frais
        resultat = total_ventes - charges

        col1,col2,col3 = st.columns(3)
        for col,(icon,lbl,val,color) in zip([col1,col2,col3],[
            ("💶","Chiffre d'affaires TTC",f"{total_ventes:,.2f} €","#2d6b4a"),
            ("🛒","Total charges TTC",f"{charges:,.2f} €","#c0392b"),
            ("💰","Résultat net",f"{resultat:,.2f} €","#a0522d" if resultat>=0 else "#c0392b")]):
            with col:
                st.markdown(f'''<div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{color};">{val}</div>
                    <div class="kpi-lbl">{lbl}</div></div>''', unsafe_allow_html=True)

        st.markdown('<div style="height:1.25rem"></div>', unsafe_allow_html=True)
        col_l,col_r = st.columns(2)
        with col_l:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">📊 Détail des charges</p>', unsafe_allow_html=True)
            for lbl,val in [("Factures fournisseurs",total_achats),("Notes de frais",total_frais),("Total charges",charges)]:
                fw = "800" if lbl=="Total charges" else "500"
                st.markdown(f'<div class="stat-row"><span style="font-weight:{fw};color:#4a5568;">{lbl}</span><span style="font-weight:{fw};color:#a0522d;">{val:,.2f} €</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Répartition par catégorie
            cat_totals = {}
            for f in factures_four:
                c = f.get("categorie","Autres")
                try: cat_totals[c] = cat_totals.get(c,0) + float(str(f.get("montant_ttc","0")).replace(",",".") or 0)
                except: pass
            for n in notes:
                c = str(n.get("Catégorie","Autres")).split(" ")[-1]
                try: cat_totals[c] = cat_totals.get(c,0) + float(n.get("Montant TTC (€)",0) or 0)
                except: pass
            if cat_totals:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">🏷️ Par catégorie</p>', unsafe_allow_html=True)
                for c,v in sorted(cat_totals.items(),key=lambda x:-x[1]):
                    icon = CAT_ICONS.get(c,"📎")
                    st.markdown(f'<div class="stat-row"><span style="color:#4a5568;">{icon} {c}</span><span style="font-weight:700;color:#a0522d;">{v:,.2f} €</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">💶 Détail des produits</p>', unsafe_allow_html=True)
            by_client = {}
            for f in factures_vte:
                c = f.get("client","—")
                try: by_client[c] = by_client.get(c,0) + float(f.get("montant_ttc",0) or 0)
                except: pass
            if by_client:
                for c,v in sorted(by_client.items(),key=lambda x:-x[1]):
                    st.markdown(f'<div class="stat-row"><span style="color:#4a5568;">👤 {c}</span><span style="font-weight:700;color:#2d6b4a;">{v:,.2f} €</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#c8956c;font-size:0.85rem;text-align:center;padding:1rem 0;">Aucune vente enregistrée</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_tva:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
        try: tva_col  = sum(float(str(f.get("tva","0")).replace(",",".") or 0) for f in factures_vte)
        except: tva_col=0
        try: tva_ded_four = sum(float(str(f.get("tva","0")).replace(",",".") or 0) for f in factures_four)
        except: tva_ded_four=0
        try: tva_ded_ndf = sum(float(f.get("Montant TVA (€)",0) or 0) for f in notes)
        except: tva_ded_ndf=0
        tva_ded   = tva_ded_four + tva_ded_ndf
        tva_solde = tva_col - tva_ded

        col1,col2,col3 = st.columns(3)
        for col,(icon,lbl,val,color) in zip([col1,col2,col3],[
            ("📤","TVA collectée",f"{tva_col:,.2f} €","#a0522d"),
            ("📥","TVA déductible",f"{tva_ded:,.2f} €","#2d6b4a"),
            ("🏦","Solde à reverser",f"{tva_solde:,.2f} €","#c0392b" if tva_solde>0 else "#2d6b4a")]):
            with col:
                st.markdown(f'''<div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{color};">{val}</div>
                    <div class="kpi-lbl">{lbl}</div></div>''', unsafe_allow_html=True)

        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 1rem 0;">📋 Récapitulatif déclaration TVA</p>', unsafe_allow_html=True)
        rows_tva = [
            ("Ventes","TVA collectée sur ventes",tva_col,"badge-orange"),
            ("Achats fournisseurs","TVA déductible factures",tva_ded_four,"badge-green"),
            ("Notes de frais","TVA déductible NDF",tva_ded_ndf,"badge-green"),
            ("SOLDE","TVA nette à reverser à l'État",tva_solde,"badge-red" if tva_solde>0 else "badge-green"),
        ]
        for section,lbl,val,badge_cls in rows_tva:
            fw = "800" if section=="SOLDE" else "500"
            st.markdown(f'''<div class="stat-row">
                <div><span class="badge {badge_cls}" style="margin-right:0.5rem;">{section}</span>
                <span style="font-weight:{fw};color:#4a5568;">{lbl}</span></div>
                <span style="font-weight:800;color:#a0522d;">{val:,.2f} €</span>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_gl:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
        all_lignes = []
        for f in factures_four:
            try: ttc=float(str(f.get("montant_ttc","0")).replace(",",".") or 0)
            except: ttc=0
            all_lignes.append({"Date":f.get("date",""),"Type":"Achat","Tiers":f.get("fournisseur","—"),
                "Description":f.get("description",""),"Catégorie":f.get("categorie",""),
                "Débit":ttc,"Crédit":0,"Statut":f.get("statut","")})
        for n in notes:
            all_lignes.append({"Date":n.get("Date",""),"Type":"Note de frais","Tiers":n.get("Employé","—"),
                "Description":n.get("Description",""),"Catégorie":n.get("Catégorie",""),
                "Débit":float(n.get("Montant TTC (€)",0) or 0),"Crédit":0,"Statut":n.get("Statut","")})
        for f in factures_vte:
            all_lignes.append({"Date":f.get("date",""),"Type":"Vente","Tiers":f.get("client","—"),
                "Description":f.get("description",""),"Catégorie":f.get("categorie",""),
                "Débit":0,"Crédit":float(f.get("montant_ttc",0) or 0),"Statut":f.get("statut","")})
        if all_lignes:
            df_gl = pd.DataFrame(all_lignes)
            st.dataframe(df_gl, use_container_width=True, hide_index=True)
            buf=io.BytesIO(); df_gl.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
            col_d1,_,_ = st.columns([1,1,2])
            with col_d1: st.download_button("📥 Exporter le grand livre",data=buf,
                file_name="grand_livre.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        else:
            st.markdown("""<div style="text-align:center;padding:3rem 0;">
                <div style="font-size:3rem;">🐱</div>
                <p style="color:#a0522d;font-weight:700;">Aucune écriture pour l'instant</p>
                <p style="color:#c8956c;font-size:0.85rem;">Vos écritures apparaîtront ici au fur et à mesure 🐾</p>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CLIENTS & DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Clients & Devis":
    st.markdown("""
    <div class="cat-container">
        <div style="font-size:3rem;">🐱</div>
        <div class="chat-bubble">
            <strong style="color:#a0522d;">Clients & Devis 🐾</strong><br>
            <span style="color:#c8956c;">Gérez vos clients et créez vos devis !</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_clients, tab_devis = st.tabs(["👥 Clients","📋 Devis"])

    with tab_clients:
        with st.form("form_client", clear_on_submit=True):
            st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 0.75rem 0;">➕ Nouveau client</p>', unsafe_allow_html=True)
            col1,col2,col3 = st.columns(3)
            with col1:
                cl_nom    = st.text_input("Nom / Raison sociale")
                cl_email  = st.text_input("Email")
            with col2:
                cl_tel    = st.text_input("Téléphone")
                cl_siret  = st.text_input("SIRET")
            with col3:
                cl_adresse = st.text_area("Adresse", height=90)
            col_s1,col_s2,col_s3 = st.columns([1,2,1])
            with col_s2:
                if st.form_submit_button("➕ Ajouter le client 🐾", use_container_width=True, type="primary"):
                    if not cl_nom: st.error("Nom requis !")
                    else:
                        st.session_state["clients"].append({
                            "Nom":cl_nom,"Email":cl_email,"Téléphone":cl_tel,
                            "SIRET":cl_siret,"Adresse":cl_adresse,"Nb factures":0})
                        st.success(f"✅ Client {cl_nom} ajouté !")
                        st.rerun()

        if st.session_state["clients"]:
            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            df_cl = pd.DataFrame(st.session_state["clients"])
            st.dataframe(df_cl, use_container_width=True, hide_index=True)
        else:
            st.markdown('<p style="color:#c8956c;text-align:center;padding:1rem;">Aucun client enregistré.</p>', unsafe_allow_html=True)

    with tab_devis:
        with st.form("form_devis", clear_on_submit=True):
            st.markdown('<p style="font-weight:800;color:#a0522d;margin:0 0 0.75rem 0;">➕ Nouveau devis</p>', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                dv_num     = st.text_input("N° Devis", placeholder="DEV-2026-001")
                dv_client  = st.text_input("Client")
                dv_date    = st.date_input("Date", value=datetime.now())
                dv_valid   = st.date_input("Validité jusqu'au")
            with col2:
                dv_desc    = st.text_area("Description / Objet", height=80)
                dv_ht      = st.number_input("Montant HT (€)", min_value=0.0, step=0.01, format="%.2f")
                dv_tva_pct = st.selectbox("TVA", ["20%","10%","5.5%","0%"])
                tva_v      = float(dv_tva_pct.replace("%",""))/100
                dv_ttc     = round(dv_ht*(1+tva_v),2)
                dv_statut  = st.selectbox("Statut", ["Brouillon","Envoyé","Accepté","Refusé"])
            col_s1,col_s2,col_s3 = st.columns([1,2,1])
            with col_s2:
                if st.form_submit_button("➕ Créer le devis 🐾", use_container_width=True, type="primary"):
                    if not dv_client: st.error("Client requis !")
                    else:
                        st.session_state["devis"].append({
                            "N° Devis":dv_num,"Client":dv_client,
                            "Date":dv_date.strftime("%d/%m/%Y"),
                            "Validité":dv_valid.strftime("%d/%m/%Y"),
                            "Description":dv_desc,"HT (€)":dv_ht,
                            "TVA":dv_tva_pct,"TTC (€)":dv_ttc,"Statut":dv_statut})
                        st.success("✅ Devis créé !")
                        st.rerun()

        if st.session_state["devis"]:
            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            df_dv = pd.DataFrame(st.session_state["devis"])
            df_dv_edit = st.data_editor(df_dv, use_container_width=True, hide_index=True,
                column_config={"Statut":st.column_config.SelectboxColumn("Statut",
                    options=["Brouillon","Envoyé","Accepté","Refusé"])})
            buf=io.BytesIO(); df_dv_edit.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
            col_d1,_ = st.columns([1,3])
            with col_d1: st.download_button("📥 Exporter",data=buf,file_name="devis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        else:
            st.markdown('<p style="color:#c8956c;text-align:center;padding:1rem;">Aucun devis pour l'instant.</p>', unsafe_allow_html=True)
