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

    if st.session_state["authenticated"]:
        return True

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="max-width:440px;margin:4rem auto;background:white;border-radius:24px;
         padding:3rem;box-shadow:0 20px 60px rgba(0,0,0,0.2);">
        <div style="text-align:center;margin-bottom:2rem;">
            <div style="font-size:3.5rem;">🐱</div>
            <h2 style="color:#1a1a2e;font-weight:800;margin:0.5rem 0 0 0;">FactureCat</h2>
            <p style="color:#6b7280;margin:0.3rem 0 0 0;font-size:0.9rem;">
                Votre comptable félin 🐾
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])
    with col[1]:
        mode = st.radio("", ["🔑 Connexion", "✨ Inscription"],
                        horizontal=True, label_visibility="collapsed")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")

        if mode == "✨ Inscription":
            password2 = st.text_input("Confirmer mot de passe", type="password")
            if st.button("Créer mon compte 🐾", use_container_width=True):
                if password != password2:
                    st.error("❌ Mots de passe différents !")
                elif len(password) < 6:
                    st.error("❌ Minimum 6 caractères !")
                else:
                    try:
                        res = get_supabase().auth.sign_up({"email": email, "password": password})
                        if res.user:
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = email
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
        else:
            if st.button("Se connecter 🐾", use_container_width=True):
                try:
                    res = get_supabase().auth.sign_in_with_password(
                        {"email": email, "password": password})
                    if res.user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.rerun()
                except Exception:
                    st.error("❌ Email ou mot de passe incorrect 🙀")
    return False

if not check_password():
    st.stop()

# ─── STYLES PENNYLANE ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.stApp {
    background-color: #f8f9fc !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    border-right: none !important;
    width: 260px !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: white !important; }

/* Boutons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.4) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.5) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e, #38ef7d) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}

/* Cards */
.pl-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f0;
    margin-bottom: 1rem;
}
.pl-card-stat {
    background: white;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f0;
    text-align: center;
}
.pl-stat-value {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0.3rem 0;
}
.pl-stat-label {
    font-size: 0.8rem;
    color: #6b7280;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.pl-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.pl-badge-green { background:#d1fae5; color:#065f46; }
.pl-badge-orange { background:#fed7aa; color:#9a3412; }
.pl-badge-red { background:#fee2e2; color:#991b1b; }
.pl-badge-blue { background:#dbeafe; color:#1e40af; }

/* Header page */
.pl-page-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem 0 1rem 0;
    border-bottom: 2px solid #f0f0f0;
    margin-bottom: 1.5rem;
}
.pl-page-icon {
    width: 48px; height: 48px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
}
.pl-page-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #1a1a2e;
    margin: 0;
}
.pl-page-subtitle {
    font-size: 0.85rem;
    color: #6b7280;
    margin: 0;
}

/* Table */
.pl-table-row {
    display: flex;
    align-items: center;
    padding: 0.8rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.3rem;
    background: white;
    border: 1px solid #f5f5f5;
    cursor: pointer;
    transition: all 0.15s ease;
}
.pl-table-row:hover {
    border-color: #667eea;
    box-shadow: 0 2px 8px rgba(102,126,234,0.15);
}

/* Chat bot flottant */
#chatbot-toggle {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    cursor: pointer;
    box-shadow: 0 8px 25px rgba(102,126,234,0.5);
    z-index: 9999;
    transition: all 0.3s ease;
    border: none;
    color: white;
}
#chatbot-toggle:hover { transform: scale(1.1); }

#chatbot-window {
    position: fixed;
    bottom: 6rem;
    right: 2rem;
    width: 340px;
    height: 450px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    z-index: 9998;
    display: none;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #e5e7eb;
}
#chatbot-window.open { display: flex !important; }

#chat-header {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 1rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    color: white;
}
#chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    background: #f8f9fc;
}
.chat-msg-bot {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px 16px 16px 4px;
    padding: 0.7rem 1rem;
    font-size: 0.85rem;
    color: #1a1a2e;
    max-width: 85%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.chat-msg-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 16px 16px 4px 16px;
    padding: 0.7rem 1rem;
    font-size: 0.85rem;
    color: white;
    max-width: 85%;
    align-self: flex-end;
}
#chat-input-area {
    padding: 0.8rem;
    border-top: 1px solid #f0f0f0;
    display: flex;
    gap: 0.5rem;
    background: white;
}
#chat-input {
    flex: 1;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    font-size: 0.85rem;
    outline: none;
    font-family: 'Inter', sans-serif;
}
#chat-input:focus { border-color: #667eea; }
#chat-send {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 0.9rem;
    cursor: pointer;
    font-size: 1rem;
}

/* Nav sidebar active */
.nav-item {
    padding: 0.6rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.3rem;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.9rem;
    transition: background 0.2s;
}
.nav-item:hover { background: rgba(255,255,255,0.1); }
.nav-item.active { background: rgba(102,126,234,0.3); color: white !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: white !important;
    border-radius: 12px !important;
    padding: 0.3rem !important;
    border: 1px solid #f0f0f0 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* Inputs */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    border-radius: 10px !important;
    border: 1.5px solid #e5e7eb !important;
    font-size: 0.9rem !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.1) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: #f0f0f0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── CHATBOT FLOTTANT ─────────────────────────────────────────────────────────
components.html("""
<button id="chatbot-toggle" onclick="toggleChat()" title="Assistant FactureCat">
    🐱
</button>

<div id="chatbot-window">
    <div id="chat-header">
        <div style="font-size:1.8rem;">🐱</div>
        <div>
            <div style="font-weight:700;font-size:0.95rem;">FactureCat Assistant</div>
            <div style="font-size:0.75rem;opacity:0.85;">🟢 En ligne · Toujours prêt à aider</div>
        </div>
        <button onclick="toggleChat()"
            style="margin-left:auto;background:none;border:none;color:white;
                   font-size:1.2rem;cursor:pointer;">✕</button>
    </div>
    <div id="chat-messages">
        <div class="chat-msg-bot">
            👋 Bonjour ! Je suis <b>FactureCat</b> 🐱<br><br>
            Je peux vous aider avec :<br>
            📄 Vos factures<br>
            💰 Notes de frais<br>
            📊 Votre comptabilité<br><br>
            Comment puis-je vous aider ?
        </div>
    </div>
    <div id="chat-input-area">
        <input id="chat-input" type="text"
               placeholder="Posez votre question..."
               onkeypress="if(event.key==='Enter') sendMsg()"/>
        <button id="chat-send" onclick="sendMsg()">➤</button>
    </div>
</div>

<script>
let chatOpen = false;

function toggleChat() {
    chatOpen = !chatOpen;
    const win = document.getElementById('chatbot-window');
    const btn = document.getElementById('chatbot-toggle');
    if (chatOpen) {
        win.classList.add('open');
        btn.innerHTML = '✕';
        document.getElementById('chat-input').focus();
    } else {
        win.classList.remove('open');
        btn.innerHTML = '🐱';
    }
}

const responses = {
    "facture": "Pour analyser vos factures, allez dans <b>📄 Factures</b>, uploadez vos PDF/images et cliquez sur <b>Lancer l'extraction</b> ! 🐾",
    "note": "Les notes de frais se trouvent dans <b>💰 Notes de frais</b>. Vous pouvez ajouter, modifier et exporter vos dépenses ! 🐾",
    "export": "Vous pouvez exporter en <b>Excel</b> ou <b>CSV</b> depuis chaque module avec le bouton de téléchargement 📥",
    "tva": "La TVA est automatiquement extraite de vos factures par l'IA Gemini 2.5 ! 🤖",
    "comptabilité": "La section <b>📊 Comptabilité</b> vous donne une vue consolidée de vos finances avec graphiques et KPIs 📈",
    "bonjour": "Bonjour ! 😸 Comment puis-je vous aider aujourd'hui ?",
    "merci": "Avec plaisir ! N'hésitez pas si vous avez d'autres questions 🐾",
    "aide": "Je peux vous aider sur : les <b>factures</b>, les <b>notes de frais</b>, l'<b>export</b>, la <b>TVA</b> et la <b>comptabilité</b> !",
    "default": "Je suis FactureCat 🐱 Posez-moi des questions sur vos <b>factures</b>, <b>notes de frais</b>, <b>export</b> ou <b>comptabilité</b> !"
};

function sendMsg() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    const messages = document.getElementById('chat-messages');

    // Message user
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg-user';
    userDiv.textContent = text;
    messages.appendChild(userDiv);
    input.value = '';

    // Réponse bot
    setTimeout(() => {
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-msg-bot';
        const lower = text.toLowerCase();
        let reply = responses.default;
        for (const [key, val] of Object.entries(responses)) {
            if (lower.includes(key)) { reply = val; break; }
        }
        botDiv.innerHTML = reply;
        messages.appendChild(botDiv);
        messages.scrollTop = messages.scrollHeight;
    }, 500);

    messages.scrollTop = messages.scrollHeight;
}
</script>
""", height=0)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def configure_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None

def extraire_facture(model, images):
    prompt = """Analyse cette facture et retourne UNIQUEMENT ce JSON brut :
{
  "date": "JJ/MM/AAAA",
  "fournisseur": "nom",
  "numero": "numéro",
  "montant_ht": 0.00,
  "tva": 0.00,
  "montant_ttc": 0.00,
  "description": "description courte",
  "categorie": "Transport/Repas/Hébergement/Fournitures/Services/Autres",
  "statut": "À payer"
}"""
    response = model.generate_content([prompt, images[0]])
    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

mois_list = ["Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
now = datetime.now()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.5rem 1rem 1rem 1rem;">
        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:2rem;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                 width:40px;height:40px;border-radius:12px;
                 display:flex;align-items:center;justify-content:center;
                 font-size:1.3rem;">🐱</div>
            <div>
                <div style="color:white;font-weight:800;font-size:1rem;">FactureCat</div>
                <div style="color:#94a3b8;font-size:0.75rem;">Comptable félin</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "",
        ["🏠 Tableau de bord", "📄 Factures",
         "💰 Notes de frais", "📊 Comptabilité"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    email = st.session_state.get("user_email", "")
    st.markdown(f"""
    <div style="padding:0 1rem;">
        <div style="color:#94a3b8;font-size:0.75rem;margin-bottom:0.5rem;">CONNECTÉ EN TANT QUE</div>
        <div style="color:white;font-size:0.85rem;font-weight:600;
             overflow:hidden;text-overflow:ellipsis;">{email}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ─── FONCTIONS UI ─────────────────────────────────────────────────────────────
def page_header(icon, title, subtitle, color="#667eea"):
    st.markdown(f"""
    <div class="pl-page-header">
        <div class="pl-page-icon" style="background:linear-gradient(135deg,{color},{color}88);">
            {icon}
        </div>
        <div>
            <p class="pl-page-title">{title}</p>
            <p class="pl-page-subtitle">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def stat_card(icon, value, label, color="#667eea"):
    st.markdown(f"""
    <div class="pl-card-stat">
        <div style="font-size:1.8rem;">{icon}</div>
        <div class="pl-stat-value" style="color:{color};">{value}</div>
        <div class="pl-stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def cat_bubble(emoji, text):
    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;gap:0.8rem;
         background:white;border-radius:16px;padding:1rem 1.2rem;
         border:1px solid #f0f0f0;box-shadow:0 2px 8px rgba(0,0,0,0.06);
         margin-bottom:1rem;">
        <div style="font-size:2rem;flex-shrink:0;">{emoji}</div>
        <div style="font-size:0.9rem;color:#374151;line-height:1.5;">{text}</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TABLEAU DE BORD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Tableau de bord":
    page_header("🏠", "Tableau de bord", "Vue d'ensemble de votre activité comptable")

    cat_bubble("😺", "<b>Bonjour !</b> Voici votre récap du jour 🐾 Tout est sous contrôle !")

    # Stats globales
    try:
        factures = get_supabase().table("factures").select("*").execute().data or []
    except Exception:
        factures = []

    notes = st.session_state.get("notes_frais", [])
    total_factures = sum(float(f.get("montant_ttc", 0)) for f in factures)
    total_notes = sum(float(n.get("Montant TTC (€)", 0)) for n in notes)
    nb_apayer = len([f for f in factures if f.get("statut") == "À payer"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("📄", len(factures), "Factures", "#667eea")
    with c2:
        stat_card("💶", f"{total_factures:,.0f} €", "Total factures", "#11998e")
    with c3:
        stat_card("💰", len(notes), "Notes de frais", "#f093fb")
    with c4:
        stat_card("⏳", nb_apayer, "À payer", "#f5576c")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("""
        <div class="pl-card">
            <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
                📈 Activité récente
            </h3>
        """, unsafe_allow_html=True)

        if factures:
            recent = sorted(factures, key=lambda x: str(x.get("date", "")), reverse=True)[:5]
            for f in recent:
                ttc = float(f.get("montant_ttc", 0))
                statut = f.get("statut", "À payer")
                badge_class = ("pl-badge-green" if statut == "Payée"
                               else "pl-badge-orange" if statut == "À payer"
                               else "pl-badge-red")
                st.markdown(f"""
                <div class="pl-table-row">
                    <div style="flex:1;">
                        <div style="font-weight:600;font-size:0.9rem;color:#1a1a2e;">
                            {f.get('fournisseur','—')}
                        </div>
                        <div style="font-size:0.78rem;color:#6b7280;">
                            {f.get('date','—')} · {f.get('categorie','—')}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:700;color:#1a1a2e;">{ttc:.2f} €</div>
                        <span class="pl-badge {badge_class}">{statut}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#9ca3af;">
                <div style="font-size:3rem;">📭</div>
                <p>Aucune facture pour l'instant</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="pl-card">
            <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
                🐱 FactureCat dit...
            </h3>
        """, unsafe_allow_html=True)

        tips = [
            ("💡", "Pensez à vérifier vos factures en attente de paiement !"),
            ("📅", "Exportez vos données mensuellement pour votre comptable."),
            ("🔍", "L'IA analyse vos factures en quelques secondes !"),
            ("📊", "Consultez la section Comptabilité pour vos KPIs."),
        ]
        for icon, tip in tips:
            st.markdown(f"""
            <div style="display:flex;gap:0.8rem;padding:0.6rem 0;
                 border-bottom:1px solid #f9f9f9;">
                <span style="font-size:1.2rem;">{icon}</span>
                <span style="font-size:0.83rem;color:#374151;">{tip}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Factures":
    page_header("📄", "Factures", "Import, analyse IA et suivi de vos factures", "#667eea")

    if "resultats" not in st.session_state:
        st.session_state["resultats"] = []

    tab1, tab2, tab3 = st.tabs(["📤 Import & Analyse", "📋 Suivi", "📊 Export"])

    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        cat_bubble("😺", "<b>Déposez vos factures</b> ci-dessous ! Je les analyse automatiquement avec Gemini 2.5 🤖🐾")

        uploaded_files = st.file_uploader(
            "Glissez vos factures (PDF ou image)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="facture_uploader"
        )

        if uploaded_files:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#667eea11,#764ba211);
                 border-radius:12px;padding:0.8rem 1.2rem;
                 border:1.5px solid #667eea44;margin:0.5rem 0 1rem 0;">
                <span style="color:#667eea;font-weight:600;">
                    🐾 {len(uploaded_files)} fichier(s) prêt(s) à l'analyse
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Aperçu
            col_prev, col_info = st.columns([1, 1])
            with col_prev:
                names = [f.name for f in uploaded_files]
                selected = st.selectbox("👁️ Aperçu", names)
                for f in uploaded_files:
                    if f.name == selected:
                        f.seek(0)
                        content = f.read()
                        f.seek(0)
                        if f.name.lower().endswith(".pdf"):
                            imgs = pdf_to_images(content)
                        else:
                            imgs = [Image.open(io.BytesIO(content))]
                        st.image(imgs[0], use_container_width=True)
                        break

            with col_info:
                st.markdown("""
                <div class="pl-card">
                    <h4 style="color:#1a1a2e;margin:0 0 0.8rem 0;">⚙️ Options d'analyse</h4>
                """, unsafe_allow_html=True)

                col_m, col_a = st.columns(2)
                with col_m:
                    mois_choisi = st.selectbox("📅 Mois", mois_list,
                                               index=now.month - 1)
                with col_a:
                    annee_choisie = st.selectbox("📅 Année",
                                                  list(range(2023, 2031)),
                                                  index=list(range(2023, 2031)).index(now.year))

                st.markdown("</div>", unsafe_allow_html=True)

                noms_actuels = sorted([f.name for f in uploaded_files])
                noms_precedents = sorted(st.session_state.get("fichiers_extraits", []))
                if noms_actuels != noms_precedents and "resultats" in st.session_state:
                    st.warning("⚠️ Nouveaux fichiers détectés. Relancez l'extraction !")

                if st.button("🚀 Lancer l'extraction IA", use_container_width=True):
                    model = configure_gemini()
                    if not model:
                        st.error("❌ Clé API Gemini manquante")
                    else:
                        progress = st.progress(0)
                        status = st.empty()
                        resultats = []

                        for i, f in enumerate(uploaded_files):
                            status.info(f"🔍 Analyse : {f.name}…")
                            f.seek(0)
                            content = f.read()
                            f.seek(0)
                            if f.name.lower().endswith(".pdf"):
                                images = pdf_to_images(content)
                            else:
                                images = [Image.open(io.BytesIO(content))]

                            try:
                                result = extraire_facture(model, images)
                                result["fichier"] = f.name
                                result["mois"] = mois_choisi
                                result["annee"] = str(annee_choisie)
                                resultats.append(result)
                            except Exception as e:
                                st.warning(f"⚠️ Erreur sur {f.name} : {e}")

                            progress.progress((i + 1) / len(uploaded_files))

                        status.success(f"✅ {len(resultats)} facture(s) analysée(s) !")
                        progress.empty()
                        st.session_state["resultats"] = resultats
                        st.session_state["fichiers_extraits"] = noms_actuels
                        st.rerun()

        # Résultats
        if st.session_state.get("resultats"):
            st.markdown("---")
            cat_bubble("😻", "<b>Purrrfect !</b> Voici les données extraites. Vous pouvez les modifier directement 🐾")

            resultats = st.session_state["resultats"]
            df = pd.DataFrame(resultats)

            col_m2, col_a2 = st.columns([2, 6])
            with col_m2:
                mois_r = st.selectbox("Mois de la période", mois_list,
                                       index=mois_list.index(st.session_state.get("mois", mois_list[now.month-1])),
                                       key="mois_result")
            df["mois"] = mois_r

            col_rename = {
                "fichier": "Fichier", "date": "Date", "mois": "Mois",
                "annee": "Année", "fournisseur": "Fournisseur",
                "numero": "N° Facture", "montant_ht": "HT (€)",
                "tva": "TVA (€)", "montant_ttc": "TTC (€)",
                "description": "Description", "categorie": "Catégorie",
                "statut": "Statut"
            }
            df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
            cols_order = [v for v in col_rename.values() if v in df.columns]
            df = df[cols_order]

            df_edit = st.data_editor(
                df, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["À payer", "Payée", "En retard", "Annulée"]
                    ),
                    "Catégorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=["Transport","Repas","Hébergement",
                                 "Fournitures","Services","Autres"]
                    )
                }
            )

            # KPIs
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                stat_card("📄", len(df_edit), "Factures analysées", "#667eea")
            with k2:
                try:
                    ht = df_edit["HT (€)"].astype(float).sum()
                    stat_card("💵", f"{ht:,.2f} €", "Total HT", "#11998e")
                except Exception:
                    stat_card("💵", "—", "Total HT", "#11998e")
            with k3:
                try:
                    tva = df_edit["TVA (€)"].astype(float).sum()
                    stat_card("📊", f"{tva:,.2f} €", "Total TVA", "#f093fb")
                except Exception:
                    stat_card("📊", "—", "Total TVA", "#f093fb")
            with k4:
                try:
                    ttc = df_edit["TTC (€)"].astype(float).sum()
                    stat_card("💰", f"{ttc:,.2f} €", "Total TTC", "#f5576c")
                except Exception:
                    stat_card("💰", "—", "Total TTC", "#f5576c")

            # Export
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            col_dl = st.columns([1, 2, 1])
            with col_dl[1]:
                buffer = io.BytesIO()
                df_edit.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button(
                    "📥 Télécharger Excel 🐾",
                    data=buffer,
                    file_name=f"factures_{mois_r}_{now.year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            if not uploaded_files:
                st.markdown("""
                <div style="text-align:center;padding:3rem;background:white;border-radius:16px;
                     border:2px dashed #e5e7eb;margin-top:1rem;">
                    <div style="font-size:4rem;">🐱</div>
                    <p style="font-size:1.1rem;font-weight:700;color:#1a1a2e;margin-top:1rem;">
                        Uploadez vos factures pour commencer !
                    </p>
                    <p style="color:#6b7280;font-size:0.9rem;">
                        Formats acceptés : PDF, JPG, PNG
                    </p>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        try:
            factures_db = get_supabase().table("factures").select("*").execute().data or []
        except Exception:
            factures_db = st.session_state.get("resultats", [])

        if factures_db:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                search = st.text_input("🔍 Rechercher fournisseur")
            with col_f2:
                cats = ["Toutes"] + sorted(set(f.get("categorie","") for f in factures_db))
                cat_f = st.selectbox("📂 Catégorie", cats)
            with col_f3:
                stats = ["Tous","À payer","Payée","En retard","Annulée"]
                stat_f = st.selectbox("🏷️ Statut", stats)

            filtered = [f for f in factures_db
                        if (not search or search.lower() in str(f.get("fournisseur","")).lower())
                        and (cat_f == "Toutes" or f.get("categorie") == cat_f)
                        and (stat_f == "Tous" or f.get("statut") == stat_f)]

            st.markdown(f"<p style='color:#6b7280;font-size:0.85rem;margin:0.5rem 0 1rem 0;'>"
                        f"<b>{len(filtered)}</b> résultat(s)</p>", unsafe_allow_html=True)

            for f in filtered:
                ttc = float(f.get("montant_ttc", 0))
                statut = f.get("statut", "À payer")
                badge = ("pl-badge-green" if statut == "Payée"
                         else "pl-badge-orange" if statut == "À payer"
                         else "pl-badge-red")
                st.markdown(f"""
                <div class="pl-table-row">
                    <div style="width:40px;text-align:center;font-size:1.3rem;">📄</div>
                    <div style="flex:1;margin-left:0.5rem;">
                        <div style="font-weight:600;color:#1a1a2e;">
                            {f.get('fournisseur','—')}
                        </div>
                        <div style="font-size:0.78rem;color:#6b7280;">
                            {f.get('date','—')} · N°{f.get('numero','—')} · {f.get('categorie','—')}
                        </div>
                    </div>
                    <div style="text-align:right;min-width:120px;">
                        <div style="font-weight:700;color:#1a1a2e;font-size:1rem;">{ttc:.2f} €</div>
                        <span class="pl-badge {badge}">{statut}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            cat_bubble("😿", "Aucune facture trouvée. Importez vos premières factures dans l'onglet <b>Import & Analyse</b> !")

    # ── TAB 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        try:
            factures_exp = get_supabase().table("factures").select("*").execute().data or []
        except Exception:
            factures_exp = st.session_state.get("resultats", [])

        if factures_exp:
            df_exp = pd.DataFrame(factures_exp)
            st.dataframe(df_exp, use_container_width=True, hide_index=True)
            e1, e2 = st.columns(2)
            with e1:
                csv = df_exp.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 CSV", data=csv,
                                   file_name="factures.csv", mime="text/csv",
                                   use_container_width=True)
            with e2:
                buf = io.BytesIO()
                df_exp.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button("📥 Excel", data=buf,
                                   file_name="factures.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
        else:
            st.info("📭 Aucune facture à exporter")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":
    page_header("💰", "Notes de Frais", "Gérez et exportez vos dépenses professionnelles", "#f093fb")

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    tab_n1, tab_n2 = st.tabs(["➕ Nouvelle dépense", "📋 Mes dépenses"])

    with tab_n1:
        cat_bubble("🐱", "Remplissez le formulaire pour ajouter une nouvelle dépense 🐾")

        with st.form("form_note_frais", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nf_date = st.date_input("📅 Date", value=now)
                nf_employe = st.text_input("👤 Employé")
                nf_categorie = st.selectbox("📂 Catégorie",
                    ["Transport","Repas","Hébergement","Fournitures","Services","Autres"])
                nf_moyen = st.selectbox("💳 Moyen de paiement",
                    ["Carte bancaire","Espèces","Virement","Chèque"])
            with col2:
                nf_description = st.text_area("📝 Description", height=100)
                nf_montant_ht = st.number_input("💵 Montant HT (€)", min_value=0.0, step=0.01)
                tva_options = {"0%": 0.0, "5.5%": 5.5, "10%": 10.0, "20%": 20.0}
                nf_tva = st.selectbox("📊 TVA", list(tva_options.keys()))
                tva_val = tva_options[nf_tva]
                nf_tva_amt = round(nf_montant_ht * tva_val / 100, 2)
                nf_ttc = round(nf_montant_ht + nf_tva_amt, 2)
                st.markdown(f"""
                <div style="background:#f8f9fc;border-radius:10px;padding:0.8rem;margin-top:0.5rem;">
                    <span style="color:#6b7280;font-size:0.85rem;">TVA : </span>
                    <b style="color:#667eea;">{nf_tva_amt:.2f} €</b>
                    <span style="margin:0 0.5rem;">·</span>
                    <span style="color:#6b7280;font-size:0.85rem;">TTC : </span>
                    <b style="color:#11998e;font-size:1.1rem;">{nf_ttc:.2f} €</b>
                </div>
                """, unsafe_allow_html=True)
                nf_justif = st.file_uploader("📎 Justificatif", type=["pdf","png","jpg","jpeg"])

            submitted = st.form_submit_button("➕ Ajouter la dépense", use_container_width=True)
            if submitted:
                if not nf_employe:
                    st.error("❌ Veuillez saisir un nom d'employé !")
                elif nf_montant_ht <= 0:
                    st.error("❌ Le montant doit être supérieur à 0 !")
                else:
                    st.session_state["notes_frais"].append({
                        "Date": nf_date.strftime("%d/%m/%Y"),
                        "Employé": nf_employe,
                        "Catégorie": nf_categorie,
                        "Description": nf_description,
                        "Montant HT (€)": nf_montant_ht,
                        "TVA": nf_tva,
                        "Montant TVA (€)": nf_tva_amt,
                        "Montant TTC (€)": nf_ttc,
                        "Moyen de paiement": nf_moyen,
                        "Justificatif": nf_justif.name if nf_justif else "—",
                        "Statut": "En attente 😺"
                    })
                    st.success("✅ Dépense ajoutée ! 🐾")
                    st.rerun()

    with tab_n2:
        notes = st.session_state.get("notes_frais", [])
        if notes:
            df_nf = pd.DataFrame(notes)

            # KPIs
            n1, n2, n3, n4 = st.columns(4)
            with n1:
                stat_card("💰", len(df_nf), "Dépenses", "#f093fb")
            with n2:
                stat_card("💵", f"{df_nf['Montant TTC (€)'].sum():,.2f} €", "Total TTC", "#11998e")
            with n3:
                stat_card("😸", len(df_nf[df_nf["Statut"]=="Validé 😸"]), "Validées", "#667eea")
            with n4:
                stat_card("😺", len(df_nf[df_nf["Statut"]=="En attente 😺"]), "En attente", "#f5576c")

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            # Filtres
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                filtre_emp = st.text_input("🔍 Employé")
            with cf2:
                filtre_cat = st.selectbox("📂 Catégorie",
                    ["Toutes"] + list(df_nf["Catégorie"].unique()))
            with cf3:
                filtre_stat = st.selectbox("🏷️ Statut",
                    ["Tous","En attente 😺","Validé 😸","Refusé 🙀"])

            df_f = df_nf.copy()
            if filtre_emp:
                df_f = df_f[df_f["Employé"].str.contains(filtre_emp, case=False)]
            if filtre_cat != "Toutes":
                df_f = df_f[df_f["Catégorie"] == filtre_cat]
            if filtre_stat != "Tous":
                df_f = df_f[df_f["Statut"] == filtre_stat]

            df_nf_edit = st.data_editor(
                df_f, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["En attente 😺","Validé 😸","Refusé 🙀"]
                    )
                }
            )

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            act1, act2, act3 = st.columns(3)
            with act1:
                buf_nf = io.BytesIO()
                df_nf.to_excel(buf_nf, index=False, engine="openpyxl")
                buf_nf.seek(0)
                st.download_button("📥 Excel", data=buf_nf,
                                   file_name=f"notes_frais_{now.strftime('%Y%m')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with act2:
                csv_nf = df_nf.to_csv(index=False).encode("utf-8")
                st.download_button("📄 CSV", data=csv_nf,
                                   file_name=f"notes_frais_{now.strftime('%Y%m')}.csv",
                                   mime="text/csv", use_container_width=True)
            with act3:
                if st.button("🗑️ Tout effacer", use_container_width=True):
                    st.session_state["notes_frais"] = []
                    st.rerun()
        else:
            cat_bubble("😿", "Aucune note de frais. Ajoutez votre première dépense dans l'onglet <b>Nouvelle dépense</b> !")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPTABILITÉ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Comptabilité":
    page_header("📊", "Comptabilité", "Vue financière consolidée de votre activité", "#11998e")

    try:
        factures_all = get_supabase().table("factures").select("*").execute().data or []
    except Exception:
        factures_all = st.session_state.get("resultats", [])

    notes_all = st.session_state.get("notes_frais", [])

    # ── KPIs principaux ───────────────────────────────────────────────────────
    total_ht = sum(float(f.get("montant_ht", 0)) for f in factures_all)
    total_tva = sum(float(f.get("tva", 0)) for f in factures_all)
    total_ttc = sum(float(f.get("montant_ttc", 0)) for f in factures_all)
    total_notes = sum(float(n.get("Montant TTC (€)", 0)) for n in notes_all)
    nb_apayer = len([f for f in factures_all if f.get("statut") == "À payer"])
    nb_payees = len([f for f in factures_all if f.get("statut") == "Payée"])

    cat_bubble("😺", f"Vous avez <b>{len(factures_all)} factures</b> pour un total TTC de <b>{total_ttc:,.2f} €</b>. "
               f"<b>{nb_apayer}</b> en attente de paiement 🐾")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: stat_card("💵", f"{total_ht:,.0f} €", "Total HT", "#667eea")
    with k2: stat_card("📊", f"{total_tva:,.0f} €", "Total TVA", "#f093fb")
    with k3: stat_card("💰", f"{total_ttc:,.0f} €", "Total TTC", "#11998e")
    with k4: stat_card("💸", f"{total_notes:,.0f} €", "Notes de frais", "#f5576c")
    with k5: stat_card("✅", nb_payees, "Factures payées", "#11998e")
    with k6: stat_card("⏳", nb_apayer, "À payer", "#f5576c")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    # ── Par catégorie ─────────────────────────────────────────────────────────
    with col_g1:
        st.markdown("""
        <div class="pl-card">
            <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
                📂 Répartition par catégorie
            </h3>
        """, unsafe_allow_html=True)

        if factures_all:
            df_cat = pd.DataFrame(factures_all)
            df_cat["montant_ttc"] = pd.to_numeric(df_cat.get("montant_ttc", 0), errors="coerce").fillna(0)
            by_cat = df_cat.groupby("categorie")["montant_ttc"].sum().sort_values(ascending=False)

            for cat, val in by_cat.items():
                pct = (val / total_ttc * 100) if total_ttc > 0 else 0
                st.markdown(f"""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
                        <span style="font-size:0.85rem;font-weight:600;color:#374151;">{cat}</span>
                        <span style="font-size:0.85rem;font-weight:700;color:#1a1a2e;">{val:,.2f} €</span>
                    </div>
                    <div style="background:#f3f4f6;border-radius:20px;height:8px;">
                        <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                             width:{pct:.1f}%;height:8px;border-radius:20px;"></div>
                    </div>
                    <div style="font-size:0.75rem;color:#9ca3af;margin-top:0.1rem;">{pct:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#9ca3af;text-align:center;padding:2rem 0;'>Aucune donnée</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Par statut ────────────────────────────────────────────────────────────
    with col_g2:
        st.markdown("""
        <div class="pl-card">
            <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
                🏷️ Suivi des paiements
            </h3>
        """, unsafe_allow_html=True)

        if factures_all:
            df_stat = pd.DataFrame(factures_all)
            df_stat["montant_ttc"] = pd.to_numeric(df_stat.get("montant_ttc", 0), errors="coerce").fillna(0)
            by_stat = df_stat.groupby("statut").agg(
                               count=("montant_ttc", "count"),
                total=("montant_ttc", "sum")
            ).reset_index()

            colors = {
                "Payée": "#11998e",
                "À payer": "#f5576c",
                "En retard": "#f093fb",
                "Annulée": "#9ca3af"
            }
            icons = {
                "Payée": "✅",
                "À payer": "⏳",
                "En retard": "🔴",
                "Annulée": "❌"
            }

            for _, row in by_stat.iterrows():
                color = colors.get(row["statut"], "#667eea")
                icon = icons.get(row["statut"], "📄")
                st.markdown(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                     padding:0.7rem 1rem;border-radius:10px;margin-bottom:0.4rem;
                     background:#f8f9fc;border-left:4px solid {color};">
                    <div style="display:flex;align-items:center;gap:0.6rem;">
                        <span style="font-size:1.2rem;">{icon}</span>
                        <span style="font-weight:600;color:#374151;">{row['statut']}</span>
                        <span style="background:#e5e7eb;color:#6b7280;border-radius:20px;
                             padding:0.1rem 0.5rem;font-size:0.75rem;font-weight:600;">
                            {int(row['count'])}
                        </span>
                    </div>
                    <span style="font-weight:700;color:{color};font-size:1rem;">
                        {row['total']:,.2f} €
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#9ca3af;text-align:center;padding:2rem 0;'>Aucune donnée</p>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Évolution mensuelle ───────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="pl-card">
        <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
            📈 Évolution mensuelle
        </h3>
    """, unsafe_allow_html=True)

    if factures_all:
        df_evo = pd.DataFrame(factures_all)
        df_evo["montant_ttc"] = pd.to_numeric(df_evo.get("montant_ttc", 0), errors="coerce").fillna(0)

        if "mois" in df_evo.columns:
            by_mois = df_evo.groupby("mois")["montant_ttc"].sum().reset_index()
            by_mois.columns = ["Mois", "Total TTC"]
            by_mois = by_mois.sort_values("Mois")

            max_val = by_mois["Total TTC"].max() if not by_mois.empty else 1
            for _, row in by_mois.iterrows():
                pct = (row["Total TTC"] / max_val * 100) if max_val > 0 else 0
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.6rem;">
                    <div style="width:80px;font-size:0.8rem;font-weight:600;
                         color:#6b7280;text-align:right;">{row['Mois']}</div>
                    <div style="flex:1;background:#f3f4f6;border-radius:20px;height:10px;">
                        <div style="background:linear-gradient(135deg,#667eea,#11998e);
                             width:{pct:.1f}%;height:10px;border-radius:20px;"></div>
                    </div>
                    <div style="width:90px;font-size:0.85rem;font-weight:700;
                         color:#1a1a2e;">{row['Total TTC']:,.2f} €</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#9ca3af;'>Données mensuelles non disponibles</p>",
                        unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#9ca3af;text-align:center;padding:2rem 0;'>Aucune donnée</p>",
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Tableau récap notes de frais ─────────────────────────────────────────
    if notes_all:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="pl-card">
            <h3 style="color:#1a1a2e;font-size:1rem;font-weight:700;margin:0 0 1rem 0;">
                💰 Notes de frais — Récapitulatif
            </h3>
        """, unsafe_allow_html=True)

        df_notes_recap = pd.DataFrame(notes_all)
        df_notes_recap["Montant TTC (€)"] = pd.to_numeric(
            df_notes_recap["Montant TTC (€)"], errors="coerce").fillna(0)

        by_emp = df_notes_recap.groupby("Employé")["Montant TTC (€)"].sum().sort_values(ascending=False)
        max_emp = by_emp.max() if not by_emp.empty else 1

        for emp, val in by_emp.items():
            pct = (val / max_emp * 100) if max_emp > 0 else 0
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.6rem;">
                <div style="width:120px;font-size:0.85rem;font-weight:600;
                     color:#374151;overflow:hidden;text-overflow:ellipsis;
                     white-space:nowrap;">{emp}</div>
                <div style="flex:1;background:#f3f4f6;border-radius:20px;height:10px;">
                    <div style="background:linear-gradient(135deg,#f093fb,#f5576c);
                         width:{pct:.1f}%;height:10px;border-radius:20px;"></div>
                </div>
                <div style="width:90px;font-size:0.85rem;font-weight:700;
                     color:#1a1a2e;text-align:right;">{val:,.2f} €</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Export comptabilité ───────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    ex1, ex2 = st.columns(2)

    with ex1:
        if factures_all:
            df_export = pd.DataFrame(factures_all)
            buf_compta = io.BytesIO()
            with pd.ExcelWriter(buf_compta, engine="openpyxl") as writer:
                df_export.to_excel(writer, sheet_name="Factures", index=False)
                if notes_all:
                    pd.DataFrame(notes_all).to_excel(writer, sheet_name="Notes de frais", index=False)
            buf_compta.seek(0)
            st.download_button(
                "📥 Export comptabilité complet (Excel)",
                data=buf_compta,
                file_name=f"comptabilite_{now.strftime('%Y%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with ex2:
        if factures_all or notes_all:
            all_data = {
                "factures": factures_all,
                "notes_frais": notes_all
            }
            st.download_button(
                "📄 Export JSON",
                data=json.dumps(all_data, ensure_ascii=False, indent=2),
                file_name=f"comptabilite_{now.strftime('%Y%m')}.json",
                mime="application/json",
                use_container_width=True
            )

    # ── Pied de page ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;padding:1.5rem;background:white;border-radius:16px;
         border:1px solid #f0f0f0;box-shadow:0 2px 12px rgba(0,0,0,0.04);">
        <div style="font-size:2.5rem;">🐱</div>
        <p style="color:#1a1a2e;font-weight:700;margin:0.5rem 0 0.2rem 0;">
            FactureCat — Comptable félin 🐾
        </p>
        <p style="color:#9ca3af;font-size:0.8rem;margin:0;">
            Propulsé par Gemini AI · Données sécurisées par Supabase
        </p>
    </div>
    """, unsafe_allow_html=True)

