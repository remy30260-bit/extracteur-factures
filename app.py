import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

st.set_page_config(page_title="",page_icon="🐱",layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE & GEMINI
# ═══════════════════════════════════════════════════════════════════════════════
def get_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def configure_gemini():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel("gemini-2.5-flash")
    except:
        return None

# 
# ═══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main { background: #fdf8f5; }
    </style>
    """, unsafe_allow_html=True)


def render_cat_widget():
    import random
    import streamlit.components.v1 as components
    msg = random.choice(["Miaou ! 📄","Facture prête !","Tout est OK ! ✅","Je veille sur vos factures 🐾"])
    components.html(f"""
    <div style="position:fixed;bottom:20px;right:20px;z-index:9999;
         animation:cat-bounce 2s ease-in-out infinite;font-family:Inter,sans-serif;">
        <div id="bubble" style="position:absolute;bottom:60px;right:0;
             background:white;border:2px solid #f0a070;border-radius:16px 16px 4px 16px;
             padding:0.5rem 0.8rem;font-size:0.75rem;color:#c8956c;font-weight:600;
             white-space:nowrap;opacity:0;transition:all 0.3s;
             box-shadow:0 4px 12px rgba(200,149,108,0.2);">{msg}</div>
        <div style="font-size:2.5rem;filter:drop-shadow(0 4px 8px rgba(200,149,108,0.4));
             cursor:pointer;transition:transform 0.2s;"
             onmouseover="document.getElementById('bubble').style.opacity='1';
                          this.style.transform='scale(1.2) rotate(-10deg)'"
             onmouseout="document.getElementById('bubble').style.opacity='0';
                         this.style.transform='scale(1)'">🐱</div>
    </div>
    <style>
    @keyframes cat-bounce {{
        0%,100% {{ transform:translateY(0); }}
        50%      {{ transform:translateY(-8px); }}
    }}
    </style>
    """, height=80)


def cat_progress_bar(value: float, label: str = ""):

    pct = int(value * 100)
    st.markdown(f"""
    {f'<div style="font-size:0.8rem;color:#c8956c;font-weight:600;margin-bottom:4px;">{label}</div>' if label else ''}
    <div style="position:relative;background:rgba(240,160,112,0.1);
         border-radius:20px;height:28px;margin:0.5rem 0;
         border:1px solid rgba(240,160,112,0.3);overflow:visible;">
        <div style="width:{pct}%;height:100%;border-radius:20px;
             background:linear-gradient(90deg,#f0c090,#f0a070);"></div>
        <span style="position:absolute;top:-8px;left:{max(pct,3)}%;
              font-size:1.4rem;transform:translateX(-50%);">🐱</span>
        <span style="position:absolute;right:8px;top:50%;
              transform:translateY(-50%);font-size:0.75rem;
              color:#c8956c;font-weight:700;">{pct}%</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }

   [data-testid="stSidebarHeader"] { display: none !important; }
   [data-testid="collapsedControl"] { display: none !important; }
   header[data-testid="stHeader"] { display: none !important; }


    .main, .block-container {
        background: linear-gradient(135deg, #fff8f0 0%, #fdf0e8 100%) !important;
        padding-top: 0 !important;
        max-width: 100% !important;
    }
    .block-container { padding: 0 2rem 2rem !important; }

    /* ── TOP NAV ── */
    .topnav {
        position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(240,160,112,0.2);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 2rem; height: 64px;
        box-shadow: 0 4px 24px rgba(240,160,112,0.12);
    }
    .topnav-logo { display:flex; align-items:center; gap:0.6rem; }
    .topnav-logo-icon { font-size:1.8rem; animation: float 3s ease-in-out infinite; }
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }
    .topnav-logo-text {
        font-size:1.3rem; font-weight:800;
        background: linear-gradient(135deg,#f0a070,#e8856a);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .page-content { margin-top: 80px; }

    /* ── HERO ── */
    .hero {
        background: linear-gradient(135deg,#f0a070 0%,#e8856a 50%,#d4694f 100%);
        border-radius: 28px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
        color: white; box-shadow: 0 12px 40px rgba(240,160,112,0.35);
        position: relative; overflow: hidden;
    }
    .hero::before {
        content:''; position:absolute; top:-50%; right:-10%;
        width:400px; height:400px; background:rgba(255,255,255,0.08); border-radius:50%;
    }
    .hero h1 { margin:0; font-size:1.8rem; font-weight:800; }
    .hero p  { margin:0.4rem 0 0; opacity:0.9; font-size:0.95rem; }

    /* ── CARDS ── */
    .metric-card {
        background: white; border-radius: 20px; padding: 1.5rem;
        border: 1px solid rgba(240,160,112,0.15);
        box-shadow: 0 4px 20px rgba(240,160,112,0.08);
        transition: all 0.3s ease; position: relative; overflow: hidden;
    }
    .metric-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:3px;
        background: linear-gradient(90deg,#f0a070,#e8856a); border-radius:20px 20px 0 0;
    }
    .metric-card:hover { transform:translateY(-4px); box-shadow:0 12px 35px rgba(240,160,112,0.18); }

    .kpi-card {
        background: white; border-radius: 18px; padding: 1.3rem 1.5rem;
        border: 1px solid rgba(240,160,112,0.15);
        box-shadow: 0 4px 16px rgba(240,160,112,0.08);
        transition: all 0.3s ease; cursor: default;
    }
    .kpi-card:hover { transform:translateY(-3px); box-shadow:0 10px 30px rgba(240,160,112,0.16); }
    .kpi-icon { font-size:2rem; margin-bottom:0.5rem; }
    .kpi-value { font-size:1.8rem; font-weight:800; color:#a0522d; line-height:1; }
    .kpi-label { font-size:0.78rem; color:#c8956c; font-weight:600;
                 text-transform:uppercase; letter-spacing:0.05em; margin-top:0.3rem; }
    .kpi-delta { font-size:0.8rem; margin-top:0.4rem; font-weight:500; }

    /* ── PENNYLANE MODULES ── */
    .module-card {
        background: white; border-radius: 20px; padding: 1.5rem;
        border: 1px solid rgba(240,160,112,0.15);
        box-shadow: 0 4px 20px rgba(240,160,112,0.08);
        margin-bottom: 1rem; transition: all 0.3s;
    }
    .module-header {
        display:flex; align-items:center; gap:0.8rem;
        margin-bottom:1rem; padding-bottom:0.8rem;
        border-bottom: 2px solid rgba(240,160,112,0.1);
    }
    .module-icon {
        width:42px; height:42px; border-radius:12px;
        background: linear-gradient(135deg,#f0a070,#e8856a);
        display:flex; align-items:center; justify-content:center;
        font-size:1.2rem; flex-shrink:0;
    }
    .module-title { font-size:1rem; font-weight:700; color:#a0522d; }
    .module-sub   { font-size:0.78rem; color:#c8956c; }

    /* ── FACTURE VIEWER ── */
    .invoice-viewer {
        background: white; border-radius: 20px; padding: 1.2rem;
        border: 1px solid rgba(240,160,112,0.2);
        box-shadow: 0 8px 30px rgba(240,160,112,0.12);
        position: sticky; top: 90px;
    }
    .invoice-viewer-header {
        display:flex; align-items:center; justify-content:space-between;
        margin-bottom:1rem; padding-bottom:0.8rem;
        border-bottom:2px solid rgba(240,160,112,0.1);
    }
    .invoice-viewer-title { font-weight:700; color:#a0522d; font-size:0.95rem; }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg,#f0a070,#e8856a) !important;
        color:white !important; border:none !important;
        border-radius:14px !important; font-weight:600 !important;
        font-size:0.9rem !important; padding:0.6rem 1.2rem !important;
        transition:all 0.3s !important;
        box-shadow:0 4px 12px rgba(240,160,112,0.3) !important;
    }
    .stButton > button:hover {
        transform:translateY(-2px) !important;
        box-shadow:0 8px 24px rgba(240,160,112,0.45) !important;
    }

    /* ── INPUTS ── */
    .stTextInput>div>div>input, .stNumberInput>div>div>input,
    .stSelectbox>div>div, .stTextArea>div>div>textarea {
        border-radius:14px !important;
        border:2px solid rgba(240,160,112,0.25) !important;
        background:#fffaf7 !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        background:white; border-radius:14px; padding:0.3rem;
        border:1px solid rgba(240,160,112,0.2); gap:0.2rem;
    }
    .stTabs [data-baseweb="tab"] { border-radius:10px !important; font-weight:500 !important; color:#a0522d !important; }
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg,#f0a070,#e8856a) !important; color:white !important; }

    /* ── ALERTS ── */
    .stSuccess { border-radius:14px !important; border-left:4px solid #68d391 !important; }
    .stError   { border-radius:14px !important; border-left:4px solid #fc8181 !important; }
    .stWarning { border-radius:14px !important; border-left:4px solid #f0a070 !important; }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width:6px; }
    ::-webkit-scrollbar-track { background:#fff8f0; }
    ::-webkit-scrollbar-thumb { background:#f0a070; border-radius:3px; }

    /* ── NAV SECONDARY BUTTONS ── */
    div[data-testid="stHorizontalBlock"] .stButton>button[kind="secondary"] {
        background:transparent !important; color:#a0522d !important;
        box-shadow:none !important; border:none !important; font-weight:500 !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton>button[kind="secondary"]:hover {
        background:rgba(240,160,112,0.12) !important; transform:none !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton>button[kind="primary"] {
        background:linear-gradient(135deg,#f0a070,#e8856a) !important;
        border-radius:20px !important; font-weight:600 !important;
        box-shadow:0 4px 12px rgba(240,160,112,0.4) !important;
    }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"] { border-radius:16px !important; overflow:hidden !important; border:1px solid rgba(240,160,112,0.2) !important; }

    /* ── PROGRESS ── */
    .stProgress>div>div { background:linear-gradient(90deg,#f0a070,#e8856a) !important; border-radius:10px !important; }
    </style>
    
    /* ── CHATS ANIMÉS ── */
@keyframes cat-bounce {
    0%,100% { transform:translateY(0); }
    50%      { transform:translateY(-8px); }
}
@keyframes cat-walk {
    0%   { transform:translateX(-50%) rotate(-5deg); }
    100% { transform:translateX(-50%) rotate(5deg) translateY(-2px); }
}

""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TOP NAV
# ═══════════════════════════════════════════════════════════════════════════════
def render_topnav(current_page):
    user_email = st.session_state.get("user_email", "")
    st.markdown(f"""
    <div class="topnav">
        <div class="topnav-logo">
            <span class="topnav-logo-icon">🐱</span>
            <span class="topnav-logo-text">FactureCat</span>
        </div>
    </div>
    <div class="page-content"></div>
    """, unsafe_allow_html=True)

    cols = st.columns([0.5, 1, 1, 1, 1, 1, 1, 0.5])
    pages_map = {
        1: ("🏠 Dashboard", "🏠 Dashboard"),
        2: ("📄 Factures",  "📄 Factures"),
        3: ("🧾 Notes",     "🧾 Notes de frais"),
        4: ("📊 Compta",    "📊 Comptabilité"),
        5: ("🤖 IA",        "🤖 Assistant IA"),
        6: ("🚪 Sortir",    "logout"),
    }
    for col_idx, (label, page_key) in pages_map.items():
        with cols[col_idx]:
            is_active = (current_page == page_key)
            if st.button(label, key=f"nav_{col_idx}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                if page_key == "logout":
                    st.session_state["authenticated"] = False
                    st.session_state["user_email"] = ""
                    try: get_supabase().auth.sign_out()
                    except: pass
                else:
                    st.session_state["page"] = page_key
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [Image.open(io.BytesIO(p.get_pixmap(dpi=150).tobytes("png"))) for p in doc]

def extraire_facture(model, images):
    prompt = """Analyse cette facture et extrais en JSON strict :
{
  "fournisseur": "nom",
  "numero": "numéro",
  "date": "YYYY-MM-DD",
  "montant_ht": 0.0,
  "tva": 0.0,
  "montant_ttc": 0.0,
  "categorie": "Informatique|Transport|Repas|Fournitures|Services|Autres",
  "statut": "À payer"
}
Réponds UNIQUEMENT avec le JSON, sans markdown."""
    try:
        r = model.generate_content([prompt] + images)
        text = r.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except:
        return {"fournisseur":"Non détecté","numero":"—","date":str(datetime.now().date()),
                "montant_ht":0,"tva":0,"montant_ttc":0,"categorie":"Autres","statut":"À payer"}

def get_data(table):
    try:
        supabase = get_supabase()
        uid = st.session_state.get("user_id","")
        return supabase.table(table).select("*").eq("user_id",uid).execute().data or []
    except:
        key = "resultats" if table == "factures" else "notes_frais"
        return st.session_state.get(key, [])


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_dashboard():

    # Message de bienvenue unique en haut
    st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;
         background:rgba(240,160,112,0.08);border-radius:16px;padding:1rem 1.5rem;
         border:1px solid rgba(240,160,112,0.2);">
        <div style="font-size:2.5rem;">🐱</div>
        <div>
            <h2 style="margin:0;color:#a0522d;font-weight:800;">Bonjour !</h2>
            <p style="margin:0;color:#c8956c;font-size:0.9rem;">
                Je suis FactureCat, votre assistant comptable félin, prêt à vous aider 🐾
            </p>
        </div>
        <div style="margin-left:auto;font-size:1.5rem;opacity:0.4;">🐾 🐾 🐾</div>
    </div>
    """, unsafe_allow_html=True)

    factures = get_data("factures")
    notes    = get_data("notes_frais")

    total_ttc   = sum(float(f.get("montant_ttc",0)) for f in factures)
    total_tva   = sum(float(f.get("tva",0))          for f in factures)
    a_payer     = sum(float(f.get("montant_ttc",0)) for f in factures if "payer" in str(f.get("statut","")).lower() and "payée" not in str(f.get("statut","")).lower())
    total_notes = sum(float(n.get("montant_ttc",0)) for n in notes)

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "💰", f"{total_ttc:,.0f} €", "Chiffre d'affaires TTC", "#68d391"),
        (k2, "📋", f"{len(factures)}", "Factures totales", "#63b3ed"),
        (k3, "⏳", f"{a_payer:,.0f} €", "À encaisser", "#f6ad55"),
        (k4, "🧾", f"{total_notes:,.0f} €", "Notes de frais", "#fc8181"),
        (k5, "📊", f"{total_tva:,.0f} €", "TVA collectée", "#b794f4"),
    ]
    for col, icon, val, label, color in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-value" style="color:{color};">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Charts
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if factures:
            df_f = pd.DataFrame(factures)
            if "categorie" in df_f.columns:
                grp = df_f.groupby("categorie")["montant_ttc"].sum().reset_index()
                grp.columns = ["Catégorie","Montant"]
                fig = px.pie(grp, values="Montant", names="Catégorie",
                             color_discrete_sequence=["#f0a070","#e8856a","#d4694f",
                                                      "#c8956c","#f5c5a3","#fbe0cc"],
                             hole=0.55)
                fig.update_layout(
                    title="Répartition par catégorie",
                    showlegend=True, height=320,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#a0522d"),
                    margin=dict(t=40,b=20,l=20,r=20)
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""<div class="kpi-card" style="text-align:center;padding:3rem;">
            <div style="font-size:3rem;">📊</div>
            <p style="color:#c8956c;">Aucune donnée</p></div>""", unsafe_allow_html=True)

    with col_g2:
        if factures:
            df_f = pd.DataFrame(factures)
            if "date" in df_f.columns:
                df_f["date"] = pd.to_datetime(df_f["date"], errors="coerce")
                df_f["mois"] = df_f["date"].dt.strftime("%Y-%m")
                monthly = df_f.groupby("mois")["montant_ttc"].sum().reset_index()
                monthly.columns = ["Mois","Montant"]
                fig2 = px.bar(monthly, x="Mois", y="Montant",
                              color_discrete_sequence=["#f0a070"],
                              title="Évolution mensuelle (TTC)")
                fig2.update_layout(
                    height=320, plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#a0522d"),
                    margin=dict(t=40,b=20,l=20,r=20),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(240,160,112,0.1)")
                )
                fig2.update_traces(marker_line_width=0, marker_color="rgba(240,160,112,0.85)")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("""<div class="kpi-card" style="text-align:center;padding:3rem;">
            <div style="font-size:3rem;">📈</div>
            <p style="color:#c8956c;">Aucune donnée</p></div>""", unsafe_allow_html=True)

    # Dernières factures
    st.markdown("""<div class="module-card">
    <div class="module-header">
        <div class="module-icon">📄</div>
        <div><div class="module-title">Dernières factures</div>
             <div class="module-sub">5 plus récentes</div></div>
    </div>""", unsafe_allow_html=True)
    if factures:
        df_recent = pd.DataFrame(factures[-5:][::-1])
        cols_show = [c for c in ["fournisseur","date","montant_ttc","statut","categorie"] if c in df_recent.columns]
        st.dataframe(df_recent[cols_show], use_container_width=True, hide_index=True)
    else:
        st.markdown("<p style='color:#c8956c;text-align:center;padding:2rem;'>Aucune facture</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPTABILITÉ (style Pennylane)
# ═══════════════════════════════════════════════════════════════════════════════
def show_comptabilite():
    hero("📊", "Comptabilité", "Vision complète de vos finances 💼")

    factures = get_data("factures")
    notes    = get_data("notes_frais")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trésorerie", "🏦 Grand Livre", "📋 Bilan simplifié",
        "💸 TVA", "⚠️ Alertes"
    ])

    # ── Trésorerie ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        total_recettes  = sum(float(f.get("montant_ttc",0)) for f in factures)
        total_depenses  = sum(float(n.get("montant_ttc",0)) for n in notes)
        solde           = total_recettes - total_depenses
        payees_ttc      = sum(float(f.get("montant_ttc",0)) for f in factures if "Payée" in str(f.get("statut","")))
        en_attente      = total_recettes - payees_ttc

        c1, c2, c3, c4 = st.columns(4)
        kpis_tres = [
            (c1, "💹", f"{total_recettes:,.2f} €", "Recettes totales", "#68d391"),
            (c2, "💸", f"{total_depenses:,.2f} €", "Dépenses totales", "#fc8181"),
            (c3, "💰", f"{solde:,.2f} €",          "Solde net",
             "#68d391" if solde >= 0 else "#fc8181"),
            (c4, "⏳", f"{en_attente:,.2f} €",     "En attente", "#f6ad55"),
        ]
        for col, icon, val, label, color in kpis_tres:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-value" style="color:{color};">{val}</div>
                    <div class="kpi-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        if factures or notes:
            # Courbe trésorerie
            rows = []
            for f in factures:
                rows.append({"date": f.get("date",""), "montant": float(f.get("montant_ttc",0)),
                             "type": "Recette", "label": f.get("fournisseur","")})
            for n in notes:
                rows.append({"date": n.get("date",""), "montant": -float(n.get("montant_ttc",0)),
                             "type": "Dépense", "label": n.get("description","")})
            if rows:
                df_tres = pd.DataFrame(rows)
                df_tres["date"] = pd.to_datetime(df_tres["date"], errors="coerce")
                df_tres = df_tres.dropna(subset=["date"]).sort_values("date")
                df_tres["cumul"] = df_tres["montant"].cumsum()

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_tres["date"], y=df_tres["cumul"],
                    fill="tozeroy",
                    line=dict(color="#f0a070", width=3),
                    fillcolor="rgba(240,160,112,0.15)",
                    name="Trésorerie cumulée",
                    hovertemplate="<b>%{x|%d/%m/%Y}</b><br>%{y:,.2f} €<extra></extra>"
                ))
                fig.update_layout(
                    title="Évolution de la trésorerie", height=350,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#a0522d"),
                    margin=dict(t=40,b=20,l=20,r=20),
                    xaxis=dict(showgrid=False, showline=True, linecolor="rgba(240,160,112,0.3)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(240,160,112,0.1)",
                               ticksuffix=" €")
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Grand Livre ──────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Construction du grand livre
        ecritures = []
        for f in factures:
            ecritures.append({
                "Date": f.get("date","—"),
                "Compte": "411 - Clients",
                "Libellé": f.get("fournisseur","—"),
                "Débit": float(f.get("montant_ttc",0)),
                "Crédit": 0,
                "Catégorie": f.get("categorie","—"),
                "Statut": f.get("statut","—")
            })
            ecritures.append({
                "Date": f.get("date","—"),
                "Compte": "445660 - TVA collectée",
                "Libellé": f"TVA · {f.get('fournisseur','—')}",
                "Débit": 0,
                "Crédit": float(f.get("tva",0)),
                "Catégorie": f.get("categorie","—"),
                "Statut": "—"
            })
        for n in notes:
            ecritures.append({
                "Date": n.get("date","—"),
                "Compte": "625 - Déplacements",
                "Libellé": n.get("description","—"),
                "Débit": 0,
                "Crédit": float(n.get("montant_ttc",0)),
                "Catégorie": n.get("categorie","—"),
                "Statut": "Validée"
            })

        if ecritures:
            df_gl = pd.DataFrame(ecritures)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                search_gl = st.text_input("🔍 Rechercher", key="gl_search")
            with col_f2:
                compte_f = st.selectbox("Compte", ["Tous"] + list(df_gl["Compte"].unique()), key="gl_compte")

            filtered_gl = df_gl.copy()
            if search_gl:
                filtered_gl = filtered_gl[filtered_gl["Libellé"].str.contains(search_gl, case=False, na=False)]
            if compte_f != "Tous":
                filtered_gl = filtered_gl[filtered_gl["Compte"] == compte_f]

            total_debit  = filtered_gl["Débit"].sum()
            total_credit = filtered_gl["Crédit"].sum()
            balance      = total_debit - total_credit

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="kpi-card" style="padding:1rem;">
                <div class="kpi-icon" style="font-size:1.3rem;">📤</div>
                <div class="kpi-value" style="color:#68d391;font-size:1.3rem;">{total_debit:,.2f} €</div>
                <div class="kpi-label">Total Débit</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="kpi-card" style="padding:1rem;">
                <div class="kpi-icon" style="font-size:1.3rem;">📥</div>
                <div class="kpi-value" style="color:#fc8181;font-size:1.3rem;">{total_credit:,.2f} €</div>
                <div class="kpi-label">Total Crédit</div></div>""", unsafe_allow_html=True)
            with c3:
                color_bal = "#68d391" if balance >= 0 else "#fc8181"
                st.markdown(f"""<div class="kpi-card" style="padding:1rem;">
                <div class="kpi-icon" style="font-size:1.3rem;">⚖️</div>
                <div class="kpi-value" style="color:{color_bal};font-size:1.3rem;">{balance:,.2f} €</div>
                <div class="kpi-label">Balance</div></div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.dataframe(filtered_gl, use_container_width=True, hide_index=True, height=400)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                filtered_gl.to_excel(w, index=False, sheet_name="Grand Livre")
            st.download_button("📊 Exporter Grand Livre",
                buf.getvalue(), "grand_livre.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="dl_gl")
        else:
            st.info("Aucune écriture comptable disponible")

    # ── Bilan simplifié ──────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        total_actif   = sum(float(f.get("montant_ttc",0)) for f in factures)
        total_passif  = sum(float(n.get("montant_ttc",0)) for n in notes)
        total_tva_col = sum(float(f.get("tva",0)) for f in factures)
        capitaux      = total_actif - total_passif

        col_a, col_p = st.columns(2)
        with col_a:
            st.markdown("""
            <div class="module-card">
                <div class="module-header">
                    <div class="module-icon">📤</div>
                    <div><div class="module-title">ACTIF</div>
                         <div class="module-sub">Ce que vous possédez</div></div>
                </div>
            """, unsafe_allow_html=True)
            actif_items = [
                ("Créances clients (TTC)", total_actif),
                ("TVA déductible", total_tva_col * 0.3),
            ]
            for label, val in actif_items:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.7rem 0;
                     border-bottom:1px solid rgba(240,160,112,0.1);">
                    <span style="color:#a0522d;">{label}</span>
                    <b style="color:#68d391;">{val:,.2f} €</b>
                </div>
                """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:0.8rem 0;
                 background:rgba(240,160,112,0.08);border-radius:10px;margin-top:0.5rem;padding:0.8rem;">
                <b style="color:#a0522d;">TOTAL ACTIF</b>
                <b style="color:#68d391;font-size:1.1rem;">{total_actif:,.2f} €</b>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_p:
            st.markdown("""
            <div class="module-card">
                <div class="module-header">
                    <div class="module-icon">📥</div>
                    <div><div class="module-title">PASSIF</div>
                         <div class="module-sub">Ce que vous devez</div></div>
                </div>
            """, unsafe_allow_html=True)
            passif_items = [
                ("Dettes fournisseurs", total_passif),
                ("TVA collectée", total_tva_col),
                ("Capitaux propres", max(0, capitaux)),
            ]
            for label, val in passif_items:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.7rem 0;
                     border-bottom:1px solid rgba(240,160,112,0.1);">
                    <span style="color:#a0522d;">{label}</span>
                    <b style="color:#fc8181;">{val:,.2f} €</b>
                </div>
                """, unsafe_allow_html=True)
            total_passif_display = total_passif + total_tva_col + max(0, capitaux)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
                 background:rgba(240,160,112,0.08);border-radius:10px;margin-top:0.5rem;padding:0.8rem;">
                <b style="color:#a0522d;">TOTAL PASSIF</b>
                <b style="color:#fc8181;font-size:1.1rem;">{total_passif_display:,.2f} €</b>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Graphique bilan
        fig_bilan = go.Figure(go.Bar(
            x=["Créances clients","Notes de frais","TVA collectée","Résultat net"],
            y=[total_actif, total_passif, total_tva_col, max(0, capitaux)],
            marker_color=["#68d391","#fc8181","#b794f4","#f6ad55"],
            text=[f"{v:,.0f} €" for v in [total_actif,total_passif,total_tva_col,max(0,capitaux)]],
            textposition="outside"
        ))
        fig_bilan.update_layout(
            title="Synthèse du bilan", height=320,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#a0522d"),
            margin=dict(t=40,b=20,l=20,r=20),
            yaxis=dict(showgrid=True, gridcolor="rgba(240,160,112,0.1)", ticksuffix=" €"),
            showlegend=False
        )
        st.plotly_chart(fig_bilan, use_container_width=True)

    # ── TVA ──────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        tva_collectee  = sum(float(f.get("tva",0)) for f in factures)
        tva_deductible = sum(float(n.get("montant_ttc",0)) * (float(n.get("taux_tva",20)) / (100+float(n.get("taux_tva",20)))) for n in notes)
        tva_due        = tva_collectee - tva_deductible

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="kpi-card">
            <div class="kpi-icon">📤</div>
            <div class="kpi-value" style="color:#fc8181;">{tva_collectee:,.2f} €</div>
            <div class="kpi-label">TVA collectée</div>
            <div class="kpi-delta" style="color:#c8956c;">Sur ventes clients</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="kpi-card">
            <div class="kpi-icon">📥</div>
            <div class="kpi-value" style="color:#68d391;">{tva_deductible:,.2f} €</div>
            <div class="kpi-label">TVA déductible</div>
            <div class="kpi-delta" style="color:#c8956c;">Sur achats / frais</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            col_tva = "#fc8181" if tva_due > 0 else "#68d391"
            label_tva = "À payer à l'État" if tva_due > 0 else "Crédit de TVA"
            st.markdown(f"""<div class="kpi-card">
            <div class="kpi-icon">🏛️</div>
            <div class="kpi-value" style="color:{col_tva};">{abs(tva_due):,.2f} €</div>
            <div class="kpi-label">TVA nette due</div>
            <div class="kpi-delta" style="color:{col_tva};">{label_tva}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # TVA par mois
        if factures:
            df_tva = pd.DataFrame(factures)
            df_tva["date"] = pd.to_datetime(df_tva["date"], errors="coerce")
            df_tva["mois"] = df_tva["date"].dt.strftime("%Y-%m")
            df_tva["tva"]  = pd.to_numeric(df_tva["tva"], errors="coerce").fillna(0)
            monthly_tva = df_tva.groupby("mois")["tva"].sum().reset_index()

            fig_tva = px.bar(monthly_tva, x="mois", y="tva",
                             title="TVA collectée par mois",
                             color_discrete_sequence=["#b794f4"])
            fig_tva.update_layout(
                height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#a0522d"),
                margin=dict(t=40,b=20,l=20,r=20),
                yaxis=dict(showgrid=True, gridcolor="rgba(240,160,112,0.1)", ticksuffix=" €"),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_tva, use_container_width=True)

    # ── Alertes ──────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        alertes = []
        today = datetime.now().date()

        for f in factures:
            statut = str(f.get("statut",""))
            if "payer" in statut.lower() and "payée" not in statut.lower():
                try:
                    d = datetime.strptime(str(f.get("date","")), "%Y-%m-%d").date()
                    diff = (today - d).days
                    if diff > 30:
                        alertes.append({
                            "type": "🔴 Urgent",
                            "message": f"Facture {f.get('fournisseur','—')} en retard de {diff} jours",
                            "montant": float(f.get("montant_ttc",0)),
                            "niveau": "danger"
                        })
                    elif diff > 15:
                        alertes.append({
                            "type": "🟡 Attention",
                            "message": f"Facture {f.get('fournisseur','—')} à relancer ({diff}j)",
                            "montant": float(f.get("montant_ttc",0)),
                            "niveau": "warning"
                        })
                except: pass

        if tva_collectee > 0:
            alertes.append({
                "type": "🏛️ TVA",
                "message": f"TVA à déclarer : {tva_collectee:,.2f} € collectée",
                "montant": tva_collectee,
                "niveau": "info"
            })

        if len(factures) > 0:
            non_categ = [f for f in factures if f.get("categorie","") in ["Autres","","Non détecté"]]
            if non_categ:
                alertes.append({
                    "type": "📂 Catégorie",
                    "message": f"{len(non_categ)} facture(s) sans catégorie précise",
                    "montant": 0,
                    "niveau": "warning"
                })

        if alertes:
            for a in alertes:
                colors = {
                    "danger":  ("rgba(252,129,129,0.1)","#c53030","#fc8181"),
                    "warning": ("rgba(246,173,85,0.1)","#c05621","#f6ad55"),
                    "info":    ("rgba(99,179,237,0.1)","#2b6cb0","#63b3ed")
                }
                bg, text, border = colors.get(a["niveau"], colors["info"])
                montant_str = f" · {a['montant']:,.2f} €" if a["montant"] > 0 else ""
                st.markdown(f"""
                <div style="background:{bg};border-left:4px solid {border};
                     border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.8rem;
                     display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:700;color:{text};">{a['type']}</span>
                        <br><span style="color:{text};opacity:0.8;font-size:0.9rem;">{a['message']}</span>
                    </div>
                    <div style="font-weight:700;color:{text};font-size:1.1rem;">{montant_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem;background:rgba(104,211,145,0.1);
                 border-radius:20px;border:2px solid rgba(104,211,145,0.3);">
                <div style="font-size:3rem;">✅</div>
                <h3 style="color:#276749;">Tout est en ordre !</h3>
                <p style="color:#68d391;">Aucune alerte comptable</p>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FACTURES avec APERÇU
# ═══════════════════════════════════════════════════════════════════════════════

def hero(icon, title, subtitle):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">{icon} {title}</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def show_factures():
    hero("📄", "Gestion des Factures", "Import, analyse IA et prévisualisation 🔍")
    ...


    if "resultats" not in st.session_state:
        st.session_state["resultats"] = []
    if "current_preview" not in st.session_state:
        st.session_state["current_preview"] = None
    if "current_preview_name" not in st.session_state:
        st.session_state["current_preview_name"] = ""

    tab1, tab2, tab3 = st.tabs(["📤 Import & Analyse", "📋 Liste & Aperçu", "📊 Export"])

    # ── Import ───────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Layout : upload à gauche, preview à droite
        col_upload, col_preview = st.columns([1, 1])

        with col_upload:
            uploaded_files = st.file_uploader(
                "Glissez vos factures (PDF ou image)",
                type=["pdf","png","jpg","jpeg"],
                accept_multiple_files=True,
                key="facture_uploader"
            )

            if uploaded_files:
                # Dédoublonnage
                existing_names = {r.get("fichier","") for r in get_data("factures")}
                new_files = [f for f in uploaded_files if f.name not in existing_names]
                already   = [f for f in uploaded_files if f.name in existing_names]

                if already:
                    st.warning(f"⚠️ {len(already)} fichier(s) déjà importé(s) ignoré(s)")

                if new_files:
                    st.markdown(f"""
                    <div style="background:#fff8f0;border-radius:14px;padding:0.8rem 1.2rem;
                         border:2px solid rgba(240,160,112,0.3);margin:0.5rem 0;">
                        <span style="color:#a0522d;font-weight:600;">
                            📁 {len(new_files)} nouveau(x) fichier(s)
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sélecteur de prévisualisation avant analyse
                    names = [f.name for f in new_files]
                    selected_preview = st.selectbox("👁️ Prévisualiser", names, key="select_preview")

                    for f in new_files:
                        if f.name == selected_preview:
                            content = f.read()
                            f.seek(0)
                            if f.name.lower().endswith(".pdf"):
                                imgs = pdf_to_images(content)
                                st.session_state["current_preview"] = imgs
                            else:
                                img = Image.open(io.BytesIO(content))
                                st.session_state["current_preview"] = [img]
                            st.session_state["current_preview_name"] = f.name

                    if st.button("🔍 Analyser avec Gemini 2.5",
                                 use_container_width=True, key="btn_analyser"):
                        model = configure_gemini()
                        if not model:
                            st.error("❌ Clé API Gemini manquante")
                        else:
                            progress = st.progress(0)
                            status   = st.empty()
                            for i, f in enumerate(new_files):
                                status.markdown(f"""
                                <div style="background:#fff8f0;border-radius:12px;padding:0.8rem;
                                     border-left:4px solid #f0a070;">
                                    🔍 Analyse : <b>{f.name}</b>…
                                </div>
                                """, unsafe_allow_html=True)
                                content = f.read()
                                images  = pdf_to_images(content) if f.name.lower().endswith(".pdf") \
                                          else [Image.open(io.BytesIO(content))]
                                result  = extraire_facture(model, images)
                                result["fichier"] = f.name

                                # Sauvegarde préview
                                if f.name == st.session_state.get("current_preview_name",""):
                                    st.session_state["current_preview"] = images

                                try:
                                    supabase = get_supabase()
                                    uid = st.session_state.get("user_id","")
                                    supabase.table("factures").insert({**result,"user_id":uid}).execute()
                                except:
                                    st.session_state["resultats"].append(result)

                                progress.progress((i+1)/len(new_files))
                            status.success(f"✅ {len(new_files)} facture(s) analysée(s) !")
                            st.rerun()

        # ── Preview droite ──
        with col_preview:
            st.markdown("""
            <div class="invoice-viewer">
                <div class="invoice-viewer-header">
                    <span class="invoice-viewer-title">👁️ Aperçu de la facture</span>
                </div>
            """, unsafe_allow_html=True)

            if st.session_state.get("current_preview"):
                imgs = st.session_state["current_preview"]
                fname = st.session_state.get("current_preview_name","")

                st.markdown(f"""
                <div style="background:rgba(240,160,112,0.08);border-radius:10px;
                     padding:0.5rem 1rem;margin-bottom:0.8rem;font-size:0.82rem;
                     color:#a0522d;font-weight:600;">
                    📄 {fname}  ·  {len(imgs)} page(s)
                </div>
                """, unsafe_allow_html=True)

                if len(imgs) > 1:
                    page_idx = st.slider("Page", 1, len(imgs), 1, key="preview_page") - 1
                    st.image(imgs[page_idx], use_column_width=True)
                else:
                    st.image(imgs[0], use_column_width=True)

                # Zoom toggle
                if st.button("🔍 Agrandir", key="zoom_btn", use_container_width=True):
                    st.session_state["zoom_preview"] = not st.session_state.get("zoom_preview", False)

                if st.session_state.get("zoom_preview", False):
                    with st.expander("🔍 Vue agrandie", expanded=True):
                        for img in imgs:
                            st.image(img, use_column_width=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:4rem 2rem;">
                    <div style="font-size:4rem;margin-bottom:1rem;">📄</div>
                    <p style="color:#c8956c;font-weight:600;">Sélectionnez un fichier</p>
                    <p style="color:#d4a882;font-size:0.85rem;">
                        L'aperçu apparaîtra ici
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Liste & Aperçu ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        factures = get_data("factures")

        if factures:
            # Filtres
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                search = st.text_input("🔍 Rechercher", key="fact_search")
            with col_f2:
                cats = ["Toutes"] + sorted(set(f.get("categorie","") for f in factures))
                cat_filter = st.selectbox("📂 Catégorie", cats, key="fact_cat")
            with col_f3:
                statuts = ["Tous"] + sorted(set(f.get("statut","") for f in factures))
                stat_filter = st.selectbox("🏷️ Statut", statuts, key="fact_stat")
            with col_f4:
                sort_by = st.selectbox("↕️ Trier par", ["Date ↓","Date ↑","Montant ↓","Montant ↑"], key="fact_sort")

            filtered = [f for f in factures
                        if (not search or search.lower() in str(f.get("fournisseur","")).lower())
                        and (cat_filter == "Toutes" or f.get("categorie") == cat_filter)
                        and (stat_filter == "Tous" or f.get("statut") == stat_filter)]

            if sort_by == "Date ↓":
                filtered.sort(key=lambda x: str(x.get("date","")), reverse=True)
            elif sort_by == "Date ↑":
                filtered.sort(key=lambda x: str(x.get("date","")))
            elif sort_by == "Montant ↓":
                filtered.sort(key=lambda x: float(x.get("montant_ttc",0)), reverse=True)
            else:
                filtered.sort(key=lambda x: float(x.get("montant_ttc",0)))

            st.markdown(f"<p style='color:#c8956c;font-size:0.85rem;margin-bottom:1rem;'>"
                        f"<b>{len(filtered)}</b> résultat(s)</p>", unsafe_allow_html=True)

            # Layout liste + preview
            col_list, col_view = st.columns([1, 1])

            with col_list:
                for idx, r in enumerate(filtered):
                    statut = r.get("statut","À payer")
                    badge_color = "#68d391" if "Payée" in statut else (
                        "#fc8181" if "retard" in statut.lower() else "#f6ad55")
                    ttc = float(r.get("montant_ttc",0))

                    selected = st.session_state.get("selected_facture_idx") == idx

                    if st.button(
                        f"{'▶' if selected else '○'}  {r.get('fournisseur','—')[:22]}  ·  "
                        f"{r.get('date','—')}  ·  {ttc:.2f} €",
                        key=f"sel_fact_{idx}",
                        use_container_width=True,
                        type="primary" if selected else "secondary"
                    ):
                        st.session_state["selected_facture_idx"] = idx
                        st.rerun()

            with col_view:
                sel_idx = st.session_state.get("selected_facture_idx")
                if sel_idx is not None and sel_idx < len(filtered):
                    r = filtered[sel_idx]
                    st.markdown(f"""
                    <div class="invoice-viewer">
                        <div class="invoice-viewer-header">
                            <span class="invoice-viewer-title">
                                📄 {r.get('fournisseur','—')}
                            </span>
                            <span style="font-size:0.8rem;color:#c8956c;">
                                {r.get('date','—')}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                    # Détails
                    fields = [
                        ("🏢 Fournisseur", r.get("fournisseur","—")),
                        ("🔢 N° Facture",  r.get("numero","—")),
                        ("📅 Date",         r.get("date","—")),
                        ("📂 Catégorie",    r.get("categorie","—")),
                        ("💵 Montant HT",   f"{float(r.get('montant_ht',0)):.2f} €"),
                        ("📊 TVA",          f"{float(r.get('tva',0)):.2f} €"),
                        ("💰 Montant TTC",  f"{float(r.get('montant_ttc',0)):.2f} €"),
                        ("🏷️ Statut",       r.get("statut","—")),
                    ]
                    for label, val in fields:
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                             padding:0.5rem 0;border-bottom:1px solid rgba(240,160,112,0.1);">
                            <span style="color:#c8956c;font-size:0.85rem;">{label}</span>
                            <b style="color:#
                                                        <b style="color:#a0522d;font-size:0.85rem;">{val}</b>
                        </div>
                        """, unsafe_allow_html=True)

                    # Montants en cards
                    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    for col_m, label, key, color in [
                        (m1, "💵 HT",  "montant_ht",  "#68d391"),
                        (m2, "📊 TVA", "tva",         "#b794f4"),
                        (m3, "💰 TTC", "montant_ttc", "#f0a070"),
                    ]:
                        with col_m:
                            st.markdown(f"""
                            <div style="background:rgba(240,160,112,0.08);border-radius:12px;
                                 padding:0.8rem;text-align:center;
                                 border:1px solid rgba(240,160,112,0.2);">
                                <div style="font-size:0.75rem;color:#c8956c;font-weight:600;">{label}</div>
                                <div style="font-size:1.1rem;font-weight:800;color:{color};">
                                    {float(r.get(key,0)):.2f} €
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

                    # Actions
                    a1, a2, a3 = st.columns(3)
                    with a1:
                        new_statut = st.selectbox("Statut",
                            ["À payer","Payée","En retard","Annulée"],
                            index=["À payer","Payée","En retard","Annulée"].index(
                                r.get("statut","À payer"))
                            if r.get("statut","À payer") in ["À payer","Payée","En retard","Annulée"] else 0,
                            key=f"statut_{sel_idx}")
                    with a2:
                        if st.button("💾 Enregistrer", key=f"save_{sel_idx}", use_container_width=True):
                            try:
                                get_supabase().table("factures").update(
                                    {"statut": new_statut}
                                ).eq("id", r["id"]).execute()
                                st.success("✅ Statut mis à jour")
                                st.rerun()
                            except:
                                r["statut"] = new_statut
                                st.success("✅ Mis à jour localement")
                    with a3:
                        if st.button("🗑️ Supprimer", key=f"del_{sel_idx}", use_container_width=True):
                            try:
                                get_supabase().table("factures").delete().eq("id", r["id"]).execute()
                                st.session_state["selected_facture_idx"] = None
                                st.rerun()
                            except:
                                st.error("❌ Erreur suppression")

                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="invoice-viewer" style="text-align:center;padding:4rem 2rem;">
                        <div style="font-size:4rem;">👈</div>
                        <p style="color:#c8956c;font-weight:600;">
                            Sélectionnez une facture
                        </p>
                        <p style="color:#d4a882;font-size:0.85rem;">
                            Cliquez sur une facture pour voir son détail
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;border-radius:24px;
                 border:2px dashed rgba(240,160,112,0.3);">
                <div style="font-size:4rem;">📭</div>
                <h3 style="color:#a0522d;">Aucune facture</h3>
                <p style="color:#c8956c;">Importez vos premières factures dans l'onglet Import</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Export ───────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        factures = get_data("factures")
        if factures:
            df_exp = pd.DataFrame(factures)
            st.dataframe(df_exp, use_container_width=True, hide_index=True)
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            with e1:
                csv = df_exp.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Télécharger CSV",
                    data=csv, file_name="factures.csv", mime="text/csv",
                    use_container_width=True)
            with e2:
                json_data = json.dumps(factures, ensure_ascii=False, indent=2)
                st.download_button("📥 Télécharger JSON",
                    data=json_data, file_name="factures.json", mime="application/json",
                    use_container_width=True)
        else:
            st.info("📭 Aucune facture à exporter")


# ═══════════════════════════════════════════════════════════════════════════════
# NOTES DE FRAIS
# ═══════════════════════════════════════════════════════════════════════════════
def show_notes_frais():
    hero("🧾", "Notes de Frais", "Gérez et remboursez vos dépenses professionnelles")

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    tab1, tab2 = st.tabs(["➕ Nouvelle note", "📋 Mes notes"])

    with tab1:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        col_form, col_prev = st.columns([1, 1])

        with col_form:
            st.markdown('<div class="module-card">', unsafe_allow_html=True)
            st.markdown("""
            <div class="module-header">
                <div class="module-icon">➕</div>
                <div><div class="module-title">Nouvelle note de frais</div>
                     <div class="module-sub">Saisie manuelle ou par IA</div></div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_note = st.file_uploader(
                "Justificatif (optionnel)", type=["pdf","png","jpg","jpeg"],
                key="note_uploader")

            n1, n2 = st.columns(2)
            with n1: nom        = st.text_input("👤 Employé", key="note_nom")
            with n2: date_note  = st.date_input("📅 Date", key="note_date")
            n3, n4 = st.columns(2)
            with n3:
                cat_note = st.selectbox("📂 Catégorie",
                    ["Transport","Repas","Hébergement","Fournitures","Téléphone","Autres"],
                    key="note_cat")
            with n4: montant_note = st.number_input("💰 Montant TTC (€)", min_value=0.0, step=0.01, key="note_montant")
            n5, n6 = st.columns(2)
            with n5:
                tva_note = st.selectbox("📊 Taux TVA", [0, 5.5, 10, 20], index=3, key="note_tva")
            with n6:
                statut_note = st.selectbox("🏷️ Statut",
                    ["À rembourser","Remboursée","En attente"], key="note_statut")
            desc_note = st.text_area("📝 Description", key="note_desc", height=80)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if uploaded_note and st.button("🤖 Analyser IA", key="note_ia", use_container_width=True):
                    model = configure_gemini()
                    if model:
                        content = uploaded_note.read()
                        images  = pdf_to_images(content) if uploaded_note.name.lower().endswith(".pdf") \
                                  else [Image.open(io.BytesIO(content))]
                        result  = extraire_facture(model, images)
                        st.session_state["note_ia_result"] = result
                        st.success(f"✅ Détecté : {result.get('fournisseur','—')} · {result.get('montant_ttc',0)} €")

            with btn_col2:
                if st.button("💾 Enregistrer", key="save_note", use_container_width=True):
                    ia = st.session_state.get("note_ia_result", {})
                    note = {
                        "employe":     nom or ia.get("fournisseur","—"),
                        "date":        str(date_note),
                        "categorie":   cat_note,
                        "montant_ttc": montant_note or float(ia.get("montant_ttc",0)),
                        "taux_tva":    tva_note,
                        "statut":      statut_note,
                        "description": desc_note,
                        "fichier":     uploaded_note.name if uploaded_note else ""
                    }
                    try:
                        uid = st.session_state.get("user_id","")
                        get_supabase().table("notes_frais").insert({**note,"user_id":uid}).execute()
                        st.success("✅ Note enregistrée dans Supabase !")
                    except:
                        st.session_state["notes_frais"].append(note)
                        st.success("✅ Note enregistrée localement !")
                    st.session_state.pop("note_ia_result", None)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with col_prev:
            st.markdown("""
            <div class="invoice-viewer">
                <div class="invoice-viewer-header">
                    <span class="invoice-viewer-title">👁️ Aperçu justificatif</span>
                </div>
            """, unsafe_allow_html=True)

            if uploaded_note:
                content = uploaded_note.read()
                uploaded_note.seek(0)
                if uploaded_note.name.lower().endswith(".pdf"):
                    imgs = pdf_to_images(content)
                else:
                    imgs = [Image.open(io.BytesIO(content))]
                if len(imgs) > 1:
                    pg = st.slider("Page", 1, len(imgs), 1, key="note_page") - 1
                    st.image(imgs[pg], use_column_width=True)
                else:
                    st.image(imgs[0], use_column_width=True)

                if st.session_state.get("note_ia_result"):
                    ia = st.session_state["note_ia_result"]
                    st.markdown(f"""
                    <div style="background:rgba(104,211,145,0.1);border-radius:12px;
                         padding:1rem;margin-top:1rem;border:1px solid rgba(104,211,145,0.3);">
                        <b style="color:#276749;">✅ Résultat IA</b><br>
                        <span style="color:#2f855a;font-size:0.85rem;">
                            {ia.get('fournisseur','—')} · {ia.get('date','—')} ·
                            <b>{float(ia.get('montant_ttc',0)):.2f} €</b>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:4rem 2rem;">
                    <div style="font-size:4rem;">🧾</div>
                    <p style="color:#c8956c;font-weight:600;">
                        Uploadez un justificatif
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        notes = get_data("notes_frais")

        if notes:
            # KPIs rapides
            total_n = sum(float(n.get("montant_ttc",0)) for n in notes)
            a_rembourser = sum(float(n.get("montant_ttc",0)) for n in notes if "rembourser" in str(n.get("statut","")).lower())
            remboursees  = sum(float(n.get("montant_ttc",0)) for n in notes if "Remboursée" in str(n.get("statut","")))

            k1, k2, k3 = st.columns(3)
            for col, icon, val, label, color in [
                (k1, "💸", f"{total_n:,.2f} €",        "Total dépenses",   "#f0a070"),
                (k2, "⏳", f"{a_rembourser:,.2f} €",   "À rembourser",     "#f6ad55"),
                (k3, "✅", f"{remboursees:,.2f} €",    "Remboursées",      "#68d391"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-icon">{icon}</div>
                        <div class="kpi-value" style="color:{color};">{val}</div>
                        <div class="kpi-label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            df_notes = pd.DataFrame(notes)
            cols_show = [c for c in ["employe","date","categorie","montant_ttc","statut","description"] if c in df_notes.columns]
            st.dataframe(df_notes[cols_show], use_container_width=True, hide_index=True)

            csv_n = df_notes.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Exporter CSV", data=csv_n,
                file_name="notes_frais.csv", mime="text/csv", use_container_width=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem;background:white;border-radius:24px;
                 border:2px dashed rgba(240,160,112,0.3);">
                <div style="font-size:4rem;">📭</div>
                <h3 style="color:#a0522d;">Aucune note de frais</h3>
                <p style="color:#c8956c;">Ajoutez votre première note dans l'onglet Nouvelle note</p>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ASSISTANT IA
# ═══════════════════════════════════════════════════════════════════════════════
def show_assistant():
    hero("🤖", "Assistant IA", "Votre comptable intelligent propulsé par Gemini 2.5 Flash 🐱")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    factures_data = get_data("factures")
    notes_data    = get_data("notes_frais")

    # Suggestions rapides
    st.markdown("""
    <div style="margin-bottom:1rem;">
        <p style="color:#c8956c;font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;">
            💡 Questions rapides :
        </p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        "📊 Résume mes finances",
        "💸 TVA à déclarer ?",
        "⚠️ Factures en retard ?",
        "📈 Meilleur mois ?",
        "🏆 Top fournisseurs",
    ]
    s_cols = st.columns(len(suggestions))
    for i, (col, sug) in enumerate(zip(s_cols, suggestions)):
        with col:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state["chat_messages"].append({"role":"user","content":sug})
                model = configure_gemini()
                if model:
                    context = f"""Tu es FactureCat 🐱👓, assistant comptable expert.
Factures : {json.dumps(factures_data, ensure_ascii=False)}
Notes : {json.dumps(notes_data, ensure_ascii=False)}
Réponds en français, de façon claire et professionnelle.
Question : {sug}"""
                    try:
                        resp = model.generate_content(context)
                        st.session_state["chat_messages"].append(
                            {"role":"assistant","content":resp.text})
                    except Exception as e:
                        st.session_state["chat_messages"].append(
                            {"role":"assistant","content":f"❌ {e}"})
                st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Historique chat
    if not st.session_state["chat_messages"]:
        st.markdown("""
        <div style="text-align:center;padding:3rem;background:white;border-radius:24px;
             border:2px dashed rgba(240,160,112,0.3);">
            <div style="font-size:4rem;">🐱👓</div>
            <h3 style="color:#a0522d;">Bonjour ! Je suis FactureCat</h3>
            <p style="color:#c8956c;">
                Posez-moi des questions sur vos factures, notes de frais, TVA…
            </p>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state["chat_messages"]:
        align = "flex-end"  if msg["role"] == "user" else "flex-start"
        bg    = "linear-gradient(135deg,#f0a070,#e8856a)" if msg["role"] == "user" else "white"
        color = "white" if msg["role"] == "user" else "#a0522d"
        icon  = "👤" if msg["role"] == "user" else "🐱👓"
        border = "none" if msg["role"] == "user" else "1px solid rgba(240,160,112,0.2)"
        st.markdown(f"""
        <div style="display:flex;justify-content:{align};margin:0.6rem 0;">
            <div style="background:{bg};color:{color};padding:1rem 1.2rem;
                 border-radius:20px;max-width:75%;
                 box-shadow:0 4px 16px rgba(240,160,112,0.15);
                 border:{border};font-size:0.9rem;line-height:1.5;">
                <span style="opacity:0.6;font-size:0.75rem;">{icon}</span><br>
                {msg['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Posez votre question à FactureCat 🐾")
    if user_input:
        st.session_state["chat_messages"].append({"role":"user","content":user_input})
        model = configure_gemini()
        if model:
            context = f"""Tu es FactureCat 🐱👓, assistant comptable expert et sympathique.
Factures disponibles : {json.dumps(factures_data, ensure_ascii=False)}
Notes de frais : {json.dumps(notes_data, ensure_ascii=False)}
Réponds en français, de manière claire, structurée et professionnelle.
Question : {user_input}"""
            try:
                resp = model.generate_content(context)
                answer = resp.text
            except Exception as e:
                answer = f"❌ Erreur : {e}"
        else:
            answer = "❌ Clé API Gemini manquante dans les secrets"
        st.session_state["chat_messages"].append({"role":"assistant","content":answer})
        st.rerun()

    # Bouton vider
    if st.session_state["chat_messages"]:
        if st.button("🗑️ Vider la conversation", key="clear_chat"):
            st.session_state["chat_messages"] = []
            st.rerun()

def render_cat_widget():
    import random
    import streamlit.components.v1 as components
    msg = random.choice(["Miaou ! 📄","Facture prête !","Tout est OK ! ✅","Je veille sur vos factures 🐾"])
    components.html(f"""
    <div style="position:fixed;bottom:20px;right:20px;z-index:9999;
         font-family:Inter,sans-serif;">
        <div id="bubble" style="position:absolute;bottom:60px;right:0;
             background:white;border:2px solid #f0a070;border-radius:16px 16px 4px 16px;
             padding:0.5rem 0.8rem;font-size:0.75rem;color:#c8956c;font-weight:600;
             white-space:nowrap;opacity:0;transition:all 0.3s;
             box-shadow:0 4px 12px rgba(200,149,108,0.2);">{msg}</div>
        <div style="font-size:2.5rem;cursor:pointer;transition:transform 0.2s;"
             onmouseover="document.getElementById('bubble').style.opacity='1';
                          this.style.transform='scale(1.2) rotate(-10deg)'"
             onmouseout="document.getElementById('bubble').style.opacity='0';
                         this.style.transform='scale(1)'">🐱</div>
    </div>
    <style>
    @keyframes cat-bounce {{
        0%,100% {{ transform:translateY(0); }}
        50%      {{ transform:translateY(-8px); }}
    }}
    </style>
    """, height=80)


def cat_progress_bar(value: float, label: str = ""):
    pct = int(value * 100)
    st.markdown(f"""
    {f'<div style="font-size:0.8rem;color:#c8956c;font-weight:600;margin-bottom:4px;">{label}</div>' if label else ''}
    <div style="position:relative;background:rgba(240,160,112,0.1);
         border-radius:20px;height:28px;margin:0.5rem 0;
         border:1px solid rgba(240,160,112,0.3);overflow:visible;">
        <div style="width:{pct}%;height:100%;border-radius:20px;
             background:linear-gradient(90deg,#f0c090,#f0a070);"></div>
        <span style="position:absolute;top:-8px;left:{max(pct-2,1)}%;
              font-size:1.4rem;transform:translateX(-50%);">🐱</span>
        <span style="position:absolute;right:8px;top:50%;
              transform:translateY(-50%);font-size:0.75rem;
              color:#c8956c;font-weight:700;">{pct}%</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
         justify-content:center;min-height:90vh;">
        <div style="background:white;border-radius:28px;padding:3rem;width:100%;max-width:420px;
             box-shadow:0 20px 60px rgba(240,160,112,0.2);
             border:1px solid rgba(240,160,112,0.15);">
            <div style="text-align:center;margin-bottom:2rem;">
                <div style="font-size:4rem;animation:float 3s ease-in-out infinite;">🐱</div>
                <h1 style="background:linear-gradient(135deg,#f0a070,#e8856a);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    font-size:2rem;font-weight:800;margin:0.5rem 0;">FactureCat</h1>
                <p style="color:#c8956c;margin:0;">Gestion comptable intelligente</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        mode = st.radio("", ["🔐 Connexion", "📝 Inscription"],
                        horizontal=True, key="login_mode")
        email = st.text_input("📧 Email", key="login_email")
        pwd   = st.text_input("🔑 Mot de passe", type="password", key="login_pwd")

        if mode == "🔐 Connexion":
            if st.button("🚀 Se connecter", use_container_width=True):
                try:
                    supabase = get_supabase()
                    resp = supabase.auth.sign_in_with_password({"email":email,"password":pwd})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = email
                    st.session_state["user_id"]       = resp.user.id
                    st.session_state["page"]          = "🏠 Dashboard"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            if st.button("✨ S'inscrire", use_container_width=True):
                try:
                    supabase = get_supabase()
                    resp = supabase.auth.sign_up({"email":email,"password":pwd})
                    st.success("✅ Compte créé ! Vérifiez votre email.")
                except Exception as e:
                    st.error(f"❌ {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "🏠 Dashboard"
    if "selected_facture_idx" not in st.session_state:
        st.session_state["selected_facture_idx"] = None

    if not st.session_state["authenticated"]:
        show_login()
        return

    render_cat_widget()  # ← AJOUTEZ CETTE LIGNE ICI

    current_page = st.session_state.get("page", "🏠 Dashboard")
    render_topnav(current_page)

    if current_page == "🏠 Dashboard":
        show_dashboard()
    elif current_page == "📄 Factures":
        show_factures()
    elif current_page == "🧾 Notes de frais":
        show_notes_frais()
    elif current_page == "📊 Comptabilité":
        show_comptabilite()
    elif current_page == "🤖 Assistant IA":
        show_assistant()

if __name__ == "__main__":
    main()


