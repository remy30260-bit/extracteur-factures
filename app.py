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
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = ""
        try:
            supabase = get_supabase()
            session = supabase.auth.get_session()
            if session and session.user:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = session.user.email
        except:
            pass

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
        mode  = st.radio("Mode", ["🔑 Se connecter", "✨ Créer un compte"],
                         horizontal=True, label_visibility="collapsed")
        email = st.text_input("📧 Email")
        pwd   = st.text_input("🔒 Mot de passe", type="password")

        if st.button("Valider 🐾", use_container_width=True):
            try:
                supabase = get_supabase()
                if mode == "🔑 Se connecter":
                    res = supabase.auth.sign_in_with_password(
                        {"email": email, "password": pwd}
                    )
                else:
                    res = supabase.auth.sign_up(
                        {"email": email, "password": pwd}
                    )
                if res.user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = res.user.email
                    st.rerun()
                else:
                    st.error("❌ Echec de connexion")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# GEMINI
# ═══════════════════════════════════════════════════════════════════════════════
def configure_gemini():
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except:
        return None

def pdf_to_images(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    imgs = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return imgs

def extraire_facture(model, image, filename=""):
    prompt = """
    Analyse cette facture et extrais les informations suivantes en JSON :
    {
      "fournisseur": "nom du fournisseur",
      "numero_facture": "numéro de facture",
      "date": "date de la facture (JJ/MM/AAAA)",
      "description": "description des produits/services",
      "montant_ht": montant_ht_en_float,
      "tva": montant_tva_en_float,
      "montant_ttc": montant_ttc_en_float,
      "categorie": "catégorie (Services/Fournitures/Transport/Repas/Hébergement/Autres)",
      "statut": "À vérifier 🔍"
    }
    Réponds UNIQUEMENT avec le JSON, sans texte autour.
    """
    try:
        resp = model.generate_content([prompt, image])
        txt  = resp.text.strip()
        txt  = txt.replace("```json","").replace("```","").strip()
        data = json.loads(txt)
        data["fichier"] = filename
        return data
    except Exception as e:
        return {
            "fichier": filename, "fournisseur": "Erreur extraction",
            "numero_facture": "—", "date": "—", "description": str(e),
            "montant_ht": 0.0, "tva": 0.0, "montant_ttc": 0.0,
            "categorie": "Autres", "statut": "Erreur ❌"
        }

# ═══════════════════════════════════════════════════════════════════════════════
# CHATBOT WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
def render_chat_widget(notes_frais_data=None, factures_data=None):
    if "chat_open"     not in st.session_state: st.session_state["chat_open"]     = False
    if "chat_messages" not in st.session_state: st.session_state["chat_messages"] = []

    st.markdown("""
    <style>
    .chat-bubble-btn {
        position:fixed; bottom:2rem; right:2rem; z-index:9999;
        background:linear-gradient(135deg,#f0a070,#e8856a);
        color:white; border:none; border-radius:50%;
        width:60px; height:60px; font-size:1.8rem;
        cursor:pointer; box-shadow:0 4px 15px rgba(240,160,112,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🤖 Assistant FactureCat")
        if st.button("💬 Ouvrir/Fermer le chat", use_container_width=True):
            st.session_state["chat_open"] = not st.session_state["chat_open"]

    if st.session_state["chat_open"]:
        st.markdown("---")
        st.markdown("""
        <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
             border-radius:20px; padding:1.5rem; margin-bottom:1rem; color:white;">
            <h3 style="margin:0;">🤖 Assistant FactureCat 🐱</h3>
            <p style="margin:0.3rem 0 0; opacity:0.9; font-size:0.9rem;">
                Posez vos questions sur vos factures et notes de frais
            </p>
        </div>
        """, unsafe_allow_html=True)

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state["chat_messages"]:
                role  = msg["role"]
                txt   = msg["content"]
                align = "flex-end" if role == "user" else "flex-start"
                bg    = "linear-gradient(135deg,#f0a070,#e8856a)" if role == "user" else "white"
                color = "white" if role == "user" else "#a0522d"
                icon  = "👤" if role == "user" else "🐱"
                st.markdown(f"""
                <div style="display:flex; justify-content:{align}; margin:0.5rem 0;">
                    <div style="background:{bg}; color:{color}; padding:0.8rem 1.2rem;
                         border-radius:18px; max-width:80%; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                        <span style="font-size:0.8rem; opacity:0.7;">{icon}</span><br>{txt}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        user_input = st.chat_input("Posez votre question 🐾")
        if user_input:
            st.session_state["chat_messages"].append(
                {"role":"user","content":user_input}
            )
            model = configure_gemini()
            if model:
                context = f"""
Tu es l'assistant FactureCat 🐱, expert-comptable virtuel sympa.
Données factures : {json.dumps(factures_data or [], ensure_ascii=False)}
Données notes de frais : {json.dumps(notes_frais_data or [], ensure_ascii=False)}
Réponds en français, de façon claire et concise.
Question : {user_input}
"""
                try:
                    resp   = model.generate_content(context)
                    answer = resp.text
                except Exception as e:
                    answer = f"❌ Erreur : {e}"
            else:
                answer = "❌ Clé API Gemini manquante"

            st.session_state["chat_messages"].append(
                {"role":"assistant","content":answer}
            )
            st.rerun()

        if st.button("🗑️ Effacer la conversation", use_container_width=True):
            st.session_state["chat_messages"] = []
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #fdf6f0 0%, #fef9f5 50%, #fff8f0 100%);
    min-height: 100vh;
}

.card {
    background: white;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(240,160,112,0.1);
    border: 1px solid rgba(240,160,112,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(240,160,112,0.2);
}

.metric-card {
    background: linear-gradient(135deg, #fff8f0, #fdf0e8);
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    border: 2px solid rgba(240,160,112,0.3);
    margin-bottom: 1rem;
}

.stButton > button {
    background: linear-gradient(135deg, #f0a070, #e8856a) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(240,160,112,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(240,160,112,0.5) !important;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    border-radius: 12px !important;
    border: 2px solid rgba(240,160,112,0.3) !important;
    background: white !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #f0a070 !important;
    box-shadow: 0 0 0 3px rgba(240,160,112,0.2) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff8f0 0%, #fdf0e8 100%) !important;
    border-right: 2px solid rgba(240,160,112,0.2) !important;
}

.stDataFrame, .stTable {
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(240,160,112,0.1) !important;
}

div[data-testid="metric-container"] {
    background: white;
    border-radius: 16px;
    padding: 1rem;
    border: 2px solid rgba(240,160,112,0.2);
    box-shadow: 0 4px 15px rgba(240,160,112,0.1);
}

.stProgress > div > div {
    background: linear-gradient(135deg, #f0a070, #e8856a) !important;
    border-radius: 10px !important;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #fff8f0; border-radius: 10px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #f0a070, #e8856a);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════
if not check_password():
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:3rem;">🐱</div>
        <h2 style="color:#a0522d; margin:0.5rem 0;">FactureCat</h2>
        <p style="color:#c8956c; font-size:0.85rem; margin:0;">
            Votre comptable intelligent
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Tableau de bord", "📄 Factures",
         "🧾 Notes de frais"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    nb_factures = len(st.session_state.get("resultats", []))
    nb_notes    = len(st.session_state.get("notes_frais", []))

    total_ttc_f = sum(
        float(r.get("montant_ttc", 0))
        for r in st.session_state.get("resultats", [])
    )
    total_ttc_n = sum(
        float(n.get("montant_ttc", 0))
        for n in st.session_state.get("notes_frais", [])
    )

    st.markdown(f"""
    <div style="background:white; border-radius:16px; padding:1rem;
         border:2px solid rgba(240,160,112,0.2);">
        <p style="color:#c8956c; font-size:0.8rem; margin:0 0 0.5rem;
           font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">
            📊 Résumé rapide
        </p>
        <div style="display:flex; justify-content:space-between;
             align-items:center; margin:0.3rem 0;">
            <span style="color:#a0522d; font-size:0.85rem;">📄 Factures</span>
            <span style="background:linear-gradient(135deg,#f0a070,#e8856a);
                  color:white; border-radius:20px; padding:0.1rem 0.6rem;
                  font-size:0.8rem; font-weight:700;">{nb_factures}</span>
        </div>
        <div style="display:flex; justify-content:space-between;
             align-items:center; margin:0.3rem 0;">
            <span style="color:#a0522d; font-size:0.85rem;">🧾 Notes</span>
            <span style="background:linear-gradient(135deg,#f0a070,#e8856a);
                  color:white; border-radius:20px; padding:0.1rem 0.6rem;
                  font-size:0.8rem; font-weight:700;">{nb_notes}</span>
        </div>
        <div style="border-top:1px solid rgba(240,160,112,0.2);
             margin-top:0.5rem; padding-top:0.5rem;">
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#a0522d; font-size:0.85rem;">💰 Total</span>
                <span style="color:#e8856a; font-weight:700; font-size:0.9rem;">
                    {total_ttc_f + total_ttc_n:.2f} €
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    user_email = st.session_state.get("user_email", "")
    st.markdown(f"""
    <div style="text-align:center; padding:0.5rem;">
        <span style="font-size:1.5rem;">👤</span><br>
        <span style="color:#a0522d; font-size:0.8rem; font-weight:600;">
            {user_email}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Déconnexion", use_container_width=True):
        try:
            supabase = get_supabase()
            supabase.auth.sign_out()
        except:
            pass
        st.session_state["authenticated"] = False
        st.session_state["user_email"]    = ""
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Tableau de bord":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2.5rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2.5rem;">🐱 Bonjour FactureCat !</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9; font-size:1.1rem;">
            Votre tableau de bord comptable intelligent ✨
        </p>
    </div>
    """, unsafe_allow_html=True)

    factures   = st.session_state.get("resultats",   [])
    notes      = st.session_state.get("notes_frais", [])

    total_f_ht  = sum(float(r.get("montant_ht",  0)) for r in factures)
    total_f_tva = sum(float(r.get("tva",         0)) for r in factures)
    total_f_ttc = sum(float(r.get("montant_ttc", 0)) for r in factures)
    total_n_ht  = sum(float(n.get("montant_ht",  0)) for n in notes)
    total_n_ttc = sum(float(n.get("montant_ttc", 0)) for n in notes)

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "📄 Factures",      f"{len(factures)}",         f"Total HT : {total_f_ht:.2f} €"),
        (col2, "💰 CA Factures",   f"{total_f_ttc:.2f} €",     f"TVA : {total_f_tva:.2f} €"),
        (col3, "🧾 Notes de frais",f"{len(notes)}",            f"Total HT : {total_n_ht:.2f} €"),
        (col4, "💸 Total dépenses",f"{total_f_ttc+total_n_ttc:.2f} €", "TTC toutes dépenses"),
    ]
    for col, label, value, delta in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#c8956c; font-size:0.85rem; margin:0 0 0.5rem;
                   font-weight:600; text-transform:uppercase;">{label}</p>
                <p style="color:#a0522d; font-size:1.8rem; font-weight:700;
                   margin:0;">{value}</p>
                <p style="color:#d4a882; font-size:0.8rem; margin:0.3rem 0 0;">
                   {delta}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div class="card">
            <h3 style="color:#a0522d; margin:0 0 1rem;">📊 Répartition par catégorie</h3>
        </div>
        """, unsafe_allow_html=True)

        all_data = []
        for r in factures:
            all_data.append({
                "categorie": r.get("categorie","Autres"),
                "montant":   float(r.get("montant_ttc",0)),
                "type":      "Facture"
            })
        for n in notes:
            all_data.append({
                "categorie": n.get("categorie","Autres"),
                "montant":   float(n.get("montant_ttc",0)),
                "type":      "Note de frais"
            })

        if all_data:
            df_cat = pd.DataFrame(all_data)
            df_cat = df_cat.groupby("categorie")["montant"].sum().reset_index()
            df_cat.columns = ["Catégorie","Montant TTC (€)"]
            st.bar_chart(df_cat.set_index("Catégorie"))
        else:
            st.markdown("""
            <div style="text-align:center; padding:2rem; color:#c8956c;">
                <div style="font-size:2rem;">🐱</div>
                <p>Aucune donnée disponible</p>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="card">
            <h3 style="color:#a0522d; margin:0 0 1rem;">🕐 Dernières activités</h3>
        </div>
        """, unsafe_allow_html=True)

        activites = []
        for r in factures[-5:]:
            activites.append({
                "Type":        "📄 Facture",
                "Description": r.get("fournisseur","—"),
                "Montant":     f"{float(r.get('montant_ttc',0)):.2f} €",
                "Statut":      r.get("statut","—")
            })
        for n in notes[-5:]:
            activites.append({
                "Type":        "🧾 Note",
                "Description": n.get("description","—"),
                "Montant":     f"{float(n.get('montant_ttc',0)):.2f} €",
                "Statut":      "Validée ✅"
            })

        if activites:
            st.dataframe(
                pd.DataFrame(activites),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown("""
            <div style="text-align:center; padding:2rem; color:#c8956c;">
                <div style="font-size:2rem;">🐾</div>
                <p>Aucune activité récente</p>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Factures":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">📄 Gestion des Factures</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Importez et analysez vos factures avec l'IA 🤖
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "resultats" not in st.session_state:
        st.session_state["resultats"] = []

    # ── Upload ────────────────────────────────────────────────────────────────
    with st.expander("📤 Importer des factures", expanded=True):
        uploaded_files = st.file_uploader(
            "Glissez vos factures ici (PDF ou image)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded_files:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                analyser = st.button(
                    "🔍 Analyser avec l'IA", use_container_width=True
                )
            with col_btn2:
                st.markdown(f"""
                <div style="background:#fff8f0; border-radius:12px; padding:0.6rem;
                     text-align:center; border:2px solid rgba(240,160,112,0.3);">
                    <span style="color:#a0522d; font-weight:600;">
                        📁 {len(uploaded_files)} fichier(s) sélectionné(s)
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
                        <div style="background:#fff8f0; border-radius:12px;
                             padding:0.8rem; border-left:4px solid #f0a070;">
                            🔍 Analyse de <b>{f.name}</b>...
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            images = pdf_to_images(f)
                            result = extraire_facture(model, images)
                            result["fichier"] = f.name
                            result["statut"]  = result.get("statut", "À payer")

                            # Sauvegarde Supabase
                            try:
                                supabase = get_supabase()
                                user_id  = st.session_state.get("user_id", "")
                                supabase.table("factures").insert({
                                    "user_id":     user_id,
                                    "fichier":     result.get("fichier",""),
                                    "fournisseur": result.get("fournisseur",""),
                                    "date":        result.get("date",""),
                                    "montant_ht":  float(result.get("montant_ht",0)),
                                    "tva":         float(result.get("tva",0)),
                                    "montant_ttc": float(result.get("montant_ttc",0)),
                                    "categorie":   result.get("categorie",""),
                                    "statut":      result.get("statut",""),
                                    "numero":      result.get("numero",""),
                                }).execute()
                            except Exception as e:
                                st.warning(f"⚠️ Sauvegarde Supabase échouée : {e}")

                            st.session_state["resultats"].append(result)

                        except Exception as e:
                            st.error(f"❌ Erreur sur {f.name} : {e}")

                        progress.progress((i + 1) / len(uploaded_files))

                    status.markdown("""
                    <div style="background:#f0fff4; border-radius:12px;
                         padding:0.8rem; border-left:4px solid #68d391;">
                        ✅ Analyse terminée !
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()

    # ── Liste des factures ────────────────────────────────────────────────────
    resultats = st.session_state.get("resultats", [])

    if resultats:
        st.markdown("""
        <h3 style="color:#a0522d; margin:1.5rem 0 1rem;">
            📋 Vos factures
        </h3>
        """, unsafe_allow_html=True)

        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtre_statut = st.selectbox(
                "Filtrer par statut",
                ["Tous", "À payer", "Payée ✅", "En retard ⚠️"]
            )
        with col_f2:
            categories_dispo = list(set(
                r.get("categorie","Autres") for r in resultats
            ))
            filtre_cat = st.selectbox(
                "Filtrer par catégorie",
                ["Toutes"] + categories_dispo
            )
        with col_f3:
            tri = st.selectbox(
                "Trier par",
                ["Date ↓", "Date ↑", "Montant ↓", "Montant ↑"]
            )

        # Application des filtres
        factures_filtrees = resultats.copy()
        if filtre_statut != "Tous":
            factures_filtrees = [
                r for r in factures_filtrees
                if r.get("statut") == filtre_statut
            ]
        if filtre_cat != "Toutes":
            factures_filtrees = [
                r for r in factures_filtrees
                if r.get("categorie") == filtre_cat
            ]

        # Tri
        reverse = "↓" in tri
        if "Montant" in tri:
            factures_filtrees.sort(
                key=lambda x: float(x.get("montant_ttc", 0)),
                reverse=reverse
            )
        else:
            factures_filtrees.sort(
                key=lambda x: str(x.get("date", "")),
                reverse=reverse
            )

        # Affichage cards
        for idx, r in enumerate(factures_filtrees):
            statut    = r.get("statut", "À payer")
            statut_color = {
                "Payée ✅":    "#68d391",
                "À payer":     "#f0a070",
                "En retard ⚠️":"#fc8181"
            }.get(statut, "#f0a070")

            with st.container():
                st.markdown(f"""
                <div class="card" style="border-left:4px solid {statut_color};">
                    <div style="display:flex; justify-content:space-between;
                         align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                        <div>
                            <h4 style="color:#a0522d; margin:0;">
                                📄 {r.get('fournisseur','—')}
                            </h4>
                            <p style="color:#c8956c; margin:0.2rem 0; font-size:0.85rem;">
                                📁 {r.get('fichier','—')} &nbsp;|&nbsp;
                                📅 {r.get('date','—')} &nbsp;|&nbsp;
                                🏷️ {r.get('categorie','—')}
                            </p>
                        </div>
                        <div style="text-align:right;">
                            <p style="color:#a0522d; font-size:1.4rem;
                               font-weight:700; margin:0;">
                                {float(r.get('montant_ttc',0)):.2f} €
                            </p>
                            <span style="background:{statut_color}; color:white;
                                  border-radius:20px; padding:0.2rem 0.8rem;
                                  font-size:0.8rem; font-weight:600;">
                                {statut}
                            </span>
                        </div>
                    </div>
                    <div style="display:flex; gap:2rem; margin-top:0.8rem;
                         padding-top:0.8rem;
                         border-top:1px solid rgba(240,160,112,0.2);">
                        <span style="color:#c8956c; font-size:0.85rem;">
                            HT : <b>{float(r.get('montant_ht',0)):.2f} €</b>
                        </span>
                        <span style="color:#c8956c; font-size:0.85rem;">
                            TVA : <b>{float(r.get('tva',0)):.2f} €</b>
                        </span>
                        <span style="color:#c8956c; font-size:0.85rem;">
                            N° : <b>{r.get('numero','—')}</b>
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_s, col_d = st.columns([3, 1])
                with col_s:
                    nouveau_statut = st.selectbox(
                        "Statut",
                        ["À payer", "Payée ✅", "En retard ⚠️"],
                        index=["À payer","Payée ✅","En retard ⚠️"].index(
                            statut if statut in ["À payer","Payée ✅","En retard ⚠️"]
                            else "À payer"
                        ),
                        key=f"statut_{idx}",
                        label_visibility="collapsed"
                    )
                    if nouveau_statut != statut:
                        st.session_state["resultats"][idx]["statut"] = nouveau_statut
                        st.rerun()
                with col_d:
                    if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                        st.session_state["resultats"].pop(idx)
                        st.rerun()

        # ── Export ────────────────────────────────────────────────────────────
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        df_export = pd.DataFrame(resultats)
        col_ex1, col_ex2 = st.columns(2)

        with col_ex1:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exporter CSV",
                data=csv,
                file_name=f"factures_{datetime.now().strftime('%Y_%m')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_ex2:
            buffer_xl = io.BytesIO()
            with pd.ExcelWriter(buffer_xl, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Factures")
            st.download_button(
                "📊 Exporter Excel",
                data=buffer_xl.getvalue(),
                file_name=f"factures_{datetime.now().strftime('%Y_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    else:
        st.markdown("""
        <div style="text-align:center; padding:4rem; background:white;
             border-radius:24px; border:2px dashed #f0d5c0; margin-top:1rem;">
            <div style="font-size:4rem;">🐱</div>
            <h3 style="color:#a0522d;">Aucune facture importée</h3>
            <p style="color:#c8956c;">
                Utilisez le formulaire ci-dessus pour importer vos factures 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧾 Notes de frais":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">🧾 Notes de Frais</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Gérez vos dépenses professionnelles 💼
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    # ── Formulaire ────────────────────────────────────────────────────────────
    with st.expander("➕ Ajouter une note de frais", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            date_note    = st.date_input("📅 Date", datetime.now())
            description  = st.text_input("📝 Description", placeholder="Ex: Repas client...")
            categorie    = st.selectbox("🏷️ Catégorie", [
                "Repas", "Transport", "Hébergement",
                "Fournitures", "Formation", "Téléphone",
                "Carburant", "Autres"
            ])

        with col2:
            montant_ht   = st.number_input("💶 Montant HT (€)", min_value=0.0, step=0.01)
            taux_tva     = st.selectbox("📊 Taux TVA", ["20%","10%","5.5%","0%"])
            justificatif = st.file_uploader(
                "📎 Justificatif", type=["pdf","png","jpg","jpeg"]
            )

        taux = float(taux_tva.replace("%","")) / 100
        tva        = montant_ht * taux
        montant_ttc = montant_ht + tva

        st.markdown(f"""
        <div style="background:#fff8f0; border-radius:12px; padding:1rem;
             border:2px solid rgba(240,160,112,0.3); margin:0.5rem 0;">
            <div style="display:flex; gap:2rem; justify-content:center;">
                <span style="color:#c8956c;">
                    HT : <b style="color:#a0522d;">{montant_ht:.2f} €</b>
                </span>
                <span style="color:#c8956c;">
                    TVA : <b style="color:#a0522d;">{tva:.2f} €</b>
                </span>
                <span style="color:#c8956c;">
                    TTC : <b style="color:#a0522d; font-size:1.1rem;">{montant_ttc:.2f} €</b>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Ajouter la note de frais", use_container_width=True):
            if description and montant_ht > 0:
                note = {
                    "date":        str(date_note),
                    "description": description,
                    "categorie":   categorie,
                    "montant_ht":  montant_ht,
                    "tva":         tva,
                    "montant_ttc": montant_ttc,
                    "taux_tva":    taux_tva,
                    "justificatif":justificatif.name if justificatif else "—"
                }

                # Sauvegarde Supabase
                try:
                    supabase = get_supabase()
                    user_id  = st.session_state.get("user_id","")
                    supabase.table("notes_frais").insert({
                        "user_id":     user_id,
                        "date":        str(date_note),
                        "description": description,
                        "categorie":   categorie,
                        "montant_ht":  montant_ht,
                        "tva":         tva,
                        "montant_ttc": montant_ttc,
                        "taux_tva":    taux_tva,
                        "justificatif":justificatif.name if justificatif else "—"
                    }).execute()
                    st.success("✅ Note sauvegardée dans Supabase !")
                except Exception as e:
                    st.warning(f"⚠️ Sauvegarde Supabase échouée : {e}")

                st.session_state["notes_frais"].append(note)
                st.rerun()
            else:
                st.error("❌ Veuillez remplir la description et le montant")

    # ── Liste des notes ───────────────────────────────────────────────────────
    notes = st.session_state.get("notes_frais", [])

    if notes:
        st.markdown("""
        <h3 style="color:#a0522d; margin:1.5rem 0 1rem;">
            📋 Vos notes de frais
        </h3>
        """, unsafe_allow_html=True)

        total_notes = sum(float(n.get("montant_ttc",0)) for n in notes)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#fff8f0,#fdf0e8);
             border-radius:16px; padding:1rem; margin-bottom:1rem;
             border:2px solid rgba(240,160,112,0.3); text-align:center;">
            <span style="color:#a0522d; font-size:1.3rem; font-weight:700;">
                Total : {total_notes:.2f} € TTC
            </span>
            &nbsp;|&nbsp;
            <span style="color:#c8956c;">
                {len(notes)} note(s) de frais
            </span>
        </div>
        """, unsafe_allow_html=True)

        for idx, n in enumerate(notes):
            with st.container():
                st.markdown(f"""
                <div class="card" style="border-left:4px solid #f0a070;">
                    <div style="display:flex; justify-content:space-between;
                         align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                        <div>
                            <h4 style="color:#a0522d; margin:0;">
                                🧾 {n.get('description','—')}
                            </h4>
                            <p style="color:#c8956c; margin:0.2rem 0; font-size:0.85rem;">
                                📅 {n.get('date','—')} &nbsp;|&nbsp;
                                🏷️ {n.get('categorie','—')} &nbsp;|&nbsp;
                                📎 {n.get('justificatif','—')}
                            </p>
                        </div>
                        <div style="text-align:right;">
                            <p style="color:#a0522d; font-size:1.4rem;
                               font-weight:700; margin:0;">
                                {float(n.get('montant_ttc',0)):.2f} €
                            </p>
                            <span style="color:#c8956c; font-size:0.8rem;">
                                TVA {n.get('taux_tva','—')}
                            </span>
                        </div>
                    </div>
                    <div style="display:flex; gap:2rem; margin-top:0.8rem;
                         padding-top:0.8rem;
                         border-top:1px solid rgba(240,160,112,0.2);">
                        <span style="color:#c8956c; font-size:0.85rem;">
                            HT : <b>{float(n.get('montant_ht',0)):.2f} €</b>
                        </span>
                        <span style="color:#c8956c; font-size:0.85rem;">
                            TVA : <b>{float(n.get('tva',0)):.2f} €</b>
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Supprimer", key=f"del_note_{idx}",
                             use_container_width=True):
                    st.session_state["notes_frais"].pop(idx)
                    st.rerun()

        # Export
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        df_notes   = pd.DataFrame(notes)
        col_ex1, col_ex2 = st.columns(2)

        with col_ex1:
            csv_notes = df_notes.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exporter CSV",
                data=csv_notes,
                file_name=f"notes_frais_{datetime.now().strftime('%Y_%m')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_ex2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_notes.to_excel(writer, index=False, sheet_name="Notes de frais")
            st.download_button(
                "📊 Exporter Excel",
                data=buf.getvalue(),
                file_name=f"notes_frais_{datetime.now().strftime('%Y_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.markdown("""
        <div style="text-align:center; padding:4rem; background:white;
             border-radius:24px; border:2px dashed #f0d5c0; margin-top:1rem;">
            <div style="font-size:4rem;">🧾</div>
            <h3 style="color:#a0522d;">Aucune note de frais</h3>
            <p style="color:#c8956c;">
                Utilisez le formulaire ci-dessus pour ajouter vos dépenses 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Assistant IA":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
         border-radius:24px; padding:2rem; margin-bottom:2rem; color:white;
         box-shadow:0 8px 32px rgba(240,160,112,0.4);">
        <h1 style="margin:0; font-size:2rem;">🤖 Assistant FactureCat</h1>
        <p style="margin:0.5rem 0 0; opacity:0.9;">
            Posez vos questions comptables à votre assistant IA 🐱
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    factures_data   = st.session_state.get("resultats", [])
    notes_frais_data = st.session_state.get("notes_frais", [])

    # Historique
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["chat_messages"]:
            role = msg["role"]
            txt  = msg["content"]
            align = "flex-end"   if role == "user" else "flex-start"
            bg    = "#f0a070"    if role == "user" else "white"
            color = "white"      if role == "user" else "#a0522d"
            icon  = "👤" if role == "user" else "🐱"
            st.markdown(f"""
            <div style="display:flex; justify-content:{align}; margin:0.5rem 0;">
                <div style="background:{bg}; color:{color}; padding:0.8rem 1.2rem;
                     border-radius:18px; max-width:80%;
                     box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <span style="font-size:0.8rem; opacity:0.7;">{icon}</span>
                    <br>{txt}
                </div>
            </div>
            """, unsafe_allow_html=True)

    user_input = st.chat_input("Posez votre question 🐾")
    if user_input:
        st.session_state["chat_messages"].append(
            {"role":"user","content":user_input}
        )
        model = configure_gemini()
        if model:
            context = f"""
Tu es l'assistant FactureCat 🐱, expert-comptable virtuel sympa.
Données factures : {json.dumps(factures_data, ensure_ascii=False)}
Données notes de frais : {json.dumps(notes_frais_data, ensure_ascii=False)}
Réponds en français, de façon claire et concise.
Question : {user_input}
"""
            try:
                resp   = model.generate_content(context)
                answer = resp.text
            except Exception as e:
                answer = f"❌ Erreur : {e}"
        else:
            answer = "❌ Clé API Gemini manquante"

        st.session_state["chat_messages"].append(
            {"role":"assistant","content":answer}
        )
        st.rerun()

    if st.button("🗑️ Effacer la conversation", use_container_width=True):
        st.session_state["chat_messages"] = []
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def configure_gemini():
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"❌ Erreur Gemini : {e}")
        return None

def pdf_to_images(uploaded_file):
    content = uploaded_file.read()
    if uploaded_file.name.lower().endswith(".pdf"):
        doc    = fitz.open(stream=content, filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
        return images
    else:
        return [Image.open(io.BytesIO(content))]

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
        text     = response.text.strip()
        text     = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except json.JSONDecodeError:
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

if __name__ == "__main__":
    if check_password():
        main()


