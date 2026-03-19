import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime
import base64

st.set_page_config(page_title="FactureCat 🐱", page_icon="🐱", layout="wide")

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
    <div style="max-width:420px;margin:5rem auto;text-align:center;">
        <div style="font-size:5rem;">🐱</div>
        <h1 style="color:#a0522d;font-weight:900;font-size:2.5rem;margin:0;">FactureCat</h1>
        <p style="color:#c8956c;font-size:1rem;margin-top:0.3rem;">Extraction intelligente de factures 🐾</p>
        <hr style="border-color:rgba(200,149,108,0.3);margin:1.5rem 0;">
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1,2,1])
    with col[1]:
        mode = st.radio("Mode", ["🔑 Se connecter","✨ Créer un compte"],
                        horizontal=True, label_visibility="collapsed")
        email    = st.text_input("📧 Email")
        password = st.text_input("🔑 Mot de passe", type="password")
        if mode == "🔑 Se connecter":
            if st.button("🐾 Se connecter", use_container_width=True):
                try:
                    sb = get_supabase()
                    sb.auth.sign_in_with_password({"email":email,"password":password})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = email
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            if st.button("✨ Créer mon compte", use_container_width=True):
                try:
                    sb = get_supabase()
                    sb.auth.sign_up({"email":email,"password":password})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = email
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
    return False

if not check_password():
    st.stop()

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
*{font-family:'Nunito',sans-serif;}
[data-testid="stSidebar"]{display:none;}
[data-testid="collapsedControl"]{display:none;}
.stApp{background:linear-gradient(135deg,#fdf6f0 0%,#faebd7 50%,#fdf6f0 100%);}
.main .block-container{
    padding-top:5rem !important;
    padding-left:2rem !important;
    padding-right:2rem !important;
    max-width:1400px !important;
    margin:0 auto !important;
}

/* TOPBAR */
.topbar{
    position:fixed;top:0;left:0;right:0;z-index:9999;
    background:linear-gradient(135deg,#a0522d,#c8956c);
    padding:0.6rem 2rem;
    display:flex;align-items:center;justify-content:space-between;
    box-shadow:0 4px 20px rgba(160,82,45,0.3);
}
.topbar-logo{display:flex;align-items:center;gap:0.8rem;}
.topbar-logo span{color:white;font-weight:800;font-size:1.2rem;}
.topbar-nav{display:flex;gap:0.5rem;}
.topbar-btn{
    background:rgba(255,255,255,0.15);
    border:2px solid rgba(255,255,255,0.4);
    color:white !important;border-radius:20px;
    padding:0.3rem 1.2rem;font-size:0.85rem;font-weight:700;
    cursor:pointer;transition:all 0.2s;text-decoration:none;
    font-family:'Nunito',sans-serif;
}
.topbar-btn:hover,.topbar-btn.active{
    background:rgba(255,255,255,0.3);
    border-color:white;
}
.topbar-user{color:rgba(255,255,255,0.85);font-size:0.8rem;}

/* Streamlit buttons */
.stButton>button{
    background:white !important;color:#a0522d !important;
    border:2px solid #f0a070 !important;border-radius:25px !important;
    padding:0.55rem 1.5rem !important;font-size:0.92rem !important;
    font-weight:700 !important;transition:all 0.25s ease !important;
    font-family:'Nunito',sans-serif !important;
}
.stButton>button:hover{
    background:#fdf6f0 !important;border-color:#e8856a !important;
    transform:translateY(-2px) !important;
    box-shadow:0 4px 15px rgba(200,149,108,0.4) !important;
}

/* Bouton analyse spécial */
.btn-analyse-wrap .stButton>button{
    background:linear-gradient(135deg,#f0a070,#c8956c) !important;
    color:white !important;border:none !important;
    border-radius:30px !important;padding:0.8rem 2rem !important;
    font-size:1.05rem !important;font-weight:800 !important;
    box-shadow:0 4px 18px rgba(200,149,108,0.4) !important;
}
.btn-analyse-wrap .stButton>button:hover{
    background:linear-gradient(135deg,#e8906a,#b07850) !important;
    transform:translateY(-2px) !important;
    box-shadow:0 6px 22px rgba(200,149,108,0.5) !important;
}

/* Cat bubble */
.cat-container{display:flex;align-items:flex-start;gap:1rem;margin:1rem 0;}
.cat-avatar{font-size:2.8rem;line-height:1;flex-shrink:0;}
.cat-bubble{
    background:white;border-radius:18px 18px 18px 4px;
    padding:0.9rem 1.3rem;
    border:2px solid rgba(200,149,108,0.25);
    box-shadow:0 4px 15px rgba(200,149,108,0.12);flex:1;
}
.cat-bubble-title{color:#a0522d;font-weight:800;font-size:1rem;margin-bottom:0.15rem;}
.cat-bubble-sub{color:#c8956c;font-size:0.87rem;font-weight:600;}

/* Section title */
.section-title{
    font-size:1rem;font-weight:800;color:#a0522d;
    margin-bottom:0.8rem;padding-bottom:0.35rem;
    border-bottom:2px solid rgba(240,160,112,0.5);
}

/* Metric / dash cards */
.dash-card{
    background:white;border-radius:20px;padding:1.5rem 1rem;
    text-align:center;border:2px solid rgba(200,149,108,0.15);
    box-shadow:0 4px 20px rgba(200,149,108,0.1);margin-bottom:0.5rem;
}
.dash-card .icon{font-size:2.2rem;margin-bottom:0.3rem;}
.dash-card .value{font-size:2rem;font-weight:900;color:#a0522d;}
.dash-card .value.green{color:#27ae60;}
.dash-card .value.red{color:#e74c3c;}
.dash-card .label{color:#c8956c;font-size:0.82rem;font-weight:600;}

.metric-card{
    background:white;border-radius:16px;padding:1rem;
    text-align:center;border:2px solid rgba(200,149,108,0.15);
    box-shadow:0 3px 12px rgba(200,149,108,0.1);margin-bottom:0.5rem;
}
.metric-value{font-size:1.5rem;font-weight:900;color:#a0522d;}
.metric-value.green{color:#27ae60;}
.metric-value.red{color:#e74c3c;}
.metric-label{font-size:0.78rem;color:#c8956c;font-weight:600;margin-top:0.1rem;}

/* Pending box */
.pending-box{
    background:white;border:2px solid rgba(240,160,112,0.5);
    border-radius:16px;padding:0.9rem 1.3rem;
    color:#a0522d;font-weight:700;font-size:0.92rem;margin-bottom:1rem;
}

/* Info row */
.info-row{
    display:flex;justify-content:space-between;align-items:center;
    padding:0.45rem 0.8rem;margin-bottom:0.35rem;
    background:white;border-radius:10px;
    border:1px solid rgba(200,149,108,0.2);
}
.info-label{color:#c8956c;font-size:0.8rem;font-weight:700;}
.info-value{color:#a0522d;font-size:0.83rem;font-weight:800;max-width:55%;text-align:right;}

/* Upload */
[data-testid="stFileUploader"]{
    background:white;border:2px dashed #f0a070;border-radius:16px;padding:1rem;
}
hr{border-color:rgba(200,149,108,0.3) !important;}
::-webkit-scrollbar{width:8px;}
::-webkit-scrollbar-track{background:#fdf6f0;}
::-webkit-scrollbar-thumb{background:linear-gradient(#f0a070,#c8956c);border-radius:4px;}
</style>
""", unsafe_allow_html=True)

# ── Init page ──
if "page" not in st.session_state:
    st.session_state["page"] = "factures"

user_email = st.session_state.get("user_email","")

# ── TOPBAR HTML ──
st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">
        <span style="font-size:1.8rem;">🐱</span>
        <span>FactureCat</span>
        <span style="color:rgba(255,255,255,0.6);font-size:0.75rem;font-weight:400;">
            Votre assistant comptable félin
        </span>
    </div>
    <div class="topbar-user">🐾 {user_email}</div>
</div>
""", unsafe_allow_html=True)

# ── NAV CENTRÉE ──
sp1,nc1,nc2,nc3,sp2 = st.columns([2,1,1,1,2])
with nc1:
    if st.button("📄 Factures", use_container_width=True, key="nav_fac"):
        st.session_state["page"] = "factures"; st.rerun()
with nc2:
    if st.button("💰 Notes de frais", use_container_width=True, key="nav_notes"):
        st.session_state["page"] = "notes"; st.rerun()
with nc3:
    if st.button("🚪 Déco", use_container_width=True, key="nav_deco"):
        st.session_state["authenticated"] = False; st.rerun()

st.markdown("---")
page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════
# GEMINI
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def get_gemini():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel("gemini-2.5-flash")

model = get_gemini()

def extract_pdf_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for p in doc:
        pix = p.get_pixmap(matrix=fitz.Matrix(2,2))
        img = Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
        images.append(img)
    return images

def image_to_bytes(img, fmt="PNG"):
    buf = io.BytesIO(); img.save(buf, format=fmt); return buf.getvalue()

def img_to_base64(img):
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def raw_bytes_to_base64(b):
    return base64.b64encode(b).decode()

def pdf_bytes_to_base64_pages(pdf_bytes):
    return [base64.b64encode(image_to_bytes(img)).decode()
            for img in extract_pdf_images(pdf_bytes)]

def analyze_invoice(file_bytes, file_type):
    prompt = """Tu es FactureCat 🐱. Analyse cette facture. JSON strict :
{
  "fournisseur":"nom émetteur (pas le client)",
  "date":"JJ/MM/AAAA",
  "numero_facture":"...",
  "montant_ht":0.00,
  "tva":0.00,
  "montant_ttc":0.00,
  "devise":"EUR",
  "description":"...",
  "categorie":"Transport/Repas/Hébergement/Fournitures/Formation/Client/Autres",
  "statut":"Validé 😸 ou À vérifier 🐱 ou Erreur 🙀"
}
Réponds UNIQUEMENT avec le JSON."""
    try:
        if file_type == "application/pdf":
            images = extract_pdf_images(file_bytes)
            if not images: return None
            img_bytes = image_to_bytes(images[0])
            resp = model.generate_content([prompt,{"mime_type":"image/png","data":img_bytes}])
        else:
            resp = model.generate_content([prompt,{"mime_type":file_type,"data":file_bytes}])
        text = resp.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:   text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"❌ Erreur analyse : {e}"); return None

# ══════════════════════════════════════════════════════════════
# CHAT WIDGET FLOTTANT
# ══════════════════════════════════════════════════════════════
def render_chat_widget(factures_data):
    factures_json = json.dumps(factures_data, ensure_ascii=False)
    gemini_key    = st.secrets["GEMINI_API_KEY"]

    html = f"""
<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Nunito',sans-serif;}}
body{{background:transparent;overflow:hidden;}}

/* FAB */
#chat-fab{{
    position:fixed;bottom:2rem;right:2rem;
    width:66px;height:66px;border-radius:50%;
    background:linear-gradient(135deg,#f0a070,#a0522d);
    box-shadow:0 6px 24px rgba(160,82,45,0.5);
    display:flex;align-items:center;justify-content:center;
    cursor:pointer;z-index:100000;
    transition:transform 0.25s ease,box-shadow 0.25s ease;
    border:3px solid white;font-size:2rem;user-select:none;
}}
#chat-fab:hover{{transform:scale(1.12) rotate(-6deg);box-shadow:0 8px 30px rgba(160,82,45,0.6);}}
#notif-dot{{
    position:absolute;top:3px;right:3px;width:14px;height:14px;
    background:#e74c3c;border-radius:50%;border:2px solid white;
    animation:pulse 1.5s infinite;
}}
@keyframes pulse{{0%,100%{{transform:scale(1);opacity:1;}}50%{{transform:scale(1.2);opacity:0.8;}}}}

/* WIDGET */
#chat-widget{{
    display:none;position:fixed;
    bottom:6.8rem;right:2rem;
    width:370px;
    background:#fdf6f0;border-radius:24px;
    box-shadow:0 14px 50px rgba(160,82,45,0.35);
    z-index:99999;flex-direction:column;overflow:hidden;
    border:2px solid rgba(240,160,112,0.35);
    animation:slideUp 0.25s ease;
}}
#chat-widget.open{{display:flex;}}
@keyframes slideUp{{
    from{{opacity:0;transform:translateY(24px) scale(0.94);}}
    to{{opacity:1;transform:translateY(0) scale(1);}}
}}

/* Header */
#chat-header{{
    background:linear-gradient(135deg,#a0522d,#c8956c);
    padding:0.9rem 1.2rem;
    display:flex;align-items:center;gap:0.8rem;
}}
#chat-header .cat-face{{font-size:2.2rem;line-height:1;}}
#chat-header .htxt h4{{color:white;margin:0;font-size:0.95rem;font-weight:800;}}
#chat-header .htxt p{{color:rgba(255,255,255,0.8);margin:0;font-size:0.72rem;}}
#chat-header .hclose{{
    margin-left:auto;background:rgba(255,255,255,0.22);
    border:none;border-radius:50%;width:30px;height:30px;
    color:white;font-size:1rem;cursor:pointer;font-weight:900;
    display:flex;align-items:center;justify-content:center;
    transition:background 0.2s;
}}
#chat-header .hclose:hover{{background:rgba(255,255,255,0.38);}}

/* Messages */
#chat-messages{{
    flex:1;overflow-y:auto;padding:1rem;
    display:flex;flex-direction:column;gap:0.55rem;
    max-height:300px;min-height:120px;
}}
#chat-messages::-webkit-scrollbar{{width:5px;}}
#chat-messages::-webkit-scrollbar-thumb{{background:#f0a070;border-radius:3px;}}

.wmsg-user{{
    background:linear-gradient(135deg,#f0a070,#c8956c);
    color:white;border-radius:16px 16px 4px 16px;
    padding:0.6rem 0.9rem;font-size:0.84rem;font-weight:600;
    align-self:flex-end;max-width:85%;word-break:break-word;
    box-shadow:0 2px 8px rgba(200,149,108,0.3);
}}
.wmsg-bot{{
    background:white;border:2px solid rgba(200,149,108,0.25);
    border-radius:16px 16px 16px 4px;
    padding:0.6rem 0.9rem;font-size:0.84rem;color:#5a3010;
    align-self:flex-start;max-width:85%;word-break:break-word;
    box-shadow:0 2px 8px rgba(200,149,108,0.1);
}}
.wmsg-bot .sender{{font-size:0.73rem;color:#c8956c;font-weight:800;margin-bottom:0.2rem;}}

#thinking{{
    padding:0.5rem 1rem;color:#c8956c;font-size:0.82rem;
    font-style:italic;background:white;
    border-top:1px solid rgba(240,160,112,0.2);display:none;
}}

/* Footer */
#chat-footer{{
    padding:0.75rem 0.9rem;
    background:white;border-top:2px solid rgba(240,160,112,0.2);
}}
#chat-input-row{{display:flex;gap:0.45rem;align-items:center;}}
#chat-text{{
    flex:1;border:2px solid rgba(240,160,112,0.4);
    border-radius:20px;padding:0.5rem 1rem;
    font-size:0.84rem;font-family:'Nunito',sans-serif;
    color:#5a3010;outline:none;background:#fdf6f0;
    transition:border-color 0.2s;
}}
#chat-text:focus{{border-color:#f0a070;}}
#chat-text::placeholder{{color:#c8956c;opacity:0.8;}}

/* Boutons chat — même style que Streamlit */
.cbtn{{
    background:white;color:#a0522d;
    border:2px solid #f0a070;border-radius:20px;
    padding:0.48rem 1rem;font-size:0.84rem;font-weight:700;
    font-family:'Nunito',sans-serif;cursor:pointer;
    transition:all 0.2s ease;white-space:nowrap;
    display:flex;align-items:center;gap:0.3rem;
}}
.cbtn:hover{{
    background:#fdf6f0;border-color:#e8856a;
    transform:translateY(-1px);
    box-shadow:0 3px 10px rgba(200,149,108,0.35);
}}
.cbtn.icon-only{{
    padding:0.48rem 0.65rem;
    border-color:rgba(240,160,112,0.5);color:#c8956c;font-size:1rem;
}}
.cbtn.icon-only:hover{{border-color:#e8856a;color:#a0522d;}}
</style>
</head><body>

<!-- FAB -->
<div id="chat-fab" onclick="toggleChat()">
    🐱
    <div id="notif-dot"></div>
</div>

<!-- WIDGET -->
<div id="chat-widget">
    <div id="chat-header">
        <div class="cat-face">🐱</div>
        <div class="htxt">
            <h4>FactureCat Assistant 🐾</h4>
            <p>Posez-moi vos questions comptables !</p>
        </div>
        <button class="hclose" onclick="toggleChat()">✕</button>
    </div>

    <div id="chat-messages">
        <div class="wmsg-bot">
            <div class="sender">🐱 FactureCat</div>
            Bonjour ! Je suis FactureCat 🐾<br>
            <span style="color:#c8956c;font-size:0.79rem;">
                Posez-moi des questions sur vos factures !
            </span>
        </div>
    </div>

    <div id="thinking">🐱 FactureCat réfléchit<span id="dots">...</span></div>

    <div id="chat-footer">
        <div id="chat-input-row">
            <input id="chat-text" type="text"
                   placeholder="Ex: Total des factures ?"
                   onkeydown="if(event.key==='Enter')sendMsg()"/>
            <button class="cbtn" onclick="sendMsg()">🐾 Envoyer</button>
            <button class="cbtn icon-only" onclick="clearChat()" title="Effacer le chat">🧹</button>
        </div>
    </div>
</div>

<script>
const GEMINI_KEY = "{gemini_key}";
const FACTURES   = {factures_json};
let isOpen = false;
let dotInterval;

function toggleChat(){{
    isOpen = !isOpen;
    const w   = document.getElementById('chat-widget');
    const dot = document.getElementById('notif-dot');
    if(isOpen){{
        w.classList.add('open');
        dot.style.display='none';
        scrollBottom();
    }}else{{
        w.classList.remove('open');
    }}
}}

function scrollBottom(){{
    const m = document.getElementById('chat-messages');
    m.scrollTop = m.scrollHeight;
}}

function addMsg(content, role){{
    const msgs = document.getElementById('chat-messages');
    const div  = document.createElement('div');
    div.className = role==='user' ? 'wmsg-user' : 'wmsg-bot';
    if(role==='bot'){{
        div.innerHTML = '<div class="sender">🐱 FactureCat</div>' + content;
    }}else{{
        div.textContent = content;
    }}
    msgs.appendChild(div);
    scrollBottom();
}}

function clearChat(){{
    document.getElementById('chat-messages').innerHTML='';
    addMsg('Chat effacé ! Nouvelle conversation 🐾','bot');
}}

function showThinking(show){{
    const t = document.getElementById('thinking');
    t.style.display = show ? 'block' : 'none';
    if(show){{
        let i=0;
        const dots=['.','..','.','..','...'];
        dotInterval = setInterval(()=>{{
            document.getElementById('dots').textContent=dots[i%dots.length];
            i++;
        }},400);
    }}else{{
        clearInterval(dotInterval);
    }}
}}

async function sendMsg(){{
    const input = document.getElementById('chat-text');
    const text  = input.value.trim();
    if(!text) return;

    addMsg(text,'user');
    input.value = '';
    input.focus();

    showThinking(true);
    scrollBottom();

    const ctx = FACTURES.length>0
        ? `Factures disponibles: ${{JSON.stringify(FACTURES)}}\n`
        : "Aucune facture chargée pour l'instant.\n";

    const prompt = `Tu es FactureCat, comptable félin expert 🐱.
Réponds en français avec des emojis 🐾. Sois concis et utile.
${{ctx}}
Question: ${{text}}`;

    try{{
        const resp = await fetch(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key='+GEMINI_KEY,
            {{
                method:'POST',
                headers:{{'Content-Type':'application/json'}},
                body:JSON.stringify({{contents:[{{parts:[{{text:prompt}}]}}]}})
            }}
        );
        const data  = await resp.json();
        const reply = data.candidates[0].content.parts[0].text;
        showThinking(false);
        addMsg(reply.replace(/\\n/g,'<br>'),'bot');
    }}catch(e){{
        showThinking(false);
        addMsg('Miaou ! Une erreur est survenue 🙀 : '+e.message,'bot');
    }}
}}
</script>
</body></html>
"""
    st.components.v1.html(html, height=520, scrolling=False)


# ══════════════════════════════════════════════════════════════
# PREVIEW MODALE
# ══════════════════════════════════════════════════════════════
def render_preview(file_bytes, file_type, selected_file):
    if file_type == "application/pdf":
        pages_b64 = pdf_bytes_to_base64_pages(file_bytes)
    else:
        pages_b64 = [raw_bytes_to_base64(file_bytes)]

    if not pages_b64:
        st.warning("Impossible de prévisualiser."); return

    pages_html = ""
    modals_html = ""

    for i, b64 in enumerate(pages_b64):
        pid = f"pg{i}"; mid = f"modal{i}"
        lbl = (f"<p style='color:#c8956c;font-size:0.72rem;margin:0.3rem 0;'>"
               f"Page {i+1}/{len(pages_b64)}</p>") if len(pages_b64)>1 else ""
        pages_html += f"""
        {lbl}
        <img src="data:image/png;base64,{b64}"
             style="width:100%;border-radius:10px;cursor:zoom-in;
                    box-shadow:0 4px 15px rgba(0,0,0,0.12);
                    margin-bottom:0.4rem;transition:opacity 0.2s;"
             onclick="openModal('{mid}')" title="Cliquer pour agrandir 🔍"/>
        """
        modals_html += f"""
        <div id="{mid}" onclick="closeModal('{mid}')"
             style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;
                    background:rgba(0,0,0,0.88);z-index:99999;
                    justify-content:center;align-items:center;padding:1rem;">
            <div onclick="event.stopPropagation()"
                 style="background:white;border-radius:20px;padding:1.5rem;
                        max-width:92vw;max-height:92vh;overflow-y:auto;
                        position:relative;min-width:300px;">
                <button onclick="closeModal('{mid}')"
                        style="position:absolute;top:0.8rem;right:0.8rem;
                               background:#f0a070;border:none;border-radius:50%;
                               width:34px;height:34px;color:white;font-size:1rem;
                               cursor:pointer;font-weight:900;">✕</button>
                <p style="color:#a0522d;font-weight:800;margin-bottom:0.8rem;padding-right:2.5rem;">
                    📄 {selected_file}{"&nbsp;— Page "+str(i+1) if len(pages_b64)>1 else ""}
                </p>
                <div style="display:flex;gap:0.5rem;margin-bottom:0.8rem;align-items:center;flex-wrap:wrap;">
                    <button onclick="zoom('{mid}_img','{mid}_pct',-1)"
                            style="background:#f0a070;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.9rem;font-size:1.1rem;
                                   cursor:pointer;font-weight:700;">−</button>
                    <span id="{mid}_pct"
                          style="color:#a0522d;font-weight:800;min-width:50px;text-align:center;">100%</span>
                    <button onclick="zoom('{mid}_img','{mid}_pct',1)"
                            style="background:#f0a070;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.9rem;font-size:1.1rem;
                                   cursor:pointer;font-weight:700;">+</button>
                    <button onclick="resetZoom('{mid}_img','{mid}_pct')"
                            style="background:#c8956c;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.9rem;font-size:0.85rem;
                                   cursor:pointer;font-weight:700;">Reset</button>
                </div>
                <div style="overflow:auto;border-radius:8px;">
                    <img id="{mid}_img" src="data:image/png;base64,{b64}"
                         data-zoom="100"
                         style="width:100%;display:block;border-radius:8px;"/>
                </div>
            </div>
        </div>
        """

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{margin:0;background:transparent;font-family:'Nunito',sans-serif;}}
</style></head><body>
<div style="overflow-y:auto;max-height:420px;padding-right:4px;">
{pages_html}
</div>
{modals_html}
<script>
function openModal(id){{
    var m = document.getElementById(id);
    m.style.display='flex';
    document.body.style.overflow='hidden';
}}
function closeModal(id){{
    document.getElementById(id).style.display='none';
    document.body.style.overflow='';
}}
function zoom(imgId,pctId,dir){{
    var img = document.getElementById(imgId);
    var cur = parseInt(img.getAttribute('data-zoom')||'100');
    cur = Math.min(Math.max(cur + dir*25, 25), 400);
    img.setAttribute('data-zoom',cur);
    img.style.width = cur+'%';
    document.getElementById(pctId).textContent = cur+'%';
}}
function resetZoom(imgId,pctId){{
    var img = document.getElementById(imgId);
    img.setAttribute('data-zoom','100');
    img.style.width='100%';
    document.getElementById(pctId).textContent='100%';
}}
document.addEventListener('keydown',function(e){{
    if(e.key==='Escape'){{
        document.querySelectorAll('[id^="modal"]').forEach(function(m){{
            m.style.display='none';
        }});
        document.body.style.overflow='';
    }}
}});
</script>
</body></html>
"""
    st.components.v1.html(html, height=440, scrolling=False)


# ══════════════════════════════════════════════════════════════
# PAGE FACTURES
# ══════════════════════════════════════════════════════════════
if page == "factures":

    for k,v in [
        ("factures",[]),("uploaded_files_data",{}),
        ("selected_rows",{}),("selected_preview",None),("pending_files",[])
    ]:
        if k not in st.session_state: st.session_state[k]=v

    # Header
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem 0;">
        <div style="font-size:4rem;">🐱</div>
        <h1 style="color:#a0522d;font-weight:900;font-size:2.2rem;margin:0.2rem 0;">FactureCat</h1>
        <p style="color:#c8956c;font-size:1rem;margin:0;">Extraction intelligente de factures 🐾</p>
        <hr style="border-color:rgba(200,149,108,0.3);margin:0.8rem auto;max-width:350px;">
    </div>
    """, unsafe_allow_html=True)

    # Bubble accueil
    if not st.session_state["factures"] and not st.session_state["pending_files"]:
        st.markdown("""
        <div class="cat-container">
            <div class="cat-avatar">😺</div>
            <div class="cat-bubble">
                <div class="cat-bubble-title">Bonjour ! Je suis FactureCat 🐾</div>
                <div class="cat-bubble-sub">Déposez vos factures ci-dessous et je m'occupe de tout extraire pour vous !</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="section-title">📤 Importer des factures</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Glissez vos factures ici",
        type=["pdf","png","jpg","jpeg","webp"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        new_files = False
        for uf in uploaded_files:
            if uf.name not in st.session_state["uploaded_files_data"]:
                fb = uf.read()
                st.session_state["uploaded_files_data"][uf.name] = {"bytes":fb,"type":uf.type}
                already = any(f.get("filename")==uf.name for f in st.session_state["factures"])
                if not already and uf.name not in st.session_state["pending_files"]:
                    st.session_state["pending_files"].append(uf.name)
                    new_files = True
        if new_files: st.rerun()

    # Pending
    if st.session_state["pending_files"]:
        nb = len(st.session_state["pending_files"])
        st.markdown(f"""
        <div class="cat-container">
            <div class="cat-avatar">🐱</div>
            <div class="cat-bubble">
                <div class="cat-bubble-title">Miaou ! {nb} fichier(s) détecté(s) et prêt(s) à être analysé(s) 🐾</div>
                <div class="cat-bubble-sub">Cliquez sur le bouton ci-dessous pour lancer l'extraction !</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns([1,3,1])
        with c2:
            st.markdown('<div class="btn-analyse-wrap">', unsafe_allow_html=True)
            if st.button("🐾 Lancer l'extraction !", use_container_width=True, key="btn_analyse"):
                for fname in list(st.session_state["pending_files"]):
                    data = st.session_state["uploaded_files_data"].get(fname)
                    if data:
                        with st.spinner(f"🐱 Analyse de {fname}..."):
                            result = analyze_invoice(data["bytes"],data["type"])
                            if result:
                                result["filename"] = fname
                                result["id"]       = len(st.session_state["factures"])
                                st.session_state["factures"].append(result)
                                st.session_state["selected_preview"] = fname
                st.session_state["pending_files"] = []
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            if st.button("🗑️ Annuler", use_container_width=True, key="cancel_pend"):
                for fn in st.session_state["pending_files"]:
                    st.session_state["uploaded_files_data"].pop(fn,None)
                st.session_state["pending_files"] = []
                st.rerun()

    # ── Résultats ──
    if st.session_state["factures"]:

        # Bubble succès
        st.markdown("""
        <div class="cat-container" style="margin-top:1rem;">
            <div class="cat-avatar">😻</div>
            <div class="cat-bubble">
                <div class="cat-bubble-title">Purrrfect ! Voici ce que j'ai trouvé 🐾</div>
                <div class="cat-bubble-sub">Vous pouvez modifier directement dans le tableau !</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_all = pd.DataFrame(st.session_state["factures"])
        nb_total   = len(df_all)
        nb_valides = int(df_all["statut"].str.contains("Validé",na=False).sum()) if "statut" in df_all.columns else 0
        nb_erreurs = int(df_all["statut"].str.contains("Erreur",na=False).sum())  if "statut" in df_all.columns else 0

        # Dashboard
        st.markdown("### 📊 Tableau de bord")
        dc1,dc2,dc3 = st.columns(3)
        for col,icon,val,cls,lbl in [
            (dc1,"🐱",nb_total,"",   "Factures traitées"),
            (dc2,"😸",nb_valides,"green","Validées"),
            (dc3,"🙀",nb_erreurs,"red",  "Erreurs"),
        ]:
            with col:
                st.markdown(f"""
                <div class="dash-card">
                    <div class="icon">{icon}</div>
                    <div class="value {cls}">{val}</div>
                    <div class="label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3 colonnes ──
        col_prev, col_info, col_metrics = st.columns([1.5,2.2,1.3], gap="medium")

        with col_prev:
            st.markdown('<div class="section-title">🖼️ Prévisualisation</div>', unsafe_allow_html=True)
            filenames = [f["filename"] for f in st.session_state["factures"]]
            if st.session_state["selected_preview"] not in filenames:
                st.session_state["selected_preview"] = filenames[0]

            sel = st.selectbox("Facture",options=filenames,
                index=filenames.index(st.session_state["selected_preview"]),
                label_visibility="collapsed",key="sel_prev")
            st.session_state["selected_preview"] = sel

            fd = st.session_state["uploaded_files_data"].get(sel)
            if fd: render_preview(fd["bytes"],fd["type"],sel)

        with col_info:
            st.markdown('<div class="section-title">🧾 Données extraites</div>', unsafe_allow_html=True)

            fac = next((f for f in st.session_state["factures"]
                        if f.get("filename")==st.session_state["selected_preview"]), None)
            if fac:
                champs = [
                    ("🏢 Fournisseur", fac.get("fournisseur","—")),
                    ("📅 Date",        fac.get("date","—")),
                    ("🔢 N° Facture",  fac.get("numero_facture","—")),
                    ("💶 Montant HT",  f"{fac.get('montant_ht',0):.2f} €"),
                    ("📊 TVA",         f"{fac.get('tva',0):.2f} €"),
                    ("💰 Montant TTC", f"{fac.get('montant_ttc',0):.2f} €"),
                    ("💱 Devise",      fac.get("devise","EUR")),
                    ("📂 Catégorie",   fac.get("categorie","—")),
                    ("✅ Statut",      fac.get("statut","—")),
                    ("📋 Description", fac.get("description","—")),
                ]
                for label,val in champs:
                    st.markdown(f"""
                    <div class="info-row">
                        <span class="info-label">{label}</span>
                        <span class="info-value">{val}</span>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">📋 Toutes les factures</div>', unsafe_allow_html=True)

            df = pd.DataFrame(st.session_state["factures"])
            cols_d = ["filename","fournisseur","date","numero_facture",
                      "montant_ht","tva","montant_ttc","statut"]
            df_d = df[[c for c in cols_d if c in df.columns]].copy()
            df_d.insert(0,"✅",False)

            st.data_editor(df_d, use_container_width=True, hide_index=True,
                column_config={
                    "✅": st.column_config.CheckboxColumn("✅",default=False),
                    "statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]
                    ),
                    "montant_ht":  st.column_config.NumberColumn("HT €",  format="%.2f"),
                    "tva":         st.column_config.NumberColumn("TVA €", format="%.2f"),
                    "montant_ttc": st.column_config.NumberColumn("TTC €", format="%.2f"),
                }, key="table_fac")

        with col_metrics:
            st.markdown('<div class="section-title">📊 Métriques</div>', unsafe_allow_html=True)
            df = pd.DataFrame(st.session_state["factures"])
            ttc = df["montant_ttc"].sum() if "montant_ttc" in df.columns else 0
            ht  = df["montant_ht"].sum()  if "montant_ht"  in df.columns else 0
            tva = df["tva"].sum()          if "tva"         in df.columns else 0

            for val,lbl in [
                (f"{ttc:.2f} €","Total TTC 🔥"),
                (f"{ht:.2f} €", "Total HT 📊"),
                (f"{tva:.2f} €","Total TVA 🧾"),
                (str(nb_total), "Nb Factures 📄"),
            ]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<div class="section-title">💾 Exports</div>', unsafe_allow_html=True)

            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine="openpyxl"); buf.seek(0)
            st.download_button("📥 Excel", data=buf,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="dl_excel")

            st.download_button("📄 CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key="dl_csv")

            if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_all"):
                for k in ["factures","pending_files"]:
                    st.session_state[k] = []
                for k in ["uploaded_files_data","selected_rows"]:
                    st.session_state[k] = {}
                st.session_state["selected_preview"] = None
                st.rerun()

        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center;padding:1rem 0;">
            <p style="font-weight:900;color:#a0522d;font-size:1.1rem;">Purrrfait travail ! 🐾</p>
            <p style="color:#c8956c;font-size:0.88rem;">FactureCat — Votre comptable félin 🐱</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        if not st.session_state.get("pending_files"):
            st.markdown("""
            <div style="text-align:center;padding:3rem 0;">
                <div style="font-size:5rem;">🐱</div>
                <p style="font-size:1.2rem;font-weight:800;color:#a0522d;margin-top:1rem;">
                    Aucune facture importée !
                </p>
                <p style="color:#c8956c;">Glissez vos factures ci-dessus pour commencer 🐾</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Chat widget ──
    render_chat_widget(st.session_state.get("factures",[]))


# ══════════════════════════════════════════════════════════════
# PAGE NOTES DE FRAIS
# ══════════════════════════════════════════════════════════════
elif page == "notes":

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem 0;">
        <div style="font-size:3rem;">💰</div>
        <h2 style="color:#a0522d;font-weight:900;margin:0.2rem 0;">Notes de frais</h2>
        <p style="color:#c8956c;font-size:0.95rem;margin:0;">Gérez vos dépenses professionnelles 🐾</p>
        <hr style="border-color:rgba(200,149,108,0.3);margin:0.8rem auto;max-width:400px;">
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1,1], gap="large")

    with col1:
        st.markdown('<div class="section-title">➕ Ajouter une dépense</div>', unsafe_allow_html=True)

        with st.form("form_notes", clear_on_submit=True):
            date_dep    = st.date_input("📅 Date", datetime.now())
            description = st.text_input("📝 Description")
            cf1,cf2 = st.columns(2)
            with cf1:
                montant = st.number_input("💰 Montant (€)", min_value=0.0, step=0.01, format="%.2f")
            with cf2:
                categorie = st.selectbox("📂 Catégorie",[
                    "Transport 🚗","Repas 🍽️","Hébergement 🏨",
                    "Fournitures 📦","Formation 🎓","Client 🤝","Autres"
                ])
            cf3,cf4 = st.columns(2)
            with cf3:
                moyen = st.selectbox("💳 Paiement",["Carte bancaire","Espèces","Virement","Chèque"])
            with cf4:
                statut = st.selectbox("✅ Statut",["En attente","Validé","Remboursé","Refusé"])
            notes       = st.text_area("📝 Notes", height=80)
            justif      = st.file_uploader("📎 Justificatif", type=["pdf","png","jpg","jpeg"])
            submitted   = st.form_submit_button("➕ Ajouter la dépense", use_container_width=True)

            if submitted:
                if not description:
                    st.warning("⚠️ Description requise !")
                elif montant <= 0:
                    st.warning("⚠️ Montant doit être > 0 !")
                else:
                    st.session_state["notes_frais"].append({
                        "Date":           date_dep.strftime("%d/%m/%Y"),
                        "Description":    description,
                        "Montant (€)":    montant,
                        "Catégorie":      categorie,
                        "Paiement":       moyen,
                        "Statut":         statut,
                        "Notes":          notes,
                        "Justificatif":   justif.name if justif else "Aucun",
                    })
                    st.success(f"✅ Dépense ajoutée ! 🐾 ({montant:.2f} €)")
                    st.rerun()

        # Analyse IA
        if st.session_state["notes_frais"]:
            st.markdown("---")
            st.markdown('<div class="section-title">🤖 Analyse IA</div>', unsafe_allow_html=True)
            if st.button("🐱 Analyser avec l'IA", use_container_width=True):
                with st.spinner("🐱 Analyse en cours..."):
                    try:
                        ctx = json.dumps(st.session_state["notes_frais"], ensure_ascii=False, indent=2)
                        r   = model.generate_content(
                            f"Tu es FactureCat 🐱. Analyse ces notes de frais :\n{ctx}\n"
                            f"Total par catégorie, anomalies, conseils. Réponds en français avec emojis 🐾."
                        )
                        st.markdown(f"""
                        <div style="background:white;border:2px solid rgba(200,149,108,0.3);
                                    border-radius:16px;padding:1rem;color:#5a3010;">
                            🐱 {r.text}
                        </div>""", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ {e}")

    with col2:
        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])
            total = df_nf["Montant (€)"].sum() if "Montant (€)" in df_nf.columns else 0
            nb    = len(df_nf)

            st.markdown('<div class="section-title">📊 Tableau des dépenses</div>', unsafe_allow_html=True)

            m1,m2 = st.columns(2)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total:.2f} €</div>
                    <div class="metric-label">Total dépenses 💰</div>
                </div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{nb}</div>
                    <div class="metric-label">Nb dépenses 📄</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.data_editor(df_nf, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["En attente","Validé","Remboursé","Refusé"]
                    ),
                    "Montant (€)": st.column_config.NumberColumn("Montant (€)", format="%.2f"),
                }, key="table_notes")

            st.markdown("---")
            st.markdown('<div class="section-title">💾 Exports</div>', unsafe_allow_html=True)
            ce1,ce2,ce3 = st.columns(3)
            with ce1:
                buf = io.BytesIO()
                df_nf.to_excel(buf,index=False,engine="openpyxl"); buf.seek(0)
                st.download_button("📥 Excel",data=buf,
                    file_name=f"notes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with ce2:
                st.download_button("📄 CSV",
                    data=df_nf.to_csv(index=False).encode("utf-8"),
                    file_name=f"notes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",use_container_width=True)
            with ce3:
                if st.button("🗑️ Effacer",use_container_width=True,key="clear_notes"):
                    st.session_state["notes_frais"] = []
                    st.rerun()
        else:
            st.markdown("""
            <div style="text-align:center;padding:4rem 0;">
                <div style="font-size:4rem;">🐱</div>
                <p style="font-size:1.1rem;font-weight:800;color:#a0522d;margin-top:1rem;">
                    Aucune dépense ajoutée !
                </p>
                <p style="color:#c8956c;">Ajoutez vos dépenses à gauche 🐾</p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;padding:1rem 0;">
        <p style="font-weight:900;color:#a0522d;font-size:1.1rem;">Purrrfait travail ! 🐾</p>
        <p style="color:#c8956c;font-size:0.88rem;">FactureCat — Votre comptable félin 🐱</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat widget
    render_chat_widget(st.session_state.get("notes_frais",[]))
