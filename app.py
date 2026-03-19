import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime
import base64
import streamlit.components.v1 as components

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
# CSS GLOBAL
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
.section-title{
    font-size:1rem;font-weight:800;color:#a0522d;
    margin-bottom:0.8rem;padding-bottom:0.35rem;
    border-bottom:2px solid rgba(240,160,112,0.5);
}
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
.info-row{
    display:flex;justify-content:space-between;align-items:center;
    padding:0.45rem 0.8rem;margin-bottom:0.35rem;
    background:white;border-radius:10px;
    border:1px solid rgba(200,149,108,0.2);
}
.info-label{color:#c8956c;font-size:0.8rem;font-weight:700;}
.info-value{color:#a0522d;font-size:0.83rem;font-weight:800;max-width:55%;text-align:right;}
[data-testid="stFileUploader"]{
    background:white;border:2px dashed #f0a070;border-radius:16px;padding:1rem;
}
hr{border-color:rgba(200,149,108,0.3) !important;}
::-webkit-scrollbar{width:8px;}
::-webkit-scrollbar-track{background:#fdf6f0;}
::-webkit-scrollbar-thumb{background:linear-gradient(#f0a070,#c8956c);border-radius:4px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state["page"] = "factures"

user_email = st.session_state.get("user_email","")

st.markdown(f"""
<div style="position:fixed;top:0;left:0;right:0;z-index:9999;
    background:linear-gradient(135deg,#a0522d,#c8956c);
    padding:0.6rem 2rem;
    display:flex;align-items:center;justify-content:space-between;
    box-shadow:0 4px 20px rgba(160,82,45,0.3);">
    <div style="display:flex;align-items:center;gap:0.8rem;">
        <span style="font-size:1.8rem;">🐱</span>
        <span style="color:white;font-weight:800;font-size:1.2rem;">FactureCat</span>
        <span style="color:rgba(255,255,255,0.6);font-size:0.75rem;">Votre assistant comptable félin</span>
    </div>
    <div style="color:rgba(255,255,255,0.85);font-size:0.8rem;">🐾 {user_email}</div>
</div>
""", unsafe_allow_html=True)

# ── NAV CENTRÉE ──
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
_, nc1, nc2, nc3, _ = st.columns([2,1,1,1,2])
with nc1:
    if st.button("📄 Factures", use_container_width=True, key="nav_fac"):
        st.session_state["page"] = "factures"; st.rerun()
with nc2:
    if st.button("💰 Notes de frais", use_container_width=True, key="nav_notes"):
        st.session_state["page"] = "notes"; st.rerun()
with nc3:
    if st.button("🚪 Déconnexion", use_container_width=True, key="nav_deco"):
        st.session_state["authenticated"] = False
        st.session_state["page"] = "factures"
        st.rerun()

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

def analyze_invoice(file_bytes, file_type):
    prompt = """Tu es FactureCat. Analyse cette facture. Réponds UNIQUEMENT en JSON strict :
{
  "fournisseur":"nom émetteur",
  "date":"JJ/MM/AAAA",
  "numero_facture":"...",
  "montant_ht":0.00,
  "tva":0.00,
  "montant_ttc":0.00,
  "devise":"EUR",
  "description":"...",
  "categorie":"Transport/Repas/Hébergement/Fournitures/Formation/Client/Autres",
  "statut":"Validé 😸 ou À vérifier 🐱 ou Erreur 🙀"
}"""
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

def render_preview(file_bytes, file_type, filename):
    try:
        if file_type == "application/pdf":
            images = extract_pdf_images(file_bytes)
            if images:
                buf = io.BytesIO()
                images[0].save(buf, format="PNG")
                st.image(buf.getvalue(), use_container_width=True,
                         caption=f"📄 {filename}")
        else:
            st.image(file_bytes, use_container_width=True, caption=f"🖼️ {filename}")
    except Exception as e:
        st.error(f"❌ Prévisualisation : {e}")

# ══════════════════════════════════════════════════════════════
# CHAT WIDGET FLOTTANT
# ══════════════════════════════════════════════════════════════
def render_chat_widget(data):
    data_json  = json.dumps(data, ensure_ascii=False)
    gemini_key = st.secrets["GEMINI_API_KEY"]

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Nunito',sans-serif;}}
body{{background:transparent;}}

#fab{{
    position:fixed;bottom:2rem;right:2rem;
    width:64px;height:64px;border-radius:50%;
    background:linear-gradient(135deg,#f0a070,#a0522d);
    box-shadow:0 6px 24px rgba(160,82,45,0.5);
    display:flex;align-items:center;justify-content:center;
    cursor:pointer;z-index:999999;font-size:2rem;
    border:3px solid white;user-select:none;
    transition:transform 0.25s,box-shadow 0.25s;
}}
#fab:hover{{transform:scale(1.12) rotate(-6deg);box-shadow:0 8px 30px rgba(160,82,45,0.6);}}

#dot{{
    position:absolute;top:2px;right:2px;
    width:14px;height:14px;background:#e74c3c;
    border-radius:50%;border:2px solid white;
    animation:pulse 1.5s infinite;
}}
@keyframes pulse{{0%,100%{{transform:scale(1);}}50%{{transform:scale(1.3);}}}}

#widget{{
    display:none;position:fixed;
    bottom:7.5rem;right:2rem;width:360px;
    background:#fdf6f0;border-radius:24px;
    box-shadow:0 14px 50px rgba(160,82,45,0.35);
    z-index:999998;flex-direction:column;overflow:hidden;
    border:2px solid rgba(240,160,112,0.35);
}}
#widget.open{{display:flex;animation:slideUp 0.25s ease;}}
@keyframes slideUp{{
    from{{opacity:0;transform:translateY(20px) scale(0.95);}}
    to{{opacity:1;transform:translateY(0) scale(1);}}
}}

#whead{{
    background:linear-gradient(135deg,#a0522d,#c8956c);
    padding:0.85rem 1.1rem;
    display:flex;align-items:center;gap:0.7rem;
}}
#whead .face{{font-size:2rem;}}
#whead .txt h4{{color:white;margin:0;font-size:0.9rem;font-weight:800;}}
#whead .txt p{{color:rgba(255,255,255,0.8);margin:0;font-size:0.7rem;}}
#whead .cls{{
    margin-left:auto;background:rgba(255,255,255,0.2);
    border:none;border-radius:50%;width:28px;height:28px;
    color:white;font-size:1rem;cursor:pointer;font-weight:900;
    display:flex;align-items:center;justify-content:center;
}}
#whead .cls:hover{{background:rgba(255,255,255,0.35);}}

#msgs{{
    flex:1;overflow-y:auto;padding:0.9rem;
    display:flex;flex-direction:column;gap:0.5rem;
    max-height:280px;min-height:100px;
}}
#msgs::-webkit-scrollbar{{width:4px;}}
#msgs::-webkit-scrollbar-thumb{{background:#f0a070;border-radius:2px;}}

.mu{{
    background:linear-gradient(135deg,#f0a070,#c8956c);
    color:white;border-radius:16px 16px 4px 16px;
    padding:0.55rem 0.85rem;font-size:0.82rem;font-weight:600;
    align-self:flex-end;max-width:84%;word-break:break-word;
}}
.mb{{
    background:white;border:2px solid rgba(200,149,108,0.25);
    border-radius:16px 16px 16px 4px;
    padding:0.55rem 0.85rem;font-size:0.82rem;color:#5a3010;
    align-self:flex-start;max-width:84%;word-break:break-word;
}}
.mb .s{{font-size:0.7rem;color:#c8956c;font-weight:800;margin-bottom:0.15rem;}}

#think{{
    padding:0.4rem 0.9rem;color:#c8956c;font-size:0.78rem;
    font-style:italic;background:white;
    border-top:1px solid rgba(240,160,112,0.2);display:none;
}}

#foot{{padding:0.7rem 0.85rem;background:white;border-top:2px solid rgba(240,160,112,0.2);}}
#irow{{display:flex;gap:0.4rem;align-items:center;}}
#inp{{
    flex:1;border:2px solid rgba(240,160,112,0.4);
    border-radius:20px;padding:0.48rem 0.9rem;
    font-size:0.82rem;font-family:'Nunito',sans-serif;
    color:#5a3010;outline:none;background:#fdf6f0;
}}
#inp:focus{{border-color:#f0a070;}}
#inp::placeholder{{color:#c8956c;opacity:0.8;}}

.btn{{
    background:white;color:#a0522d;
    border:2px solid #f0a070;border-radius:20px;
    padding:0.46rem 0.9rem;font-size:0.82rem;font-weight:700;
    font-family:'Nunito',sans-serif;cursor:pointer;
    transition:all 0.2s;white-space:nowrap;
    display:flex;align-items:center;gap:0.25rem;
}}
.btn:hover{{
    background:#fdf6f0;border-color:#e8856a;
    transform:translateY(-1px);
    box-shadow:0 3px 10px rgba(200,149,108,0.3);
}}
.btn.sm{{padding:0.46rem 0.6rem;font-size:0.9rem;color:#c8956c;border-color:rgba(240,160,112,0.5);}}
.btn.sm:hover{{color:#a0522d;border-color:#e8856a;}}
</style>
</head><body>

<div id="fab" onclick="toggle()">🐱<div id="dot"></div></div>

<div id="widget">
  <div id="whead">
    <div class="face">🐱</div>
    <div class="txt">
      <h4>FactureCat Assistant 🐾</h4>
      <p>Posez-moi vos questions comptables !</p>
    </div>
    <button class="cls" onclick="toggle()">✕</button>
  </div>

  <div id="msgs">
    <div class="mb">
      <div class="s">🐱 FactureCat</div>
      Bonjour ! Je suis FactureCat 🐾<br>
      <span style="color:#c8956c;font-size:0.77rem;">
        Posez-moi vos questions sur vos factures !
      </span>
    </div>
  </div>

  <div id="think">🐱 FactureCat réfléchit<span id="dots">...</span></div>

  <div id="foot">
    <div id="irow">
      <input id="inp" type="text"
             placeholder="Ex: Total des factures ?"
             onkeydown="if(event.key==='Enter')send()"/>
      <button class="btn" onclick="send()">🐾 Envoyer</button>
      <button class="btn sm" onclick="clear2()" title="Effacer">🧹</button>
    </div>
  </div>
</div>

<script>
const KEY  = "{gemini_key}";
const DATA = {data_json};
let open=false, dotTimer;

function toggle(){{
  open=!open;
  document.getElementById('widget').classList.toggle('open',open);
  if(open){{document.getElementById('dot').style.display='none';scroll();}}
}}
function scroll(){{
  const m=document.getElementById('msgs');m.scrollTop=m.scrollHeight;
}}
function addMsg(html,role){{
  const m=document.getElementById('msgs');
  const d=document.createElement('div');
  d.className=role==='user'?'mu':'mb';
  if(role==='bot') d.innerHTML='<div class="s">🐱 FactureCat</div>'+html;
  else d.textContent=html;
  m.appendChild(d);scroll();
}}
function clear2(){{
  document.getElementById('msgs').innerHTML='';
  addMsg('Chat effacé ! 🐾','bot');
}}
function thinking(on){{
  const t=document.getElementById('think');
  t.style.display=on?'block':'none';
  if(on){{
    let i=0;const d=['.','..','...'];
    dotTimer=setInterval(()=>{{document.getElementById('dots').textContent=d[i++%3];}},400);
  }}else clearInterval(dotTimer);
}}
async function send(){{
  const inp=document.getElementById('inp');
  const txt=inp.value.trim();if(!txt)return;
  addMsg(txt,'user');inp.value='';inp.focus();
  thinking(true);scroll();
  const ctx=DATA.length>0
    ?'Données disponibles: '+JSON.stringify(DATA)+'\n'
    :'Aucune donnée chargée.\n';
  const prompt=`Tu es FactureCat, comptable félin expert 🐱.
Réponds en français avec des emojis 🐾. Sois concis et précis.
${{ctx}}
Question: ${{txt}}`;
  try{{
    const r=await fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key='+KEY,
      {{method:'POST',headers:{{'Content-Type':'application/json'}},
       body:JSON.stringify({{contents:[{{parts:[{{text:prompt}}]}}]}})}}
    );
    const j=await r.json();
    const ans=j?.candidates?.[0]?.content?.parts?.[0]?.text||'Miaou... je n\\'ai pas compris 🐱';
    thinking(false);addMsg(ans,'bot');
  }}catch(e){{
    thinking(false);addMsg('❌ Erreur: '+e.message,'bot');
  }}
}}
</script>
</body></html>
"""
    components.html(html, height=0, scrolling=False)


# ══════════════════════════════════════════════════════════════
# PAGE FACTURES
# ══════════════════════════════════════════════════════════════
if page == "factures":

    for k,v in [
        ("factures",[]),("uploaded_files_data",{}),
        ("selected_preview",None),("pending_files",[])
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

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
        for uf in uploaded_files:
            if uf.name not in st.session_state["uploaded_files_data"]:
                fb = uf.read()
                st.session_state["uploaded_files_data"][uf.name] = {"bytes":fb,"type":uf.type}
                already = any(f.get("filename")==uf.name for f in st.session_state["factures"])
                if not already and uf.name not in st.session_state["pending_files"]:
                    st.session_state["pending_files"].append(uf.name)
        st.rerun()

    # Pending
    if st.session_state["pending_files"]:
        nb = len(st.session_state["pending_files"])
        st.markdown(f"""
        <div class="cat-container">
            <div class="cat-avatar">🐱</div>
            <div class="cat-bubble">
                <div class="cat-bubble-title">🐱 Miaou ! {nb} fichier(s) détecté(s) et prêt(s) à être analysé(s) 🐾</div>
                <div class="cat-bubble-sub">Cliquez sur le bouton ci-dessous pour lancer l'extraction !</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns([1,3,1])
        with c2:
            st.markdown('<div class="btn-analyse-wrap">', unsafe_allow_html=True)
            if st.button("🐾 Lancer l'extraction !", use_container_width=True, key="btn_run"):
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
            (dc1,"🐱",nb_total,"",     "Factures traitées"),
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

        # 3 colonnes
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
            if fd:
                render_preview(fd["bytes"],fd["type"],sel)

        with col_info:
            st.markdown('<div class="section-title">🧾 Données extraites</div>', unsafe_allow_html=True)
            fac = next((f for f in st.session_state["factures"]
                        if f.get("filename")==st.session_state["selected_preview"]),None)
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
            st.data_editor(df_d, use_container_width=True, hide_index=True,
                column_config={
                    "statut": st.column_config.SelectboxColumn("Statut",
                        options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]),
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
                st.session_state["factures"]           = []
                st.session_state["pending_files"]      = []
                st.session_state["uploaded_files_data"]= {}
                st.session_state["selected_preview"]   = None
                st.rerun()

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
            notes  = st.text_area("📝 Notes", height=70)
            justif = st.file_uploader("📎 Justificatif", type=["pdf","png","jpg","jpeg"])
            sub    = st.form_submit_button("➕ Ajouter la dépense", use_container_width=True)

            if sub:
                if not description:
                    st.warning("⚠️ Description requise !")
                elif montant <= 0:
                    st.warning("⚠️ Montant doit être > 0 !")
                else:
                    st.session_state["notes_frais"].append({
                        "Date":        date_dep.strftime("%d/%m/%Y"),
                        "Description": description,
                        "Montant (€)": montant,
                        "Catégorie":   categorie,
                        "Paiement":    moyen,
                        "Statut":      statut,
                        "Notes":       notes,
                        "Justificatif":justif.name if justif else "Aucun",
                    })
                    st.success(f"✅ Dépense ajoutée ! 🐾 ({montant:.2f} €)")
                    st.rerun()

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
                                    border-radius:16px;padding:1rem;color:#5a3010;margin-top:0.5rem;">
                            🐱 {r.text}
                        </div>""", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ {e}")

    with col2:
        if st.session_state["notes_frais"]:
            df_nf  = pd.DataFrame(st.session_state["notes_frais"])
            total  = df_nf["Montant (€)"].sum() if "Montant (€)" in df_nf.columns else 0
            nb     = len(df_nf)

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
                    "Statut": st.column_config.SelectboxColumn("Statut",
                        options=["En attente","Validé","Remboursé","Refusé"]),
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

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;padding:1rem 0;">
        <p style="font-weight:900;color:#a0522d;font-size:1.1rem;">Purrrfait travail ! 🐾</p>
        <p style="color:#c8956c;font-size:0.88rem;">FactureCat — Votre comptable félin 🐱</p>
    </div>
    """, unsafe_allow_html=True)

    render_chat_widget(st.session_state.get("notes_frais",[]))
