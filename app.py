import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═══════════════════════════════════════════════════════════════════════════════
from supabase import create_client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# ═══════════════════════════════════════════════════════════════════════════════
# GEMINI — clé directe GEMINI_API_KEY
# ═══════════════════════════════════════════════════════════════════════════════
def configure_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = ""
        st.session_state["user_id"] = ""
        try:
            supabase = get_supabase()
            session = supabase.auth.get_session()
            if session and session.user:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = session.user.email
                st.session_state["user_id"] = session.user.id
        except:
            pass

    if st.session_state["authenticated"]:
        return True

    st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #fff8f0 0%, #fdf0e8 100%); }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:3rem 0 2rem;">
            <div style="font-size:5rem;">🐱</div>
            <h1 style="color:#a0522d; margin:0;">FactureCat</h1>
            <p style="color:#c8956c;">Gestion comptable intelligente 🐾</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email    = st.text_input("📧 Email", placeholder="votre@email.com")
            password = st.text_input("🔑 Mot de passe", type="password")
            submit   = st.form_submit_button("🚀 Se connecter", use_container_width=True)

            if submit:
                try:
                    supabase = get_supabase()
                    res = supabase.auth.sign_in_with_password({
                        "email": email, "password": password
                    })
                    if res.user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"]    = res.user.email
                        st.session_state["user_id"]       = res.user.id
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# UTILS PDF
# ═══════════════════════════════════════════════════════════════════════════════
def pdf_to_images(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    imgs = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return imgs

def extraire_facture(model, images):
    prompt = """
Analyse cette facture et extrais les informations suivantes en JSON :
{
  "fournisseur": "nom du fournisseur",
  "numero": "numéro de facture",
  "date": "date au format YYYY-MM-DD",
  "montant_ht": valeur numérique,
  "tva": valeur numérique,
  "montant_ttc": valeur numérique,
  "categorie": "catégorie (Informatique/Transport/Repas/Fournitures/Services/Autres)",
  "statut": "À payer"
}
Réponds UNIQUEMENT avec le JSON, sans markdown.
"""
    try:
        response = model.generate_content([prompt] + images)
        text     = response.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except:
        return {
            "fournisseur": "Non détecté",
            "numero":      "—",
            "date":        str(datetime.now().date()),
            "montant_ht":  0,
            "tva":         0,
            "montant_ttc": 0,
            "categorie":   "Autres",
            "statut":      "À payer"
        }

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #fff8f0 0%, #fdf0e8 100%) !important; }
    .card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(240,160,112,0.15);
        border: 1px solid rgba(240,160,112,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(240,160,112,0.25);
    }
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        border: 2px solid rgba(240,160,112,0.2);
        box-shadow: 0 4px 15px rgba(240,160,112,0.1);
        margin-bottom: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #f0a070, #e8856a) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(240,160,112,0.4) !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 12px !important;
        border: 2px solid rgba(240,160,112,0.3) !important;
        background: white !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff8f0 0%, #fdf0e8 100%) !important;
        border-right: 2px solid rgba(240,160,112,0.3) !important;
    }

    /* ── Widget flottant IA ── */
    #chat-fab {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 9999;
    }
    #chat-fab button {
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        font-size: 1.6rem !important;
        padding: 0 !important;
        box-shadow: 0 6px 24px rgba(240,160,112,0.5) !important;
    }
    #chat-panel {
        position: fixed;
        bottom: 6rem;
        right: 2rem;
        width: 380px;
        max-height: 520px;
        background: white;
        border-radius: 24px;
        box-shadow: 0 12px 48px rgba(160,82,45,0.2);
        border: 2px solid rgba(240,160,112,0.4);
        z-index: 9998;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    #chat-header {
        background: linear-gradient(135deg,#f0a070,#e8856a);
        padding: 1rem 1.2rem;
        color: white;
        font-weight: 700;
        font-size: 1rem;
        border-radius: 22px 22px 0 0;
    }
    #chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        background: #fff8f0;
    }
    .msg-user {
        align-self: flex-end;
        background: #f0a070;
        color: white;
        padding: 0.6rem 1rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 85%;
        font-size: 0.88rem;
    }
    .msg-bot {
        align-self: flex-start;
        background: white;
        color: #a0522d;
        padding: 0.6rem 1rem;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        font-size: 0.88rem;
        border: 1px solid rgba(240,160,112,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET IA FLOTTANT (affiché sur toutes les pages sauf page IA)
# ═══════════════════════════════════════════════════════════════════════════════
def show_floating_chat():
    if "float_open" not in st.session_state:
        st.session_state["float_open"] = False
    if "float_messages" not in st.session_state:
        st.session_state["float_messages"] = [
            {"role":"assistant","content":"Bonjour ! Je suis FactureCat 🐱 Posez-moi vos questions comptables !"}
        ]

    # Bouton flottant
    col_fab = st.columns([10,1])[1]
    with col_fab:
        label = "✖️" if st.session_state["float_open"] else "🐱"
        if st.button(label, key="fab_btn"):
            st.session_state["float_open"] = not st.session_state["float_open"]

    if st.session_state["float_open"]:
        st.markdown("""
        <div id="chat-panel">
            <div id="chat-header">🐱 Assistant FactureCat</div>
            <div id="chat-messages">
        """, unsafe_allow_html=True)

        for msg in st.session_state["float_messages"]:
            css = "msg-user" if msg["role"] == "user" else "msg-bot"
            icon = "👤 " if msg["role"] == "user" else "🐱 "
            st.markdown(f'<div class="{css}">{icon}{msg["content"]}</div>',
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            col_in, col_send = st.columns([5,1])
            with col_in:
                user_msg = st.text_input("", placeholder="Votre question...",
                                         label_visibility="collapsed",
                                         key="float_input")
            with col_send:
                send = st.button("➤", key="float_send")

            if send and user_msg:
                st.session_state["float_messages"].append(
                    {"role":"user","content":user_msg}
                )
                model = configure_gemini()
                if model:
                    try:
                        supabase = get_supabase()
                        uid = st.session_state.get("user_id","")
                        factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
                        notes    = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
                    except:
                        factures = st.session_state.get("resultats",[])
                        notes    = st.session_state.get("notes_frais",[])

                    context = f"""
Tu es FactureCat 🐱, assistant comptable expert et sympa.
Factures : {json.dumps(factures, ensure_ascii=False)}
Notes de frais : {json.dumps(notes, ensure_ascii=False)}
Réponds en français, clair et concis.
Question : {user_msg}
"""
                    try:
                        answer = model.generate_content(context).text
                    except Exception as e:
                        answer = f"❌ Erreur : {e}"
                else:
                    answer = "❌ Clé API Gemini manquante"

                st.session_state["float_messages"].append(
                    {"role":"assistant","content":answer}
                )
                st.rerun()

            col_cl, _ = st.columns([1,3])
            with col_cl:
                if st.button("🗑️ Vider", key="float_clear"):
                    st.session_state["float_messages"] = [
                        {"role":"assistant","content":"Bonjour ! Je suis FactureCat 🐱 Posez-moi vos questions !"}
                    ]
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">🏠 Dashboard</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Vue d'ensemble de votre comptabilité 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        supabase = get_supabase()
        uid      = st.session_state.get("user_id","")
        factures = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        notes    = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
    except:
        factures = st.session_state.get("resultats",[])
        notes    = st.session_state.get("notes_frais",[])

    total_f_ht  = sum(float(r.get("montant_ht",  0)) for r in factures)
    total_f_tva = sum(float(r.get("tva",         0)) for r in factures)
    total_f_ttc = sum(float(r.get("montant_ttc", 0)) for r in factures)
    total_n_ht  = sum(float(n.get("montant_ht",  0)) for n in notes)
    total_n_ttc = sum(float(n.get("montant_ttc", 0)) for n in notes)

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "📄 Factures",       f"{len(factures)}",                  f"Total HT : {total_f_ht:.2f} €"),
        (col2, "💰 CA Factures",    f"{total_f_ttc:.2f} €",              f"TVA : {total_f_tva:.2f} €"),
        (col3, "🧾 Notes de frais", f"{len(notes)}",                     f"Total HT : {total_n_ht:.2f} €"),
        (col4, "💸 Total dépenses", f"{total_f_ttc+total_n_ttc:.2f} €", "TTC toutes dépenses"),
    ]
    for col, label, value, delta in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#c8956c;font-size:0.85rem;margin:0 0 0.5rem;
                   font-weight:600;text-transform:uppercase;">{label}</p>
                <p style="color:#a0522d;font-size:1.8rem;font-weight:700;margin:0;">{value}</p>
                <p style="color:#d4a882;font-size:0.8rem;margin:0.3rem 0 0;">{delta}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Graphiques
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div class="card">
            <h4 style="color:#a0522d;margin:0 0 1rem;">📊 Répartition par catégorie</h4>
        """, unsafe_allow_html=True)
        if factures:
            df_cat = pd.DataFrame(factures)
            if "categorie" in df_cat.columns and "montant_ttc" in df_cat.columns:
                df_cat["montant_ttc"] = pd.to_numeric(df_cat["montant_ttc"], errors="coerce").fillna(0)
                cat_data = df_cat.groupby("categorie")["montant_ttc"].sum()
                st.bar_chart(cat_data)
            else:
                st.markdown("<p style='color:#c8956c;text-align:center;'>Pas de données 🐱</p>",
                            unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#c8956c;text-align:center;'>Aucune facture 🐾</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="card">
            <h4 style="color:#a0522d;margin:0 0 1rem;">🧾 Dernières factures</h4>
        """, unsafe_allow_html=True)
        if factures:
            for r in factures[-5:][::-1]:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                     padding:0.5rem 0;border-bottom:1px solid rgba(240,160,112,0.2);">
                    <span style="color:#a0522d;font-weight:600;">
                        🏢 {r.get('fournisseur','—')}
                    </span>
                    <span style="color:#f0a070;font-weight:700;">
                        {float(r.get('montant_ttc',0)):.2f} €
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#c8956c;text-align:center;'>Aucune facture 🐾</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Petits chats décoratifs
    st.markdown("""
    <div style="text-align:center; padding:2rem; opacity:0.4;">
        🐱 &nbsp;&nbsp; 🐱 &nbsp;&nbsp; 🐱
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE FACTURES
# ═══════════════════════════════════════════════════════════════════════════════
def show_factures():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">📄 Gestion des Factures</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Importez et analysez vos factures avec l'IA 🤖🐱
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "resultats" not in st.session_state:
        st.session_state["resultats"] = []

    with st.expander("📤 Importer des factures", expanded=True):
        uploaded_files = st.file_uploader(
            "Glissez vos factures ici (PDF ou image)",
            type=["pdf","png","jpg","jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="facture_uploader"
        )

        if uploaded_files:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                analyser = st.button("🔍 Analyser avec l'IA",
                                     use_container_width=True,
                                     key="btn_analyser")
            with col_btn2:
                st.markdown(f"""
                <div style="background:#fff8f0;border-radius:12px;padding:0.6rem;
                     text-align:center;border:2px solid rgba(240,160,112,0.3);">
                    <span style="color:#a0522d;font-weight:600;">
                        📁 {len(uploaded_files)} fichier(s) 🐾
                    </span>
                </div>
                """, unsafe_allow_html=True)

            if analyser:
                model = configure_gemini()
                if not model:
                    st.error("❌ Clé API Gemini manquante dans les secrets")
                else:
                    progress = st.progress(0)
                    status   = st.empty()
                    for i, f in enumerate(uploaded_files):
                        status.markdown(f"""
                        <div style="background:#fff8f0;border-radius:12px;
                             padding:0.8rem;border-left:4px solid #f0a070;">
                            🔍 Analyse de <b>{f.name}</b>... 🐱
                        </div>
                        """, unsafe_allow_html=True)
                        content = f.read()
                        if f.name.lower().endswith(".pdf"):
                            images = pdf_to_images(content)
                        else:
                            images = [Image.open(io.BytesIO(content))]
                        result = extraire_facture(model, images)
                        result["fichier"] = f.name
                        # Sauvegarde Supabase
                        try:
                            supabase = get_supabase()
                            uid = st.session_state.get("user_id","")
                            supabase.table("factures").insert({
                                "user_id":     uid,
                                "fournisseur": result.get("fournisseur",""),
                                "numero":      result.get("numero",""),
                                "date":        result.get("date",""),
                                "montant_ht":  result.get("montant_ht",0),
                                "tva":         result.get("tva",0),
                                "montant_ttc": result.get("montant_ttc",0),
                                "categorie":   result.get("categorie","Autres"),
                                "statut":      result.get("statut","À payer"),
                                "fichier":     f.name
                            }).execute()
                        except:
                            pass
                        st.session_state["resultats"].append(result)
                        progress.progress((i+1)/len(uploaded_files))
                    status.success(f"✅ {len(uploaded_files)} facture(s) analysée(s) ! 🐱")

    # Liste factures
    resultats = st.session_state.get("resultats",[])
    try:
        supabase = get_supabase()
        uid = st.session_state.get("user_id","")
        db_res = supabase.table("factures").select("*").eq("user_id",uid).execute().data
        if db_res:
            resultats = db_res
    except:
        pass

    if resultats:
        total_ttc = sum(float(r.get("montant_ttc",0)) for r in resultats)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#fff8f0,#fdf0e8);
             border-radius:16px;padding:1rem;margin-bottom:1rem;
             border:2px solid rgba(240,160,112,0.3);text-align:center;">
            <span style="color:#a0522d;font-size:1.3rem;font-weight:700;">
                Total : {total_ttc:.2f} € TTC
            </span>
            &nbsp;|&nbsp;
            <span style="color:#c8956c;">{len(resultats)} facture(s) 🐾</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, r in enumerate(resultats):
            statut = r.get("statut","À payer")
            statut_color = {"Payée":"#4CAF50","À payer":"#f0a070","En retard":"#e74c3c"}.get(statut,"#f0a070")

            with st.container():
                st.markdown(f"""
                <div class="card" style="border-left:4px solid {statut_color};">
                    <div style="display:flex;justify-content:space-between;
                         align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
                        <div>
                            <h4 style="color:#a0522d;margin:0;">
                                🏢 {r.get('fournisseur','—')}
                            </h4>
                            <p style="color:#c8956c;margin:0.2rem 0;font-size:0.85rem;">
                                📅 {r.get('date','—')} &nbsp;|&nbsp;
                                🏷️ {r.get('categorie','—')} &nbsp;|&nbsp;
                                📄 {r.get('fichier','—')}
                            </p>
                        </div>
                        <div style="text-align:right;">
                            <p style="color:#a0522d;font-size:1.4rem;font-weight:700;margin:0;">
                                {float(r.get('montant_ttc',0)):.2f} €
                            </p>
                            <span style="background:{statut_color};color:white;
                                  padding:0.2rem 0.6rem;border-radius:20px;
                                  font-size:0.75rem;font-weight:600;">{statut}</span>
                        </div>
                    </div>
                    <div style="margin-top:0.8rem;display:flex;gap:1rem;font-size:0.85rem;color:#c8956c;">
                        <span>HT: {float(r.get('montant_ht',0)):.2f}€</span>
                        <span>TVA: {float(r.get('tva',0)):.2f}€</span>
                        <span>N°: {r.get('numero','—')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_s, col_d = st.columns([3,1])
                with col_s:
                    new_statut = st.selectbox(
                        "Statut",
                        ["À payer","Payée","En retard"],
                        index=["À payer","Payée","En retard"].index(statut) if statut in ["À payer","Payée","En retard"] else 0,
                        key=f"statut_f_{idx}",
                        label_visibility="collapsed"
                    )
                    if new_statut != statut:
                        st.session_state["resultats"][idx]["statut"] = new_statut
                        st.rerun()
                with col_d:
                    if st.button("🗑️", key=f"del_f_{idx}", use_container_width=True):
                        st.session_state["resultats"].pop(idx)
                        st.rerun()

        # Export
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        df_export = pd.DataFrame(resultats)
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exporter CSV", data=csv,
                file_name=f"factures_{datetime.now().strftime('%Y_%m')}.csv",
                mime="text/csv", use_container_width=True,
                key="export_csv_factures"
            )
        with col_ex2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_export.to_excel(w, index=False, sheet_name="Factures")
            st.download_button(
                "📊 Exporter Excel", data=buf.getvalue(),
                file_name=f"factures_{datetime.now().strftime('%Y_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="export_xl_factures"
            )
    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem;background:white;
             border-radius:24px;border:2px dashed #f0d5c0;margin-top:1rem;">
            <div style="font-size:4rem;">🐱</div>
            <h3 style="color:#a0522d;">Aucune facture importée</h3>
            <p style="color:#c8956c;">
                Utilisez le formulaire ci-dessus pour importer vos factures 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE NOTES DE FRAIS
# ═══════════════════════════════════════════════════════════════════════════════
def show_notes():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">🧾 Notes de Frais</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Gérez vos dépenses professionnelles 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    with st.expander("➕ Ajouter une note de frais", expanded=True):
        with st.form("form_note", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date_note   = st.date_input("📅 Date", datetime.now(), key="note_date")
                description = st.text_input("📝 Description", key="note_desc")
                categorie   = st.selectbox(
                    "🏷️ Catégorie",
                    ["Transport","Repas","Hébergement","Fournitures","Informatique","Autres"],
                    key="note_cat"
                )
            with col2:
                montant_ht = st.number_input("💶 Montant HT (€)", min_value=0.0,
                                              step=0.01, key="note_ht")
                taux_tva   = st.selectbox("📊 Taux TVA", [0,5.5,10,20],
                                           index=3, key="note_tva_taux")
                tva        = round(montant_ht * taux_tva / 100, 2)
                montant_ttc= round(montant_ht + tva, 2)
                st.markdown(f"""
                <div style="background:#fff8f0;border-radius:12px;padding:0.8rem;
                     border:2px solid rgba(240,160,112,0.3);margin-top:0.5rem;">
                    <p style="margin:0;color:#a0522d;font-weight:700;">
                        💰 TTC : {montant_ttc:.2f} €
                    </p>
                    <p style="margin:0;color:#c8956c;font-size:0.85rem;">
                        TVA ({taux_tva}%) : {tva:.2f} €
                    </p>
                </div>
                """, unsafe_allow_html=True)
                justificatif = st.file_uploader("📎 Justificatif", key="note_just")

            submitted = st.form_submit_button("✅ Ajouter la note de frais",
                                               use_container_width=True)
            if submitted:
                if description and montant_ht > 0:
                    note = {
                        "date":        str(date_note),
                        "description": description,
                        "categorie":   categorie,
                        "montant_ht":  montant_ht,
                        "tva":         tva,
                        "montant_ttc": montant_ttc,
                        "taux_tva":    taux_tva,
                        "justificatif": justificatif.name if justificatif else "—"
                    }
                    try:
                        supabase = get_supabase()
                        uid = st.session_state.get("user_id","")
                        supabase.table("notes_frais").insert({
                            "user_id": uid, **note
                        }).execute()
                        st.success("✅ Note sauvegardée dans Supabase ! 🐱")
                    except Exception as e:
                        st.warning(f"⚠️ Sauvegarde locale uniquement : {e}")
                    st.session_state["notes_frais"].append(note)
                    st.rerun()
                else:
                    st.error("❌ Veuillez remplir la description et le montant")

    # Liste
    notes = st.session_state.get("notes_frais",[])
    try:
        supabase = get_supabase()
        uid = st.session_state.get("user_id","")
        db_notes = supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data
        if db_notes:
            notes = db_notes
    except:
        pass

    if notes:
        total_notes = sum(float(n.get("montant_ttc",0)) for n in notes)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#fff8f0,#fdf0e8);
             border-radius:16px;padding:1rem;margin-bottom:1rem;
             border:2px solid rgba(240,160,112,0.3);text-align:center;">
            <span style="color:#a0522d;font-size:1.3rem;font-weight:700;">
                Total : {total_notes:.2f} € TTC
            </span>
            &nbsp;|&nbsp;
            <span style="color:#c8956c;">{len(notes)} note(s) 🐾</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, n in enumerate(notes):
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex;justify-content:space-between;
                         align-items:center;flex-wrap:wrap;gap:0.5rem;">
                        <div>
                            <h4 style="color:#a0522d;margin:0;">
                                📝 {n.get('description','—')}
                            </h4>
                            <p style="color:#c8956c;margin:0.2rem 0;font-size:0.85rem;">
                                📅 {n.get('date','—')} &nbsp;|&nbsp;
                                🏷️ {n.get('categorie','—')} &nbsp;|&nbsp;
                                📎 {n.get('justificatif','—')}
                            </p>
                        </div>
                        <div style="text-align:right;">
                            <p style="color:#a0522d;font-size:1.4rem;font-weight:700;margin:0;">
                                {float(n.get('montant_ttc',0)):.2f} €
                            </p>
                            <p style="color:#c8956c;font-size:0.8rem;margin:0;">
                                HT: {float(n.get('montant_ht',0)):.2f}€ |
                                TVA: {float(n.get('tva',0)):.2f}€
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Supprimer", key=f"del_note_{idx}",
                             use_container_width=True):
                    st.session_state["notes_frais"].pop(idx)
                    st.rerun()

        # Export
        df_n = pd.DataFrame(notes)
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.download_button(
                "📥 Exporter CSV",
                data=df_n.to_csv(index=False).encode("utf-8"),
                file_name=f"notes_{datetime.now().strftime('%Y_%m')}.csv",
                mime="text/csv", use_container_width=True,
                key="export_csv_notes"
            )
        with col_n2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_n.to_excel(w, index=False, sheet_name="Notes")
            st.download_button(
                "📊 Exporter Excel", data=buf.getvalue(),
                file_name=f"notes_{datetime.now().strftime('%Y_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="export_xl_notes"
            )
    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem;background:white;
             border-radius:24px;border:2px dashed #f0d5c0;margin-top:1rem;">
            <div style="font-size:4rem;">🐱</div>
            <h3 style="color:#a0522d;">Aucune note de frais</h3>
            <p style="color:#c8956c;">
                Ajoutez votre première dépense ci-dessus 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ASSISTANT IA (pleine page)
# ═══════════════════════════════════════════════════════════════════════════════
def show_chatbot():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">🤖 Assistant IA FactureCat</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Votre expert-comptable virtuel 🐱
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {"role":"assistant",
             "content":"Bonjour ! Je suis FactureCat 🐱 Comment puis-je vous aider aujourd'hui ?"}
        ]

    try:
        supabase = get_supabase()
        uid = st.session_state.get("user_id","")
        factures_data   = supabase.table("factures").select("*").eq("user_id",uid).execute().data or []
        notes_frais_data= supabase.table("notes_frais").select("*").eq("user_id",uid).execute().data or []
    except:
        factures_data    = st.session_state.get("resultats",[])
        notes_frais_data = st.session_state.get("notes_frais",[])

    # Historique
    for msg in st.session_state["chat_messages"]:
        role  = msg["role"]
        txt   = msg["content"]
        align = "flex-end" if role=="user" else "flex-start"
        bg    = "#f0a070"  if role=="user" else "white"
        color = "white"    if role=="user" else "#a0522d"
        icon  = "👤" if role=="user" else "🐱"
        st.markdown(f"""
        <div style="display:flex;justify-content:{align};margin:0.5rem 0;">
            <div style="background:{bg};color:{color};padding:0.8rem 1.2rem;
                 border-radius:18px;max-width:75%;
                 box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <span style="font-size:0.8rem;opacity:0.7;">{icon}</span>
                <br>{txt}
            </div>
        </div>
        """, unsafe_allow_html=True)

    user_input = st.chat_input("Posez votre question comptable 🐾")
    if user_input:
        st.session_state["chat_messages"].append({"role":"user","content":user_input})
        model = configure_gemini()
        if model:
            context = f"""
Tu es FactureCat 🐱, assistant expert-comptable virtuel, sympa et précis.
Factures : {json.dumps(factures_data, ensure_ascii=False)}
Notes de frais : {json.dumps(notes_frais_data, ensure_ascii=False)}
Réponds en français, de façon claire et concise.
Question : {user_input}
"""
            try:
                answer = model.generate_content(context).text
            except Exception as e:
                answer = f"❌ Erreur : {e}"
        else:
            answer = "❌ Clé API Gemini manquante dans les secrets"

        st.session_state["chat_messages"].append({"role":"assistant","content":answer})
        st.rerun()

    if st.button("🗑️ Effacer la conversation", use_container_width=True,
                 key="btn_clear_chat_page"):
        st.session_state["chat_messages"] = [
            {"role":"assistant",
             "content":"Bonjour ! Je suis FactureCat 🐱 Comment puis-je vous aider ?"}
        ]
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0;">
            <div style="font-size:3rem;">🐱</div>
            <h2 style="color:#a0522d; margin:0;">FactureCat</h2>
            <p style="color:#c8956c; font-size:0.85rem;">Gestion comptable IA 🐾</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#fff8f0;border-radius:12px;padding:0.6rem;
             text-align:center;margin-bottom:1rem;
             border:1px solid rgba(240,160,112,0.3);">
            <span style="color:#c8956c;font-size:0.8rem;">
                👤 {st.session_state.get('user_email','')}
            </span>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["🏠 Dashboard","📄 Factures","🧾 Notes de frais","🤖 Assistant IA"],
            label_visibility="collapsed",
            key="nav_radio"
        )

        st.markdown("<hr style='border-color:rgba(240,160,112,0.3)'>",
                    unsafe_allow_html=True)

        # Petits chats dans la sidebar
        st.markdown("""
        <div style="text-align:center;padding:1rem 0;opacity:0.5;font-size:1.5rem;">
            🐱 🐱 🐱
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Déconnexion", use_container_width=True, key="btn_logout"):
            st.session_state["authenticated"] = False
            st.session_state["user_email"]    = ""
            try:
                get_supabase().auth.sign_out()
            except:
                pass
            st.rerun()

    if page == "🏠 Dashboard":
        show_dashboard()
        show_floating_chat()
    elif page == "📄 Factures":
        show_factures()
        show_floating_chat()
    elif page == "🧾 Notes de frais":
        show_notes()
        show_floating_chat()
    elif page == "🤖 Assistant IA":
        show_chatbot()


if check_password():
    main()
