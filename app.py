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

# ─── SUPABASE ─────────────────────────────────────────────────────────────────
from supabase import create_client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# ─── LOGIN ────────────────────────────────────────────────────────────────────
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
        mode = st.radio("Mode", ["🔑 Se connecter", "✨ Créer un compte"],
                        horizontal=True, label_visibility="collapsed")
        email    = st.text_input("📧 Email")
        password = st.text_input("🔑 Mot de passe", type="password")

        if mode == "✨ Créer un compte":
            password2 = st.text_input("🔑 Confirmer mot de passe", type="password")
            if st.button("🐾 Créer mon compte", use_container_width=True):
                if password != password2:
                    st.error("❌ Mots de passe différents !")
                elif len(password) < 6:
                    st.error("❌ Minimum 6 caractères !")
                else:
                    try:
                        supabase = get_supabase()
                        res = supabase.auth.sign_up({"email": email, "password": password})
                        if res.user:
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = email
                            st.success("✅ Bienvenue ! 🐾")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")
        else:
            if st.button("🐾 Se connecter", use_container_width=True):
                try:
                    supabase = get_supabase()
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Identifiants incorrects : {e}")

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

    /* ── Tableau éditable amélioré ── */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 2px solid #f0d5c0 !important;
        box-shadow: 0 4px 20px rgba(200,149,108,0.15) !important;
    }
    .dvn-scroller { border-radius: 16px !important; }
    .glideDataEditor {
        border-radius: 16px !important;
        font-family: 'Nunito', sans-serif !important;
    }
    /* Header */
    .gdg-style-header {
        background: linear-gradient(135deg, #f0a070, #e8856a) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }
    /* Lignes alternées */
    .gdg-style tr:nth-child(even) { background-color: #fff8f3 !important; }
    .gdg-style tr:nth-child(odd)  { background-color: #ffffff !important; }
    /* Hover */
    .gdg-style tr:hover { background-color: #fde8d8 !important; }

    pre.cat-ascii {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 1.1rem !important; line-height: 1.2 !important;
        color: #c8956c !important; white-space: pre !important;
        background: none !important; border: none !important;
        padding: 0.5rem 1rem !important; margin: 0.5rem auto !important;
        display: block !important; text-align: center !important;
        width: fit-content !important;
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

# ─── CHATBOT FLOTTANT ─────────────────────────────────────────────────────────
def render_chat_widget(notes_frais_data=None, factures_data=None):
    """Chat flottant FactureCat — répond aux questions sur les données."""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "chat_open" not in st.session_state:
        st.session_state["chat_open"] = False

    # Contexte données
    ctx_factures = ""
    if factures_data:
        try:
            ctx_factures = f"Factures extraites : {json.dumps(factures_data, ensure_ascii=False)}"
        except:
            ctx_factures = ""

    ctx_notes = ""
    if notes_frais_data:
        try:
            ctx_notes = f"Notes de frais : {json.dumps(notes_frais_data, ensure_ascii=False)}"
        except:
            ctx_notes = ""

    # Bouton toggle
    with st.container():
        col_chat = st.columns([6, 1])
        with col_chat[1]:
            if st.button("💬 FactureCat", key="chat_toggle"):
                st.session_state["chat_open"] = not st.session_state["chat_open"]

    if not st.session_state["chat_open"]:
        # Widget flottant CSS-only quand fermé
        components.html("""
        <style>
        .fab-chat {
            position: fixed; bottom: 2rem; right: 2rem;
            background: linear-gradient(135deg,#f0a070,#e8856a);
            color: white; border-radius: 50px;
            padding: 0.8rem 1.5rem; font-size: 1rem; font-weight: 700;
            box-shadow: 0 4px 20px rgba(200,149,108,0.5);
            cursor: pointer; z-index: 9999;
            font-family: 'Nunito', sans-serif;
            border: none; transition: all 0.3s;
        }
        .fab-chat:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(200,149,108,0.7); }
        </style>
        <button class="fab-chat" onclick="window.parent.document.querySelector('[data-testid=\\'stBaseButton-secondary\\']').click()">
            💬 FactureCat
        </button>
        """, height=0)
        return

    # Fenêtre de chat
    st.markdown("""
    <div style="
        position: fixed; bottom: 5rem; right: 2rem;
        width: 380px; max-height: 520px;
        background: white; border-radius: 20px;
        box-shadow: 0 8px 40px rgba(200,149,108,0.35);
        border: 2px solid #f0d5c0;
        z-index: 9998; display: flex; flex-direction: column;
        overflow: hidden;
    ">
        <div style="
            background: linear-gradient(135deg,#f0a070,#e8856a);
            padding: 1rem 1.5rem; border-radius: 18px 18px 0 0;
            display: flex; align-items: center; gap: 0.8rem;
        ">
            <span style="font-size:1.8rem;">🐱</span>
            <div>
                <p style="color:white;font-weight:800;margin:0;font-size:1rem;">FactureCat</p>
                <p style="color:#fff8f3;margin:0;font-size:0.75rem;">Votre assistant comptable félin</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Historique messages
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["chat_history"]:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-end;margin:0.4rem 0;">
                    <div style="background:linear-gradient(135deg,#f0a070,#e8856a);
                        color:white;border-radius:18px 18px 4px 18px;
                        padding:0.6rem 1rem;max-width:75%;font-size:0.9rem;font-weight:600;">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;gap:0.5rem;margin:0.4rem 0;">
                    <span style="font-size:1.5rem;">🐱</span>
                    <div style="background:#fff8f3;border:2px solid #f5e6d8;
                        border-radius:4px 18px 18px 18px;
                        padding:0.6rem 1rem;max-width:75%;font-size:0.9rem;">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Input
    with st.form("chat_form", clear_on_submit=True):
        col_i, col_s = st.columns([4, 1])
        with col_i:
            user_input = st.text_input("", placeholder="Posez votre question...",
                                       label_visibility="collapsed", key="chat_input")
        with col_s:
            send = st.form_submit_button("📨")

    if send and user_input.strip():
        st.session_state["chat_history"].append({"role": "user", "content": user_input})

        # Réponses rapides sans API
        q = user_input.lower()
        reponse = None

        if any(w in q for w in ["total", "somme", "montant"]):
            if factures_data:
                try:
                    total = sum(float(str(r.get("montant_ttc", 0)).replace(",", ".") or 0)
                                for r in factures_data)
                    reponse = f"💰 Total TTC de vos factures : **{total:.2f} €** 🐾"
                except:
                    reponse = "Je n'arrive pas à calculer le total, vérifiez les montants 🙀"
            else:
                reponse = "Aucune facture chargée pour l'instant 🐱"

        elif any(w in q for w in ["fournisseur", "qui", "vendeur"]):
            if factures_data:
                fournisseurs = list(set(r.get("fournisseur", "?") for r in factures_data))
                reponse = f"📋 Fournisseurs : **{', '.join(fournisseurs)}** 🐾"
            else:
                reponse = "Aucune facture chargée 🐱"

        elif any(w in q for w in ["combien", "nombre", "facture"]):
            n = len(factures_data) if factures_data else 0
            reponse = f"📄 Vous avez **{n} facture(s)** chargée(s) 🐾"

        elif any(w in q for w in ["note", "frais", "dépense"]):
            n = len(notes_frais_data) if notes_frais_data else 0
            reponse = f"💳 Vous avez **{n} note(s) de frais** enregistrée(s) 🐾"

        elif any(w in q for w in ["catégorie", "categorie", "type"]):
            if factures_data:
                cats = {}
                for r in factures_data:
                    c = r.get("categorie", "Autres")
                    cats[c] = cats.get(c, 0) + 1
                detail = ", ".join(f"{k}: {v}" for k, v in cats.items())
                reponse = f"📂 Catégories : {detail} 🐾"
            else:
                reponse = "Aucune facture chargée 🐱"

        elif any(w in q for w in ["attente", "valider", "statut"]):
            if factures_data:
                en_attente = [r for r in factures_data if "attente" in str(r.get("statut", "")).lower()]
                reponse = f"⏳ **{len(en_attente)} facture(s)** en attente de validation 🐾"
            else:
                reponse = "Aucune facture chargée 🐱"

        elif any(w in q for w in ["bonjour", "salut", "hello", "coucou"]):
            reponse = "Miaou ! 🐾 Bonjour ! Je suis FactureCat, votre assistant comptable félin. Comment puis-je vous aider ?"

        elif any(w in q for w in ["aide", "help", "quoi", "que sais"]):
            reponse = ("Je peux vous aider avec 🐾 :\n"
                       "• **total** → montant total TTC\n"
                       "• **fournisseurs** → liste des fournisseurs\n"
                       "• **combien** → nombre de factures\n"
                       "• **catégories** → répartition par catégorie\n"
                       "• **statut** → factures en attente\n"
                       "• **notes de frais** → vos dépenses")

        # Fallback Gemini
        if reponse is None:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model_chat = genai.GenerativeModel("gemini-2.5-flash")
                system_ctx = f"""Tu es FactureCat 🐱, un assistant comptable félin sympathique.
Tu réponds en français, de façon concise et avec des emojis chat.
{ctx_factures}
{ctx_notes}"""
                full_prompt = f"{system_ctx}\n\nQuestion: {user_input}"
                resp = model_chat.generate_content(full_prompt)
                reponse = resp.text
            except:
                reponse = "Miaou... Je n'arrive pas à répondre pour l'instant 🙀 Réessayez !"

        st.session_state["chat_history"].append({"role": "assistant", "content": reponse})
        st.rerun()

    # Bouton effacer historique
    if st.session_state["chat_history"]:
        if st.button("🗑️ Effacer la conversation", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size: 3rem;">🐱</div>
        <h2 style="color:#a0522d; margin:0;">FactureCat</h2>
        <p style="color:#c8956c; font-size:0.85rem;">Votre assistant comptable félin</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📂 Navigation")
    page = st.radio("", ["📄 Factures", "💰 Notes de frais"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    api_key = st.secrets["GEMINI_API_KEY"]

    st.markdown("---")
    mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    now = datetime.now()
    mois_choisi  = mois_list[now.month - 1]
    annee_choisie = now.year

    if page == "📄 Factures":
        st.markdown("""
        <div class="card">
            <p style="color:#a0522d;font-weight:700;margin:0 0 0.5rem 0;">📖 Guide rapide</p>
            <p style="color:#c8956c;font-size:0.85rem;margin:0;">
            1. 📁 Uploadez vos factures<br>
            2. 🚀 Lancez l'extraction<br>
            3. ✏️ Vérifiez les données<br>
            4. 📥 Exportez en Excel
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card">
            <p style="color:#a0522d;font-weight:700;margin:0 0 0.5rem 0;">📖 Guide rapide</p>
            <p style="color:#c8956c;font-size:0.85rem;margin:0;">
            1. ➕ Ajoutez une dépense<br>
            2. 📸 Joignez le justificatif<br>
            3. ✏️ Vérifiez les données<br>
            4. 📥 Exportez en Excel
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center; margin-top:1rem;">
        <div style="font-size:0.9rem;">{ascii_to_html(CAT_ASCII_PETIT)}</div>
        <p style="color:#d4a882;font-size:0.75rem;margin-top:0.3rem;">
            Miaouu~ je veille sur vos dépenses
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
if page == "📄 Factures":

    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:4rem;">🐱</div>
        <h1 style="margin:0;">FactureCat</h1>
        <p style="color:#c8956c;margin:0.5rem 0 0 0;font-size:1.1rem;">
            Extraction intelligente de factures 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)

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
        type=["pdf","jpg","jpeg","png"],
        accept_multiple_files=True,
        help="Formats acceptés : PDF, JPG, PNG"
    )

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

    if fichiers:
        # ── Anti-doublon ──────────────────────────────────────────────────────
        ids_actuels = [f.name + str(f.size) for f in fichiers]
        noms_actuels = [f.name for f in fichiers]

        # Nettoyer les résultats des fichiers supprimés
        if "resultats" in st.session_state:
            st.session_state["resultats"] = [
                r for r in st.session_state["resultats"]
                if r.get("fichier", "") in noms_actuels
            ]

        fichiers_ont_change = (ids_actuels != st.session_state.get("fichiers_ids", []))

        st.markdown(f"""
        <div class="card" style="background:linear-gradient(135deg,#fff8f3,#fdf0e8);">
            <span style="color:#a0522d;font-weight:700;">
                🐱 Miaou ! {len(fichiers)} fichier(s) détecté(s) 🐾
            </span>
        </div>
        """, unsafe_allow_html=True)

        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            lancer = st.button("🐾 Lancer l'extraction !", type="primary", use_container_width=True)

        if fichiers_ont_change and "resultats" in st.session_state:
            st.warning("⚠️ Fichiers modifiés. Clique sur **Lancer l'extraction** pour analyser !")

        doit_extraire = lancer and fichiers_ont_change

        if doit_extraire:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            st.markdown("""
            <div class="cat-container">
                <div style="font-size:2.5rem;">😺</div>
                <div class="chat-bubble">
                    <span style="color:#a0522d;font-weight:700;">
                        Je suis sur le coup ! Analyse en cours... 🐾
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            progress = st.progress(0)

            # Garder les résultats existants, n'extraire que les nouveaux
            if "resultats" not in st.session_state:
                st.session_state["resultats"] = []

            deja_extraits = [r.get("fichier", "") for r in st.session_state["resultats"]]

            for i, fichier in enumerate(fichiers):
                if fichier.name not in deja_extraits:
                    try:
                        data = extraire_facture(fichier, model, mois_choisi, annee_choisie)
                        data["fichier"] = fichier.name
                        data["statut"] = "À vérifier 🐱"
                        st.session_state["resultats"].append(data)
                    except Exception as e:
                        st.session_state["resultats"].append({
                            "fichier": fichier.name,
                            "date": "", "fournisseur": "Erreur extraction",
                            "numero_facture": "", "montant_ht": "",
                            "tva": "", "montant_ttc": "",
                            "description": str(e),
                            "categorie": "Autres", "statut": "Erreur 🙀"
                        })
                progress.progress((i + 1) / len(fichiers))

            progress.empty()
            st.session_state["fichiers_ids"] = ids_actuels
            st.session_state["mois"] = mois_choisi
            st.session_state["annee"] = annee_choisie
            st.session_state["scroll_to_dashboard"] = True
            st.rerun()

        # ── Affichage résultats ────────────────────────────────────────────────
        if "resultats" in st.session_state and st.session_state["resultats"]:
            resultats = st.session_state["resultats"]

            st.markdown("""
            <div class="cat-container">
                <div style="font-size:2.5rem;">😻</div>
                <div class="chat-bubble">
                    <span style="color:#a0522d;font-weight:700;">
                        Purrrfect ! Voici ce que j'ai trouvé 🐾
                    </span><br>
                    <span style="color:#c8956c;">Vous pouvez modifier directement dans le tableau !</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div id="dashboard"></div>', unsafe_allow_html=True)

            col_p1, col_p2, _ = st.columns([2, 2, 4])
            with col_p1:
                mois_rapide = st.selectbox("📅 Mois", mois_list,
                    index=mois_list.index(st.session_state.get("mois", mois_choisi)))
            with col_p2:
                annee_rapide = st.selectbox("📅 Année", list(range(2023, 2031)),
                    index=list(range(2023, 2031)).index(
                        st.session_state.get("annee", annee_choisie)))

            df = pd.DataFrame(resultats)
            df = df.rename(columns={
                "fichier": "Fichier", "date": "Date",
                "fournisseur": "Fournisseur", "numero_facture": "N° Facture",
                "montant_ht": "Montant HT (€)", "tva": "TVA (€)",
                "montant_ttc": "Montant TTC (€)", "description": "Description",
                "categorie": "Catégorie", "statut": "Statut"
            })
            df["Mois"]  = mois_rapide
            df["Année"] = annee_rapide
            colonnes_ordre = ["Fichier","Date","Mois","Année","Fournisseur",
                              "N° Facture","Montant HT (€)","TVA (€)",
                              "Montant TTC (€)","Catégorie","Description","Statut"]
            df = df[colonnes_ordre]

            # ── Tableau éditable stylé ────────────────────────────────────────
            st.markdown("""
            <div style="
                background:white; border-radius:20px;
                box-shadow:0 4px 20px rgba(200,149,108,0.15);
                border:2px solid #f0d5c0; overflow:hidden;
                margin-bottom:1rem;
            ">
                <div style="
                    background:linear-gradient(135deg,#f0a070,#e8856a);
                    padding:0.8rem 1.5rem;
                ">
                    <span style="color:white;font-weight:800;font-size:1rem;">
                        📋 Tableau des factures — cliquez pour modifier
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            df_edit = st.data_editor(
                df, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut 🏷️",
                        options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]
                    ),
                    "Catégorie": st.column_config.SelectboxColumn(
                        "Catégorie 📂",
                        options=["Transport","Repas","Hébergement","Fournitures","Services","Autres"]
                    ),
                    "Montant HT (€)": st.column_config.NumberColumn("Montant HT (€)", format="%.2f €"),
                    "TVA (€)":        st.column_config.NumberColumn("TVA (€)",        format="%.2f €"),
                    "Montant TTC (€)":st.column_config.NumberColumn("Montant TTC (€)",format="%.2f €"),
                },
                key="editor_factures"
            )

            if st.session_state.get("scroll_to_dashboard"):
                components.html(
                    "<script>setTimeout(()=>{"
                    "try{window.parent.document.getElementById('dashboard')"
                    ".scrollIntoView({behavior:'smooth'});}catch(e){}"
                    "},150);</script>", height=0
                )
                st.session_state["scroll_to_dashboard"] = False

            # ── Dashboard stats ───────────────────────────────────────────────
            st.markdown("### 📊 Tableau de bord")
            col1, col2, col3, col4 = st.columns(4)

            def safe_sum(series):
                total = 0
                for v in series:
                    try: total += float(str(v).replace(",",".") or 0)
                    except: pass
                return total

            total_ht  = safe_sum(df_edit["Montant HT (€)"])
            total_tva = safe_sum(df_edit["TVA (€)"])
            total_ttc = safe_sum(df_edit["Montant TTC (€)"])
            nb_valides = len(df_edit[df_edit["Statut"] == "Validé 😸"])

            with col1:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">📄</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">{len(resultats)}</div>
                    <div style="color:#c8956c;">Factures</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">💶</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">{total_ht:.2f}€</div>
                    <div style="color:#c8956c;">Total HT</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">💰</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">{total_ttc:.2f}€</div>
                    <div style="color:#c8956c;">Total TTC</div>
                </div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="card-green" style="text-align:center;">
                    <div style="font-size:2rem;">✅</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#2d5a2d;">{nb_valides}</div>
                    <div style="color:#7fc87f;">Validées</div>
                </div>""", unsafe_allow_html=True)

            # ── Visualisation factures ────────────────────────────────────────
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

            # ── Export Excel ──────────────────────────────────────────────────
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

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":

    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:4rem;">💰</div>
        <h1 style="margin:0;">Notes de Frais</h1>
        <p style="color:#c8956c;margin:0.5rem 0 0 0;font-size:1.1rem;">
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
            nf_date      = st.date_input("📅 Date", value=datetime.now())
            nf_employe   = st.text_input("👤 Employé")
            nf_categorie = st.selectbox("📂 Catégorie",
                ["Transport","Repas","Hébergement","Fournitures","Services","Autres"])
            nf_moyen_paiement = st.selectbox("💳 Moyen de paiement",
                ["Carte bancaire","Espèces","Virement","Chèque"])
        with col2:
            nf_description = st.text_area("📝 Description", height=100)
            nf_montant_ht  = st.number_input("💶 Montant HT (€)", min_value=0.0, step=0.01)
            nf_tva         = st.selectbox("🧾 TVA (%)", [0, 5.5, 10, 20])
            nf_montant_tva = round(nf_montant_ht * nf_tva / 100, 2)
            nf_montant_ttc = round(nf_montant_ht + nf_montant_tva, 2)
            st.markdown(f"""
            <div class="card" style="padding:0.8rem;">
                <span style="color:#c8956c;">TVA : <strong>{nf_montant_tva:.2f} €</strong></span><br>
                <span style="color:#a0522d;font-size:1.1rem;">
                    TTC : <strong>{nf_montant_ttc:.2f} €</strong>
                </span>
            </div>
            """, unsafe_allow_html=True)
            nf_justificatif = st.file_uploader("📎 Justificatif",
                type=["pdf","jpg","jpeg","png"])

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
                    "TVA (%)": nf_tva,
                    "Montant TVA (€)": nf_montant_tva,
                    "Montant TTC (€)": nf_montant_ttc,
                    "Moyen de paiement": nf_moyen_paiement,
                    "Justificatif": nf_justificatif.name if nf_justificatif else "—",
                    "Statut": "En attente 😺"
                }
                st.session_state["notes_frais"].append(nouvelle_note)
                st.success("✅ Dépense ajoutée avec succès ! 🐾")
                st.rerun()

    # ── Tableau notes de frais ─────────────────────────────────────────────────
    if st.session_state["notes_frais"]:
        st.markdown("---")

        st.markdown("""
        <div class="cat-container">
            <div style="font-size:2.5rem;">😻</div>
            <div class="chat-bubble">
                <span style="color:#a0522d;font-weight:700;">Vos notes de frais 🐾</span><br>
                <span style="color:#c8956c;">Modifiez directement dans le tableau !</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_nf = pd.DataFrame(st.session_state["notes_frais"])

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtre_employe = st.text_input("🔍 Filtrer par employé", "")
        with col_f2:
            filtre_categorie = st.selectbox("📂 Catégorie",
                ["Toutes"] + list(df_nf["Catégorie"].unique()))
        with col_f3:
            filtre_statut = st.selectbox("🏷️ Statut",
                ["Tous","En attente 😺","Validé 😸","Refusé 🙀"])

        df_filtre = df_nf.copy()
        if filtre_employe:
            df_filtre = df_filtre[
                df_filtre["Employé"].str.contains(filtre_employe, case=False)]
        if filtre_categorie != "Toutes":
            df_filtre = df_filtre[df_filtre["Catégorie"] == filtre_categorie]
        if filtre_statut != "Tous":
            df_filtre = df_filtre[df_filtre["Statut"] == filtre_statut]

        # Stats rapides
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                    {len(df_filtre)}
                </div>
                <div style="color:#c8956c;">Dépenses</div>
            </div>""", unsafe_allow_html=True)
        with col_s2:
            total_nf = df_filtre["Montant HT (€)"].sum()
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                    {total_nf:.2f}€
                </div>
                <div style="color:#c8956c;">Total HT</div>
            </div>""", unsafe_allow_html=True)
        with col_s3:
            total_ttc_nf = df_filtre["Montant TTC (€)"].sum()
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                    {total_ttc_nf:.2f}€
                </div>
                <div style="color:#c8956c;">Total TTC</div>
            </div>""", unsafe_allow_html=True)

        # Tableau éditable stylé
        st.markdown("""
        <div style="
            background:white; border-radius:20px;
            box-shadow:0 4px 20px rgba(200,149,108,0.15);
            border:2px solid #f0d5c0; overflow:hidden;
            margin-bottom:1rem;
        ">
            <div style="
                background:linear-gradient(135deg,#f0a070,#e8856a);
                padding:0.8rem 1.5rem;
            ">
                <span style="color:white;font-weight:800;font-size:1rem;">
                    💳 Notes de frais — cliquez pour modifier
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        edited_nf = st.data_editor(
            df_filtre, use_container_width=True, hide_index=True,
            column_config={
                "Statut": st.column_config.SelectboxColumn(
                    "Statut 🏷️",
                    options=["En attente 😺","Validé 😸","Refusé 🙀","Remboursé 💸"]
                ),
                "Catégorie": st.column_config.SelectboxColumn(
                    "Catégorie 📂",
                    options=["Transport","Repas","Hébergement","Fournitures","Services","Autres"]
                ),
                "Montant HT (€)":  st.column_config.NumberColumn(format="%.2f €"),
                "Montant TVA (€)": st.column_config.NumberColumn(format="%.2f €"),
                "Montant TTC (€)": st.column_config.NumberColumn(format="%.2f €"),
            },
            key="editor_notes"
        )
        st.session_state["notes_frais"] = edited_nf.to_dict("records")

        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            buffer_nf = io.BytesIO()
            edited_nf.to_excel(buffer_nf, index=False, engine="openpyxl")
            buffer_nf.seek(0)
            st.download_button(
                "📥 Exporter Excel 🐾", data=buffer_nf,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_act2:
            csv_nf = edited_nf.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📄 Exporter CSV", data=csv_nf,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.csv",
                mime="text/csv", use_container_width=True
            )
        with col_act3:
            if st.button("🗑️ Effacer tout", use_container_width=True):
                st.session_state["notes_frais"] = []
                st.rerun()

    else:
        st.markdown(f"""
        <div style="text-align:center; padding:3rem 0;">
            <div style="font-size:3rem;">🐱</div>
            <p style="font-size:1.2rem;font-weight:700;color:#a0522d;">
                Aucune note de frais pour l'instant !
            </p>
            <p style="color:#c8956c;">
                Ajoutez votre première dépense avec le formulaire ci-dessus 🐾
            </p>
        </div>
        """, unsafe_allow_html=True)

# ─── FOOTER + CHATBOT FLOTTANT ────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:1rem 0;">
    <p style="font-weight:900;color:#a0522d;font-size:1.1rem;">Purrrfait travail ! 🐾</p>
    <p style="color:#c8956c;font-size:0.88rem;">FactureCat — Votre comptable félin 🐱</p>
</div>
""", unsafe_allow_html=True)

# Chat flottant toujours présent
render_chat_widget(
    notes_frais_data=st.session_state.get("notes_frais", []),
    factures_data=st.session_state.get("resultats", [])
)
