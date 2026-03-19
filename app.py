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
                    st.error("❌ Email ou mot de passe incorrect 🙀")

    return False

if not check_password():
    st.stop()

# ─── CONFIG GEMINI ────────────────────────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def pdf_to_image(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    mat  = fitz.Matrix(2, 2)
    pix  = page.get_pixmap(matrix=mat)
    return Image.open(io.BytesIO(pix.tobytes("png")))

def pdf_to_images(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    imgs = []
    mat  = fitz.Matrix(2, 2)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return imgs

def analyze_invoice(file_bytes, file_type):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        if file_type == "application/pdf":
            img = pdf_to_image(file_bytes)
        else:
            img = Image.open(io.BytesIO(file_bytes))
        prompt = """Analyse cette facture et extrais en JSON :
{
  "fournisseur": "",
  "date": "JJ/MM/AAAA",
  "numero_facture": "",
  "montant_ht": 0.0,
  "tva": 0.0,
  "montant_ttc": 0.0,
  "categorie": "",
  "description": "",
  "statut": "En attente"
}
Réponds UNIQUEMENT avec le JSON."""
        resp = model.generate_content([prompt, img])
        txt  = resp.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(txt)
    except Exception as e:
        st.error(f"Erreur analyse : {e}")
        return None

# ─── ASCII ART ────────────────────────────────────────────────────────────────
CAT_ASCII_GRAND = (
    "  /\\_____/\\\n"
    " /  o   o  \\\n"
    "(  ==  ^  == )\n"
    " )          (\n"
    "(            )\n"
    "( (        ) )\n"
    "(__(__))___(__))__)"
)

def ascii_to_html(ascii_art: str) -> str:
    return ascii_art.replace("\n", "<br>")

# ─── CHAT WIDGET FLOTTANT ─────────────────────────────────────────────────────
def render_chat_widget(notes_frais_data=None, factures_data=None):
    notes_json    = json.dumps(notes_frais_data or [])
    factures_json = json.dumps(factures_data    or [])
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
    * {{ box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
    body {{ margin:0; padding:0; background:transparent; }}

    #fab {{
        position:fixed; bottom:2rem; right:2rem;
        width:60px; height:60px; border-radius:50%;
        background:linear-gradient(135deg,#f0a070,#e07040);
        border:none; cursor:pointer; font-size:1.8rem;
        box-shadow:0 4px 20px rgba(240,112,64,0.45);
        z-index:9999; transition:transform .2s;
        display:flex; align-items:center; justify-content:center;
    }}
    #fab:hover {{ transform:scale(1.12); }}

    #chatbox {{
        position:fixed; bottom:5.5rem; right:2rem; width:340px;
        background:#fffaf7; border-radius:20px;
        box-shadow:0 12px 40px rgba(0,0,0,0.18);
        z-index:9998; display:none; flex-direction:column;
        max-height:500px; overflow:hidden;
        border:1.5px solid rgba(240,160,112,0.35);
    }}
    #chat-header {{
        background:linear-gradient(135deg,#f0a070,#e07040);
        padding:1rem 1.2rem; border-radius:20px 20px 0 0;
        color:white; font-weight:800; font-size:1rem;
        display:flex; align-items:center; gap:0.5rem;
    }}
    #chat-close {{
        margin-left:auto; cursor:pointer; font-size:1.1rem;
        background:none; border:none; color:white;
    }}
    #chat-messages {{
        flex:1; overflow-y:auto; padding:1rem;
        display:flex; flex-direction:column; gap:0.7rem;
        max-height:330px;
    }}
    .msg-bot {{
        background:#fff0e6; border-radius:12px 12px 12px 0;
        padding:0.7rem 1rem; font-size:0.84rem; color:#7a3a10;
        border:1px solid #f5d5b8; max-width:90%; align-self:flex-start;
        line-height:1.5;
    }}
    .msg-user {{
        background:linear-gradient(135deg,#f0a070,#e07040);
        border-radius:12px 12px 0 12px;
        padding:0.7rem 1rem; font-size:0.84rem; color:white;
        max-width:85%; align-self:flex-end;
    }}
    #chat-input-row {{
        display:flex; padding:0.8rem; gap:0.5rem;
        border-top:1px solid #f5e0d0; background:white;
        border-radius:0 0 20px 20px;
    }}
    #chat-input {{
        flex:1; border:1.5px solid #f0d0b8; border-radius:12px;
        padding:0.5rem 0.8rem; font-size:0.85rem; outline:none;
        background:#fffaf7;
    }}
    #chat-input:focus {{ border-color:#f0a070; }}
    #chat-send {{
        background:linear-gradient(135deg,#f0a070,#e07040);
        border:none; border-radius:12px; padding:0.5rem 0.9rem;
        color:white; cursor:pointer; font-size:1rem;
        transition:transform .15s;
    }}
    #chat-send:hover {{ transform:scale(1.08); }}
    </style>
    </head>
    <body>

    <button id="fab" onclick="toggleChat()">🐱</button>

    <div id="chatbox">
        <div id="chat-header">
            🐾 FactureCat Assistant
            <button id="chat-close" onclick="toggleChat()">✕</button>
        </div>
        <div id="chat-messages">
            <div class="msg-bot">
                Miaou ! 🐱 Je suis <b>FactureCat</b> !<br>
                Pose-moi des questions sur tes <b>factures</b> ou <b>notes de frais</b>.<br>
                Tape <b>aide</b> pour voir les commandes 🐾
            </div>
        </div>
        <div id="chat-input-row">
            <input id="chat-input" type="text"
                placeholder="Pose une question..."
                onkeypress="if(event.key==='Enter') sendMsg()"/>
            <button id="chat-send" onclick="sendMsg()">➤</button>
        </div>
    </div>

    <script>
    const notesData    = {notes_json};
    const facturesData = {factures_json};

    function toggleChat() {{
        const box = document.getElementById('chatbox');
        box.style.display = (box.style.display === 'flex') ? 'none' : 'flex';
    }}

    function addMsg(text, who) {{
        const d = document.getElementById('chat-messages');
        const m = document.createElement('div');
        m.className = who === 'bot' ? 'msg-bot' : 'msg-user';
        m.innerHTML = text;
        d.appendChild(m);
        d.scrollTop = d.scrollHeight;
    }}

    function sendMsg() {{
        const inp = document.getElementById('chat-input');
        const txt = inp.value.trim();
        if (!txt) return;
        addMsg(txt, 'user');
        inp.value = '';
        setTimeout(() => addMsg(getReply(txt), 'bot'), 300);
    }}

    function getReply(msg) {{
        const m = msg.toLowerCase();

        // ── AIDE ──────────────────────────────────────────────────────────────
        if (m.includes('aide') || m.includes('help')) {{
            return `🐱 Commandes disponibles :<br>
            <b>Notes de frais :</b><br>
            • <b>total</b> — total des dépenses<br>
            • <b>catégories</b> — répartition par catégorie<br>
            • <b>plus grosse</b> — dépense la plus élevée<br>
            • <b>combien</b> — nombre de dépenses<br><br>
            <b>Factures :</b><br>
            • <b>total factures</b> — total TTC factures<br>
            • <b>fournisseurs</b> — liste des fournisseurs<br>
            • <b>en attente</b> — factures non validées`;
        }}

        // ── NOTES DE FRAIS ────────────────────────────────────────────────────
        if (m.includes('total') && !m.includes('facture')) {{
            if (notesData.length === 0) return "Aucune dépense enregistrée 🐱";
            const t = notesData.reduce((s,n) => s + (parseFloat(n.montant)||0), 0);
            return `💶 Total des dépenses : <b>${{t.toFixed(2)}} €</b> 🐾`;
        }}

        if (m.includes('catégor') || m.includes('categor')) {{
            if (notesData.length === 0) return "Aucune dépense enregistrée 🐱";
            const cats = {{}};
            notesData.forEach(n => {{
                const c = n.categorie || 'Autre';
                cats[c] = (cats[c]||0) + (parseFloat(n.montant)||0);
            }});
            const lines = Object.entries(cats)
                .sort((a,b) => b[1]-a[1])
                .map(([c,v]) => `• ${{c}}: <b>${{v.toFixed(2)}} €</b>`).join('<br>');
            return `📂 Répartition :<br>${{lines}}`;
        }}

        if (m.includes('plus') && (m.includes('gros') || m.includes('élevé') || m.includes('grand'))) {{
            if (notesData.length === 0) return "Aucune dépense enregistrée 🐱";
            const max = notesData.reduce((a,b) =>
                (parseFloat(a.montant)||0) > (parseFloat(b.montant)||0) ? a : b);
            return `🏆 Plus grosse dépense : <b>${{max.description||max.categorie}}</b> → <b>${{parseFloat(max.montant).toFixed(2)}} €</b> 🐾`;
        }}

        if (m.includes('combien')) {{
            return `📊 Tu as <b>${{notesData.length}}</b> dépense(s) enregistrée(s) 🐾`;
        }}

        // ── FACTURES ──────────────────────────────────────────────────────────
        if (m.includes('total') && m.includes('facture')) {{
            if (facturesData.length === 0) return "Aucune facture enregistrée 🐱";
            const t = facturesData.reduce((s,f) => s + (parseFloat(f["Montant TTC (€)"])||0), 0);
            return `🧾 Total TTC factures : <b>${{t.toFixed(2)}} €</b> 🐾`;
        }}

        if (m.includes('fournisseur')) {{
            if (facturesData.length === 0) return "Aucune facture 🐱";
            const fournisseurs = [...new Set(facturesData.map(f => f.Fournisseur).filter(Boolean))];
            return `🏢 Fournisseurs :<br>` + fournisseurs.map(f => `• ${{f}}`).join('<br>');
        }}

        if (m.includes('attente') || m.includes('validé') || m.includes('statut')) {{
            if (facturesData.length === 0) return "Aucune facture 🐱";
            const att = facturesData.filter(f => (f.Statut||'').includes('attente'));
            return `⏳ Factures en attente : <b>${{att.length}}</b> sur ${{facturesData.length}} 🐾`;
        }}

        // ── DEFAULT ───────────────────────────────────────────────────────────
        const replies = [
            "Miaou ! 🐱 Je ne comprends pas encore. Tape <b>aide</b> !",
            "Purrrr... 🐾 Essaie <b>total</b> ou <b>catégories</b> !",
            "🐱 Tape <b>aide</b> pour voir mes commandes !"
        ];
        return replies[Math.floor(Math.random()*replies.length)];
    }}
    </script>
    </body>
    </html>
    """
    components.html(html, height=600, scrolling=False)

# ─── CSS GLOBAL ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #fdf6f0;
}

/* ── CARDS ── */
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

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: white; border-radius: 20px;
    padding: 1rem; border: 2px dashed #f0a070;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #f0a070, #e8856a, #c8956c);
    border-radius: 10px;
}

/* ── TABLEAU DATA EDITOR ── */
[data-testid="stDataEditor"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 2px solid #f5e6d8 !important;
    box-shadow: 0 4px 20px rgba(200,149,108,0.12) !important;
}
[data-testid="stDataEditor"] table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
}
[data-testid="stDataEditor"] thead tr th {
    background: linear-gradient(135deg, #f0a070, #e07040) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    padding: 0.7rem 0.8rem !important;
    border: none !important;
}
[data-testid="stDataEditor"] tbody tr:nth-child(even) td {
    background: #fff8f3 !important;
}
[data-testid="stDataEditor"] tbody tr:hover td {
    background: #ffeedd !important;
    transition: background 0.2s;
}
[data-testid="stDataEditor"] tbody tr td {
    font-size: 0.83rem !important;
    padding: 0.55rem 0.8rem !important;
    border-bottom: 1px solid #f5e6d8 !important;
    color: #5a3020 !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: white; border-radius: 12px;
    border: 2px solid #f0d5c0;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff8f3 0%, #fdf0e8 100%);
    border-right: 2px solid #f5e6d8;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #f0a070, #e07040);
    color: white; border: none; border-radius: 12px;
    font-weight: 700; padding: 0.5rem 1.2rem;
    transition: transform .15s, box-shadow .15s;
}
.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 15px rgba(224,112,64,0.35);
}

/* ── CHAT BUBBLE ── */
.chat-bubble {
    background: white; border-radius: 20px 20px 20px 4px;
    padding: 1rem 1.5rem;
    box-shadow: 0 4px 15px rgba(200,149,108,0.2);
    border: 2px solid #f5e6d8;
    display: inline-block; margin-left: 1rem;
}
.cat-container { display: flex; align-items: center; margin: 1rem 0; }

/* ── SECTION TITLE ── */
.section-title {
    font-size: 1.2rem; font-weight: 800; color: #a0522d;
    margin-bottom: 1rem; padding-bottom: 0.5rem;
    border-bottom: 2px solid #f5e6d8;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "notes_frais"  not in st.session_state: st.session_state["notes_frais"]  = []
if "fichiers_ids" not in st.session_state: st.session_state["fichiers_ids"] = []
if "resultats"    not in st.session_state: st.session_state["resultats"]    = []

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:3rem;">🐱</div>
        <h2 style="color:#a0522d; margin:0;">FactureCat</h2>
        <p style="color:#c8956c; font-size:0.85rem;">Votre assistant comptable félin</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("", ["📄 Factures", "💰 Notes de frais"],
                    label_visibility="collapsed")
    st.markdown("---")

    api_key = st.secrets["GEMINI_API_KEY"]

    mois_list    = ["Janvier","Février","Mars","Avril","Mai","Juin",
                    "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    now          = datetime.now()
    mois_choisi  = mois_list[now.month - 1]
    annee_choisie = now.year

    st.markdown("---")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
if page == "📄 Factures":

    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:4rem;">🐱</div>
        <h1 style="margin:0; color:#a0522d;">FactureCat</h1>
        <p style="color:#c8956c; margin:0.5rem 0 0 0; font-size:1.1rem;">
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
                Déposez vos factures ci-dessous et je m'occupe de tout !
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

    lancer = st.button("🔍 Analyser les factures", use_container_width=True)

    if fichiers:
        ids_actuels = [f.name + str(f.size) for f in fichiers]
        fichiers_ont_change = (ids_actuels != st.session_state["fichiers_ids"])

        doit_extraire = lancer and fichiers_ont_change

        if doit_extraire or (
            "resultats" in st.session_state
            and st.session_state["resultats"]
            and not fichiers_ont_change
        ):
            if doit_extraire:
                genai.configure(api_key=api_key)

                st.markdown("""
                <div class="cat-container">
                    <div style="font-size:2.5rem;">😺</div>
                    <div class="chat-bubble">
                        <span style="color:#a0522d; font-weight:700;">
                            Analyse en cours... 🐾
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                progress = st.progress(0)
                resultats = []

                for i, fichier in enumerate(fichiers):
                    fichier.seek(0)
                    data = analyze_invoice(fichier.read(), fichier.type)
                    if data:
                        data["fichier"] = fichier.name
                        resultats.append(data)
                    progress.progress((i + 1) / len(fichiers))

                st.session_state["resultats"]    = resultats
                st.session_state["fichiers_ids"] = ids_actuels
                st.success(f"✅ {len(resultats)} facture(s) analysée(s) !")

            resultats = st.session_state["resultats"]

            if resultats:
                # ── SÉLECTEURS MOIS / ANNÉE ───────────────────────────────────
                col_p1, col_p2, _ = st.columns([2, 2, 4])
                with col_p1:
                    mois_rapide = st.selectbox("📅 Mois", mois_list,
                        index=mois_list.index(st.session_state.get("mois", mois_choisi)))
                with col_p2:
                    annee_rapide = st.selectbox("📅 Année", list(range(2023,2031)),
                        index=list(range(2023,2031)).index(
                            st.session_state.get("annee", annee_choisie)))

                # ── DATAFRAME ─────────────────────────────────────────────────
                df = pd.DataFrame(resultats)
                df = df.rename(columns={
                    "fichier":"Fichier","date":"Date","fournisseur":"Fournisseur",
                    "numero_facture":"N° Facture","montant_ht":"Montant HT (€)",
                    "tva":"TVA (€)","montant_ttc":"Montant TTC (€)",
                    "description":"Description","categorie":"Catégorie","statut":"Statut"
                })
                df["Mois"]  = mois_rapide
                df["Année"] = annee_rapide
                df = df[["Fichier","Date","Mois","Année","Fournisseur","N° Facture",
                         "Montant HT (€)","TVA (€)","Montant TTC (€)",
                         "Catégorie","Description","Statut"]]

                # ── KPI CARDS ─────────────────────────────────────────────────
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="card" style="text-align:center;">
                        <div style="font-size:2.5rem;">🧾</div>
                        <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                            {len(resultats)}
                        </div>
                        <div style="color:#c8956c;">Facture(s)</div>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    valides = sum(1 for r in resultats if "valid" in str(r.get("statut","")).lower())
                    st.markdown(f"""
                    <div class="card" style="text-align:center;">
                        <div style="font-size:2.5rem;">✅</div>
                        <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                            {valides}
                        </div>
                        <div style="color:#c8956c;">Validée(s)</div>
                    </div>""", unsafe_allow_html=True)
                with col3:
                    attente = sum(1 for r in resultats if "attente" in str(r.get("statut","")).lower())
                    st.markdown(f"""
                    <div class="card" style="text-align:center;">
                        <div style="font-size:2.5rem;">⏳</div>
                        <div style="font-size:1.8rem;font-weight:800;color:#a0522d;">
                            {attente}
                        </div>
                        <div style="color:#c8956c;">En attente</div>
                    </div>""", unsafe_allow_html=True)
                with col4:
                    try:
                        total = sum(float(r.get("montant_ttc",0) or 0) for r in resultats)
                        total_str = f"{total:,.2f} €"
                    except:
                        total_str = "N/A"
                    st.markdown(f"""
                    <div class="card" style="text-align:center;">
                        <div style="font-size:2.5rem;">💰</div>
                        <div style="font-size:1.5rem;font-weight:800;color:#a0522d;">
                            {total_str}
                        </div>
                        <div style="color:#c8956c;">Total TTC</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── TABLEAU ÉDITABLE ──────────────────────────────────────────
                st.markdown("""
                <div class="section-title">📋 Tableau des factures — modifiable</div>
                """, unsafe_allow_html=True)

                df_edit = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="fixed",
                    column_config={
                        "Fichier":        st.column_config.TextColumn("📎 Fichier",    disabled=True),
                        "Date":           st.column_config.TextColumn("📅 Date"),
                        "Mois":           st.column_config.SelectboxColumn(
                                            "🗓️ Mois", options=mois_list),
                        "Année":          st.column_config.NumberColumn(
                                            "📆 Année", min_value=2020, max_value=2035, step=1),
                        "Fournisseur":    st.column_config.TextColumn("🏢 Fournisseur"),
                        "N° Facture":     st.column_config.TextColumn("🔢 N° Facture"),
                        "Montant HT (€)": st.column_config.NumberColumn(
                                            "💶 HT", format="%.2f €"),
                        "TVA (€)":        st.column_config.NumberColumn(
                                            "🏷️ TVA", format="%.2f €"),
                        "Montant TTC (€)":st.column_config.NumberColumn(
                                            "💰 TTC", format="%.2f €"),
                        "Catégorie":      st.column_config.SelectboxColumn(
                                            "📂 Catégorie",
                                            options=["Fournitures","Services","Transport",
                                                     "Repas","Hébergement","Logiciel",
                                                     "Formation","Autre"]),
                        "Description":    st.column_config.TextColumn("📝 Description"),
                        "Statut":         st.column_config.SelectboxColumn(
                                            "🔖 Statut",
                                            options=["En attente","Validé ✅","Envoyé 📤","Refusé ❌"]),
                    },
                    key="editor_factures"
                )

                st.markdown("---")

                # ── VISUALISATION FACTURES ────────────────────────────────────
                st.markdown("""
                <div class="section-title">🖼️ Aperçu des factures</div>
                """, unsafe_allow_html=True)

                for idx, fichier in enumerate(fichiers):
                    with st.expander(f"📄 {fichier.name}", expanded=(idx == 0)):
                        fichier.seek(0)
                        if fichier.type == "application/pdf":
                            images = pdf_to_images(fichier.read())
                            st.image(images[0], use_container_width=True)
                            if len(images) > 1:
                                st.caption(f"📄 {len(images)} page(s)")
                        else:
                            st.image(Image.open(fichier), use_container_width=True)

                st.markdown("---")

                # ── EXPORT EXCEL ──────────────────────────────────────────────
                buffer = io.BytesIO()
                df_edit.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                col_dl = st.columns([1, 2, 1])
                with col_dl[1]:
                    st.download_button(
                        "📥 Télécharger Excel 🐾",
                        data=buffer,
                        file_name=f"factures_{mois_rapide}_{annee_rapide}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    else:
        st.markdown("""
        <div style="text-align:center; padding:2rem; color:#c8956c;">
            <div style="font-size:3rem;">☝️</div>
            <p style="font-size:1.1rem;">Uploadez vos factures ci-dessus pour commencer</p>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":

    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:4rem;">💰</div>
        <h1 style="margin:0; color:#a0522d;">Notes de Frais</h1>
        <p style="color:#c8956c; margin:0.5rem 0 0 0;">
            Gérez vos dépenses facilement 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_right = st.columns([1.2, 2.8])

    with col_left:
        st.markdown('<div class="section-title">➕ Nouvelle dépense</div>',
                    unsafe_allow_html=True)
        with st.form("form_note", clear_on_submit=True):
            desc   = st.text_input("📝 Description")
            mont   = st.number_input("💶 Montant (€)", min_value=0.0, step=0.01)
            cat    = st.selectbox("📂 Catégorie",
                        ["Repas","Transport","Hébergement","Matériel",
                         "Formation","Communication","Autre"])
            date_n = st.date_input("📅 Date", value=datetime.today())
            just   = st.file_uploader("📎 Justificatif", type=["pdf","png","jpg","jpeg"])
            submit = st.form_submit_button("✅ Ajouter", use_container_width=True)

            if submit and desc and mont > 0:
                st.session_state["notes_frais"].append({
                    "description":  desc,
                    "montant":      mont,
                    "categorie":    cat,
                    "date":         date_n.strftime("%d/%m/%Y"),
                    "justificatif": just.name if just else "—",
                    "statut":       "En attente",
                })
                st.success("✅ Dépense ajoutée !")
                st.rerun()

    with col_right:
        notes = st.session_state["notes_frais"]
        if notes:
            # KPI
            total_nf   = sum(float(n.get("montant",0)) for n in notes)
            valides_nf = sum(1 for n in notes if n.get("statut") == "Validé")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">🧾</div>
                    <div style="font-size:1.6rem;font-weight:800;color:#a0522d;">{len(notes)}</div>
                    <div style="color:#c8956c;">Dépense(s)</div>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">✅</div>
                    <div style="font-size:1.6rem;font-weight:800;color:#a0522d;">{valides_nf}</div>
                    <div style="color:#c8956c;">Validée(s)</div>
                </div>""", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-size:2rem;">💶</div>
                    <div style="font-size:1.4rem;font-weight:800;color:#a0522d;">{total_nf:.2f} €</div>
                    <div style="color:#c8956c;">Total</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # ── TABLEAU ÉDITABLE NOTES DE FRAIS ──────────────────────────────
            st.markdown("""
            <div class="section-title">📋 Mes dépenses — modifiable</div>
            """, unsafe_allow_html=True)

            df_nf = pd.DataFrame(notes)
            edited_nf = st.data_editor(
                df_nf,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "description":  st.column_config.TextColumn("📝 Description"),
                    "montant":      st.column_config.NumberColumn("💶 Montant", format="%.2f €"),
                    "categorie":    st.column_config.SelectboxColumn(
                                        "📂 Catégorie",
                                        options=["Repas","Transport","Hébergement",
                                                 "Matériel","Formation","Communication","Autre"]),
                    "date":         st.column_config.TextColumn("📅 Date"),
                    "justificatif": st.column_config.TextColumn("📎 Justificatif", disabled=True),
                    "statut":       st.column_config.SelectboxColumn(
                                        "🔖 Statut",
                                        options=["En attente","Validé","Remboursé","Refusé"]),
                },
                key="editor_notes"
            )
            st.session_state["notes_frais"] = edited_nf.to_dict("records")

            # Export
            buffer_nf = io.BytesIO()
            edited_nf.to_excel(buffer_nf, index=False, engine="openpyxl")
            buffer_nf.seek(0)
            col_dl2 = st.columns([1, 2, 1])
            with col_dl2[1]:
                st.download_button(
                    "📥 Exporter Notes de Frais",
                    data=buffer_nf,
                    file_name="notes_frais.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.markdown(f"""
            <div style="text-align:center; padding:3rem 0;">
                <div style="font-size:3rem;">🐱</div>
                <p style="font-size:1.2rem;font-weight:700;color:#a0522d;">
                    Aucune note de frais pour l'instant !
                </p>
                <p style="color:#c8956c;">
                    Ajoutez votre première dépense avec le formulaire 🐾
                </p>
            </div>
            """, unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:1rem 0;">
    <p style="font-weight:900; color:#a0522d; font-size:1.1rem;">Purrrfait travail ! 🐾</p>
    <p style="color:#c8956c; font-size:0.88rem;">FactureCat — Votre comptable félin 🐱</p>
</div>
""", unsafe_allow_html=True)

# ─── CHAT FLOTTANT ────────────────────────────────────────────────────────────
factures_pour_chat = (
    st.session_state["resultats"]
    if st.session_state.get("resultats") else []
)
render_chat_widget(
    notes_frais_data=st.session_state.get("notes_frais", []),
    factures_data=factures_pour_chat
)
