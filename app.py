import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io
from datetime import datetime

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

        if mode == "🔑 Se connecter":
            if st.button("🐾 Se connecter", use_container_width=True):
                try:
                    supabase = get_supabase()
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = email
                    st.success("✅ Connexion réussie ! 🐾")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
        else:
            if st.button("✨ Créer mon compte", use_container_width=True):
                try:
                    supabase = get_supabase()
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"]    = email
                    st.success("✅ Compte créé ! 🐾")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    return False

if not check_password():
    st.stop()

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
* { font-family: 'Nunito', sans-serif; }

[data-testid="stSidebar"]        { display: none; }
[data-testid="collapsedControl"] { display: none; }

.stApp {
    background: linear-gradient(135deg, #fdf6f0 0%, #faebd7 50%, #fdf6f0 100%);
}
.main .block-container {
    padding-top: 7rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}
.topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    background: linear-gradient(135deg, #a0522d, #c8956c);
    padding: 0.8rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(160,82,45,0.3);
}
.stButton > button {
    background: white !important;
    color: #a0522d !important;
    border: 2px solid #f0a070 !important;
    border-radius: 20px !important;
    padding: 0.6rem 2rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: #fdf6f0 !important;
    border-color: #e8856a !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(200,149,108,0.4) !important;
}
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1rem;
    text-align: center;
    border: 2px solid rgba(200,149,108,0.2);
    box-shadow: 0 4px 15px rgba(200,149,108,0.1);
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 900;
    color: #a0522d;
}
.metric-label {
    font-size: 0.8rem;
    color: #c8956c;
    font-weight: 600;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #a0522d;
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #f0a070;
}
.cat-ascii {
    font-family: monospace !important;
    font-size: 0.7rem !important;
    line-height: 1.3 !important;
    color: #a0522d;
}
.modal-overlay {
    display: none;
    position: fixed;
    top:0; left:0; right:0; bottom:0;
    background: rgba(0,0,0,0.88);
    z-index: 99999;
    justify-content: center;
    align-items: center;
    padding: 1rem;
}
.modal-overlay.open { display: flex; }
.modal-content {
    background: white;
    border-radius: 20px;
    padding: 1.5rem;
    max-width: 92vw;
    max-height: 92vh;
    overflow-y: auto;
    position: relative;
    min-width: 300px;
}
.modal-close {
    position: absolute;
    top: 0.8rem; right: 0.8rem;
    background: #f0a070;
    color: white;
    border: none;
    border-radius: 50%;
    width: 34px; height: 34px;
    font-size: 1.1rem;
    cursor: pointer;
    font-weight: 900;
    z-index: 100001;
}
[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #f0a070;
    border-radius: 16px;
    padding: 1rem;
}
hr { border-color: rgba(200,149,108,0.3) !important; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #fdf6f0; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(#f0a070, #c8956c);
    border-radius: 4px;
}

/* ── Widget Chat Flottant ── */
#chat-fab {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0a070, #a0522d);
    box-shadow: 0 6px 24px rgba(160,82,45,0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 100000;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 3px solid white;
    font-size: 2rem;
    user-select: none;
}
#chat-fab:hover {
    transform: scale(1.1) rotate(-5deg);
    box-shadow: 0 8px 28px rgba(160,82,45,0.55);
}
#chat-fab .notif-dot {
    position: absolute;
    top: 4px; right: 4px;
    width: 12px; height: 12px;
    background: #e74c3c;
    border-radius: 50%;
    border: 2px solid white;
}

#chat-widget {
    display: none;
    position: fixed;
    bottom: 6.5rem;
    right: 2rem;
    width: 360px;
    max-height: 520px;
    background: #fdf6f0;
    border-radius: 24px;
    box-shadow: 0 12px 40px rgba(160,82,45,0.35);
    z-index: 99999;
    flex-direction: column;
    overflow: hidden;
    border: 2px solid rgba(240,160,112,0.4);
    animation: slideUp 0.25s ease;
}
#chat-widget.open { display: flex; }

@keyframes slideUp {
    from { opacity:0; transform: translateY(20px) scale(0.95); }
    to   { opacity:1; transform: translateY(0)    scale(1);    }
}

/* Header widget */
#chat-header {
    background: linear-gradient(135deg, #a0522d, #c8956c);
    padding: 0.9rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.7rem;
    border-radius: 22px 22px 0 0;
}
#chat-header .cat-face {
    font-size: 2rem;
    line-height: 1;
}
#chat-header .header-text h4 {
    color: white;
    margin: 0;
    font-size: 0.95rem;
    font-weight: 800;
}
#chat-header .header-text p {
    color: #f5e6d8;
    margin: 0;
    font-size: 0.72rem;
}
#chat-header .close-btn {
    margin-left: auto;
    background: rgba(255,255,255,0.25);
    border: none;
    border-radius: 50%;
    width: 28px; height: 28px;
    color: white;
    font-size: 1rem;
    cursor: pointer;
    font-weight: 900;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.2s;
}
#chat-header .close-btn:hover { background: rgba(255,255,255,0.4); }

/* Messages */
#chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 320px;
}
.wmsg-user {
    background: linear-gradient(135deg, #f0a070, #c8956c);
    color: white;
    border-radius: 16px 16px 4px 16px;
    padding: 0.65rem 0.9rem;
    font-size: 0.85rem;
    font-weight: 600;
    align-self: flex-end;
    max-width: 85%;
    word-break: break-word;
}
.wmsg-bot {
    background: white;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px 16px 16px 4px;
    padding: 0.65rem 0.9rem;
    font-size: 0.85rem;
    color: #5a3010;
    align-self: flex-start;
    max-width: 85%;
    word-break: break-word;
    box-shadow: 0 2px 8px rgba(200,149,108,0.1);
}
.wmsg-bot .sender { font-size:0.75rem; color:#c8956c; font-weight:700; margin-bottom:0.2rem;}

/* Footer input */
#chat-footer {
    padding: 0.8rem 1rem;
    background: white;
    border-top: 2px solid rgba(240,160,112,0.2);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
#chat-input-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}
#chat-text {
    flex: 1;
    border: 2px solid rgba(240,160,112,0.4);
    border-radius: 20px;
    padding: 0.55rem 1rem;
    font-size: 0.85rem;
    font-family: 'Nunito', sans-serif;
    color: #5a3010;
    outline: none;
    background: #fdf6f0;
    transition: border-color 0.2s;
}
#chat-text:focus { border-color: #f0a070; }
#chat-text::placeholder { color: #c8956c; }

.chat-action-btn {
    background: white;
    color: #a0522d;
    border: 2px solid #f0a070;
    border-radius: 20px;
    padding: 0.5rem 1.1rem;
    font-size: 0.85rem;
    font-weight: 700;
    font-family: 'Nunito', sans-serif;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}
.chat-action-btn:hover {
    background: #fdf6f0;
    border-color: #e8856a;
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(200,149,108,0.35);
}
.chat-action-btn.send-btn {
    background: white;
    color: #a0522d;
    border-color: #f0a070;
}
.chat-action-btn.clear-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
    border-color: rgba(240,160,112,0.5);
    color: #c8956c;
}
.chat-action-btn.clear-btn:hover { border-color: #e8856a; color: #a0522d; }

#chat-footer-row2 {
    display: flex;
    gap: 0.4rem;
    justify-content: flex-end;
}
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ───────────────────────────────────────────────────────────────────
user_email = st.session_state.get("user_email", "")
st.markdown(f"""
<div class="topbar">
    <div style="display:flex; align-items:center; gap:0.8rem;">
        <span style="font-size:1.8rem;">🐱</span>
        <span style="color:white; font-weight:800; font-size:1.3rem;">FactureCat</span>
        <span style="color:#f5e6d8; font-size:0.8rem;">Votre assistant comptable félin</span>
    </div>
    <span style="color:#f5e6d8; font-size:0.85rem;">🐾 {user_email}</span>
</div>
""", unsafe_allow_html=True)

# ─── NAV ──────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "📄 Factures"

col_n1, col_n2, col_n3, col_n4 = st.columns([1, 2, 2, 1])
with col_n2:
    if st.button("📄 Factures", use_container_width=True):
        st.session_state["page"] = "📄 Factures"
        st.rerun()
with col_n3:
    if st.button("💰 Notes de frais", use_container_width=True):
        st.session_state["page"] = "💰 Notes de frais"
        st.rerun()
with col_n4:
    if st.button("🚪 Déco", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown("---")
page = st.session_state["page"]

# ─── ASCII CATS ───────────────────────────────────────────────────────────────
CAT_ASCII_PETIT = r"""
 /\_/\  
( o.o ) 
 > ^ <  
"""
CAT_ASCII_GRAND = r"""
    /\_____/\
   /  o   o  \
  ( ==  ^  == )
   )         (
  (           )
 ( (  )   (  ) )
(__(__)___(__)__)
"""

def ascii_to_html(ascii_art):
    return ascii_art.replace("\n", "<br>").replace(" ", "&nbsp;")

# ─── GEMINI ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_gemini():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel("gemini-2.5-flash")

model = get_gemini()

def extract_pdf_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def image_to_bytes(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def img_to_base64(img):
    import base64
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def pdf_bytes_to_base64_pages(pdf_bytes):
    import base64
    images = extract_pdf_images(pdf_bytes)
    return [base64.b64encode(image_to_bytes(img)).decode() for img in images]

def raw_bytes_to_base64(raw_bytes):
    import base64
    return base64.b64encode(raw_bytes).decode()

def analyze_invoice(file_bytes, file_type):
    prompt = """Tu es FactureCat 🐱, un expert comptable félin. Analyse cette facture et extrais ces informations en JSON strict :
{
  "fournisseur": "nom du fournisseur/émetteur de la facture (pas le client)",
  "date": "date au format JJ/MM/AAAA",
  "numero_facture": "numéro de facture",
  "montant_ht": 0.00,
  "tva": 0.00,
  "montant_ttc": 0.00,
  "devise": "EUR",
  "description": "description courte des prestations",
  "categorie": "Transport/Repas/Hébergement/Fournitures/Formation/Client/Autres",
  "statut": "Validé 😸 ou À vérifier 🐱 ou Erreur 🙀"
}
IMPORTANT: "fournisseur" = celui qui émet la facture, pas le destinataire.
Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

    try:
        if file_type == "application/pdf":
            images = extract_pdf_images(file_bytes)
            if not images:
                return None
            img_bytes = image_to_bytes(images[0])
            response  = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": img_bytes}
            ])
        else:
            response = model.generate_content([
                prompt,
                {"mime_type": file_type, "data": file_bytes}
            ])

        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)
    except Exception as e:
        st.error(f"❌ Erreur analyse : {e}")
        return None

# ─── PREVIEW ──────────────────────────────────────────────────────────────────
def render_preview(file_bytes, file_type, selected_file):
    import base64

    if file_type == "application/pdf":
        pages_b64 = pdf_bytes_to_base64_pages(file_bytes)
    else:
        pages_b64 = [raw_bytes_to_base64(file_bytes)]

    if not pages_b64:
        st.warning("Impossible de prévisualiser ce fichier.")
        return

    modal_html = ""
    pages_html = ""

    for i, b64 in enumerate(pages_b64):
        page_id  = f"pg_{i}"
        modal_id = f"modal_{i}"
        page_label = (f"<p style='color:#c8956c;font-size:0.75rem;margin:0.3rem 0;'>"
                      f"Page {i+1}/{len(pages_b64)}</p>") if len(pages_b64) > 1 else ""

        pages_html += f"""
        {page_label}
        <img id="{page_id}"
             src="data:image/png;base64,{b64}"
             style="width:100%;border-radius:8px;
                    box-shadow:0 4px 15px rgba(0,0,0,0.15);
                    margin-bottom:0.5rem;cursor:zoom-in;
                    transition:transform 0.2s ease;"
             onclick="openModal('{modal_id}')"
             title="Cliquez pour agrandir 🔍"/>
        """

        modal_html += f"""
        <div id="{modal_id}" class="modal-overlay" onclick="closeModal('{modal_id}')">
            <div class="modal-content" onclick="event.stopPropagation()">
                <button class="modal-close" onclick="closeModal('{modal_id}')">✕</button>
                <p style="color:#a0522d;font-weight:800;margin-bottom:0.5rem;">
                    📄 {selected_file}{"&nbsp;— Page " + str(i+1) if len(pages_b64)>1 else ""}
                </p>
                <div style="display:flex;gap:0.5rem;margin-bottom:0.8rem;align-items:center;">
                    <button onclick="zoomImg('{modal_id}_img',-10)"
                            style="background:#f0a070;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.8rem;font-size:1.1rem;
                                   cursor:pointer;font-weight:700;">−</button>
                    <span id="{modal_id}_pct"
                          style="color:#a0522d;font-weight:700;min-width:50px;text-align:center;">
                          100%</span>
                    <button onclick="zoomImg('{modal_id}_img',+10)"
                            style="background:#f0a070;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.8rem;font-size:1.1rem;
                                   cursor:pointer;font-weight:700;">+</button>
                    <button onclick="resetZoom('{modal_id}_img','{modal_id}_pct')"
                            style="background:#c8956c;border:none;border-radius:8px;
                                   color:white;padding:0.3rem 0.8rem;font-size:0.85rem;
                                   cursor:pointer;font-weight:700;">Reset</button>
                </div>
                <div style="overflow:auto;max-height:75vh;">
                    <img id="{modal_id}_img"
                         src="data:image/png;base64,{b64}"
                         style="width:100%;border-radius:8px;"
                         data-zoom="100"/>
                </div>
            </div>
        </div>
        """

    full_html = f"""
    <style>
    .modal-overlay {{
        display:none; position:fixed;
        top:0;left:0;right:0;bottom:0;
        background:rgba(0,0,0,0.88);
        z-index:99999;
        justify-content:center; align-items:center; padding:1rem;
    }}
    .modal-overlay.open {{ display:flex; }}
    .modal-content {{
        background:white; border-radius:20px; padding:1.5rem;
        max-width:92vw; max-height:92vh; overflow-y:auto;
        position:relative; min-width:300px;
    }}
    .modal-close {{
        position:absolute; top:0.8rem; right:0.8rem;
        background:#f0a070; color:white; border:none;
        border-radius:50%; width:34px; height:34px;
        font-size:1.1rem; cursor:pointer; font-weight:900; z-index:100001;
    }}
    </style>

    <div style="
        max-height:65vh; overflow-y:auto; overflow-x:hidden;
        background:#fdf6f0; border:2px solid rgba(200,149,108,0.3);
        border-radius:16px; padding:1rem;">
        {pages_html}
    </div>
    <p style="color:#c8956c;font-size:0.75rem;margin-top:0.4rem;text-align:center;">
        💡 Cliquez sur la facture → plein écran avec zoom +/−
    </p>
    {modal_html}

    <script>
    var _zooms={{}};
    function openModal(id)  {{ document.getElementById(id).classList.add('open'); }}
    function closeModal(id) {{ document.getElementById(id).classList.remove('open'); }}
    function zoomImg(imgId, delta) {{
        var img=document.getElementById(imgId);
        var pctId=imgId.replace('_img','_pct');
        var pct=_zooms[imgId]||100;
        pct=Math.min(Math.max(pct+delta*5,30),400);
        _zooms[imgId]=pct;
        img.style.width=pct+'%';
        var el=document.getElementById(pctId);
        if(el) el.textContent=pct+'%';
    }}
    function resetZoom(imgId,pctId) {{
        var img=document.getElementById(imgId);
        _zooms[imgId]=100; img.style.width='100%';
        var el=document.getElementById(pctId);
        if(el) el.textContent='100%';
    }}
    document.addEventListener('keydown',function(e){{
        if(e.key==='Escape')
            document.querySelectorAll('.modal-overlay.open')
                    .forEach(function(m){{m.classList.remove('open');}});
    }});
    </script>
    """
    st.components.v1.html(full_html, height=720, scrolling=False)
    st.download_button(
        label="📥 Télécharger",
        data=file_bytes,
        file_name=selected_file,
        mime=file_type,
        use_container_width=True,
        key=f"dl_{selected_file}"
    )

# ─── CHAT WIDGET FLOTTANT (HTML pur) ──────────────────────────────────────────
def render_chat_widget():
    factures_json = json.dumps(
        st.session_state.get("factures", []),
        ensure_ascii=False
    )
    # Historique messages HTML
    history_html = ""
    if not st.session_state.get("chat_history"):
        history_html = """
        <div class="wmsg-bot">
            <div class="sender">🐱 FactureCat</div>
            Miaou ! Je suis votre assistant comptable félin 🐾<br>
            Posez-moi vos questions sur vos factures !
        </div>"""
    else:
        for msg in st.session_state["chat_history"]:
            if msg["role"] == "user":
                history_html += f'<div class="wmsg-user">👤 {msg["content"]}</div>'
            else:
                history_html += f'<div class="wmsg-bot"><div class="sender">🐱 FactureCat</div>{msg["content"]}</div>'

    widget_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
    * {{ box-sizing:border-box; margin:0; padding:0; font-family:'Nunito',sans-serif; }}
    body {{ background:transparent; overflow:hidden; }}

    #chat-fab {{
        position:fixed; bottom:1.5rem; right:1.5rem;
        width:64px; height:64px; border-radius:50%;
        background:linear-gradient(135deg,#f0a070,#a0522d);
        box-shadow:0 6px 24px rgba(160,82,45,0.5);
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; z-index:100000;
        transition:transform 0.25s ease, box-shadow 0.25s ease;
        border:3px solid white;
        font-size:2rem; user-select:none;
    }}
    #chat-fab:hover {{
        transform:scale(1.12) rotate(-6deg);
        box-shadow:0 8px 30px rgba(160,82,45,0.6);
    }}
    #notif-dot {{
        position:absolute; top:2px; right:2px;
        width:14px; height:14px;
        background:#e74c3c; border-radius:50%;
        border:2px solid white;
        animation: pulse 1.5s infinite;
    }}
    @keyframes pulse {{
        0%,100% {{ transform:scale(1); opacity:1; }}
        50%      {{ transform:scale(1.3); opacity:0.7; }}
    }}

    #chat-widget {{
        display:none;
        position:fixed; bottom:6rem; right:1.5rem;
        width:350px; max-height:500px;
        background:#fdf6f0;
        border-radius:24px;
        box-shadow:0 12px 40px rgba(160,82,45,0.35);
        z-index:99999;
        flex-direction:column;
        overflow:hidden;
        border:2px solid rgba(240,160,112,0.4);
        animation:slideUp 0.25s ease;
    }}
    #chat-widget.open {{ display:flex; }}
    @keyframes slideUp {{
        from {{ opacity:0; transform:translateY(20px) scale(0.95); }}
        to   {{ opacity:1; transform:translateY(0) scale(1); }}
    }}

    #chat-header {{
        background:linear-gradient(135deg,#a0522d,#c8956c);
        padding:0.85rem 1rem;
        display:flex; align-items:center; gap:0.7rem;
        flex-shrink:0;
    }}
    .cat-face {{ font-size:2.2rem; line-height:1; }}
    .header-text h4 {{
        color:white; margin:0; font-size:0.95rem; font-weight:800; }}
    .header-text p {{
        color:#f5e6d8; margin:0; font-size:0.72rem; }}
    #close-btn {{
        margin-left:auto;
        background:rgba(255,255,255,0.25);
        border:none; border-radius:50%;
        width:28px; height:28px;
        color:white; font-size:1rem; cursor:pointer; font-weight:900;
        display:flex; align-items:center; justify-content:center;
        transition:background 0.2s;
    }}
    #close-btn:hover {{ background:rgba(255,255,255,0.4); }}

    #chat-messages {{
        flex:1; overflow-y:auto; padding:0.9rem;
        display:flex; flex-direction:column; gap:0.5rem;
        max-height:300px;
    }}
    #chat-messages::-webkit-scrollbar {{ width:5px; }}
    #chat-messages::-webkit-scrollbar-thumb {{
        background:#f0a070; border-radius:3px; }}

    .wmsg-user {{
        background:linear-gradient(135deg,#f0a070,#c8956c);
        color:white; border-radius:16px 16px 4px 16px;
        padding:0.6rem 0.85rem; font-size:0.83rem; font-weight:600;
        align-self:flex-end; max-width:85%; word-break:break-word;
    }}
    .wmsg-bot {{
        background:white; border:2px solid rgba(200,149,108,0.3);
        border-radius:16px 16px 16px 4px;
        padding:0.6rem 0.85rem; font-size:0.83rem; color:#5a3010;
        align-self:flex-start; max-width:85%; word-break:break-word;
        box-shadow:0 2px 8px rgba(200,149,108,0.1);
    }}
    .sender {{ font-size:0.72rem; color:#c8956c; font-weight:700; margin-bottom:0.2rem; }}

    #chat-footer {{
        padding:0.75rem 0.9rem;
        background:white;
        border-top:2px solid rgba(240,160,112,0.2);
        flex-shrink:0;
    }}
    #input-row {{
        display:flex; gap:0.5rem; align-items:center; margin-bottom:0.4rem;
    }}
    #chat-text {{
        flex:1;
        border:2px solid rgba(240,160,112,0.4);
        border-radius:20px;
        padding:0.5rem 0.9rem;
        font-size:0.83rem;
        font-family:'Nunito',sans-serif;
        color:#5a3010; outline:none;
        background:#fdf6f0;
        transition:border-color 0.2s;
    }}
    #chat-text:focus {{ border-color:#f0a070; }}
    #chat-text::placeholder {{ color:#c8956c; }}

    .fab-btn {{
        background:white; color:#a0522d;
        border:2px solid #f0a070; border-radius:20px;
        padding:0.45rem 1rem; font-size:0.82rem; font-weight:700;
        font-family:'Nunito',sans-serif;
        cursor:pointer; transition:all 0.2s ease; white-space:nowrap;
    }}
    .fab-btn:hover {{
        background:#fdf6f0; border-color:#e8856a;
        transform:translateY(-1px);
        box-shadow:0 3px 10px rgba(200,149,108,0.35);
    }}
    .fab-btn.icon-btn {{
        padding:0.45rem 0.65rem; border-color:rgba(240,160,112,0.5);
        color:#c8956c; font-size:1rem;
    }}
    .fab-btn.icon-btn:hover {{ color:#a0522d; border-color:#e8856a; }}

    #thinking {{
        display:none; font-size:0.78rem; color:#c8956c;
        padding:0.2rem 0; font-style:italic;
    }}
    </style>
    </head>
    <body>

    <!-- FAB -->
    <div id="chat-fab" onclick="toggleChat()">
        🐱🕶️
        <div id="notif-dot"></div>
    </div>

    <!-- Widget -->
    <div id="chat-widget">
        <!-- Header -->
        <div id="chat-header">
            <div class="cat-face">🐱🕶️</div>
            <div class="header-text">
                <h4>FactureCat Assistant</h4>
                <p>Votre expert comptable félin 🐾</p>
            </div>
            <button id="close-btn" onclick="toggleChat()">✕</button>
        </div>

        <!-- Messages -->
        <div id="chat-messages">
            {history_html}
        </div>

        <!-- Footer -->
        <div id="chat-footer">
            <div id="input-row">
                <input id="chat-text"
                       type="text"
                       placeholder="Ex: Total des factures ?"
                       onkeydown="if(event.key==='Enter') sendMsg()"/>
                <button class="fab-btn" onclick="sendMsg()">🐾 Envoyer</button>
                <button class="fab-btn icon-btn" onclick="clearChat()" title="Effacer le chat">🧹</button>
            </div>
            <div id="thinking">🐱 FactureCat réfléchit...</div>
        </div>
    </div>

    <script>
    const GEMINI_KEY = "{st.secrets['GEMINI_API_KEY']}";
    const FACTURES   = {factures_json};

    var isOpen = false;

    function toggleChat() {{
        isOpen = !isOpen;
        var w = document.getElementById('chat-widget');
        var dot = document.getElementById('notif-dot');
        if (isOpen) {{
            w.classList.add('open');
            dot.style.display = 'none';
            scrollBottom();
        }} else {{
            w.classList.remove('open');
        }}
    }}

    function scrollBottom() {{
        var msgs = document.getElementById('chat-messages');
        msgs.scrollTop = msgs.scrollHeight;
    }}

    function addMsg(content, role) {{
        var msgs = document.getElementById('chat-messages');
        var div  = document.createElement('div');
        div.className = role === 'user' ? 'wmsg-user' : 'wmsg-bot';
        if (role === 'bot') {{
            div.innerHTML = '<div class="sender">🐱 FactureCat</div>' + content;
        }} else {{
            div.textContent = '👤 ' + content;
        }}
        msgs.appendChild(div);
        scrollBottom();
    }}

    function clearChat() {{
        var msgs = document.getElementById('chat-messages');
        msgs.innerHTML = '<div class="wmsg-bot"><div class="sender">🐱 FactureCat</div>Chat effacé ! Nouvelle conversation 🐾</div>';
    }}

    async function sendMsg() {{
        var input = document.getElementById('chat-text');
        var text  = input.value.trim();
        if (!text) return;

        addMsg(text, 'user');
        input.value = '';

        var thinking = document.getElementById('thinking');
        thinking.style.display = 'block';

        var prompt = `Tu es FactureCat, expert comptable félin. Réponds en français avec des emojis 🐾.
Factures disponibles: ${{JSON.stringify(FACTURES)}}
Question: ${{text}}
Sois concis et utile.`;

        try {{
            var resp = await fetch(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + GEMINI_KEY,
                {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        contents: [{{ parts: [{{ text: prompt }}] }}]
                    }})
                }}
            );
            var data = await resp.json();
            var reply = data.candidates[0].content.parts[0].text;
            thinking.style.display = 'none';
            addMsg(reply, 'bot');
        }} catch(e) {{
            thinking.style.display = 'none';
            addMsg('Miaou ! Une erreur est survenue 🙀 : ' + e.message, 'bot');
        }}
    }}
    </script>
    </body>
    </html>
    """
    st.components.v1.html(widget_html, height=600, scrolling=False)


# ════════════════════════════════════════════════════════════════════════════
# PAGE FACTURES
# ════════════════════════════════════════════════════════════════════════════
if page == "📄 Factures":

    for key, default in [
        ("factures",            []),
        ("chat_history",        []),
        ("uploaded_files_data", {}),
        ("selected_rows",       {}),
        ("selected_preview",    None),
        ("pending_files",       []),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Upload
    st.markdown('<div class="section-title">📤 Importer des factures</div>',
                unsafe_allow_html=True)

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
                file_bytes = uf.read()
                st.session_state["uploaded_files_data"][uf.name] = {
                    "bytes": file_bytes, "type": uf.type
                }
                already = any(f.get("filename") == uf.name
                              for f in st.session_state["factures"])
                if not already and uf.name not in st.session_state["pending_files"]:
                    st.session_state["pending_files"].append(uf.name)
                    new_files = True
        if new_files:
            st.rerun()

    if st.session_state["pending_files"]:
        pending_names = ", ".join(st.session_state["pending_files"])
        st.info(f"📋 {len(st.session_state['pending_files'])} fichier(s) prêt(s) : {pending_names}")

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            if st.button("🐱 Lancer l'analyse IA", use_container_width=True, key="btn_analyse"):
                for fname in list(st.session_state["pending_files"]):
                    data = st.session_state["uploaded_files_data"].get(fname)
                    if data:
                        with st.spinner(f"🐱 Analyse de {fname}..."):
                            result = analyze_invoice(data["bytes"], data["type"])
                            if result:
                                result["filename"] = fname
                                result["id"]       = len(st.session_state["factures"])
                                st.session_state["factures"].append(result)
                                st.session_state["selected_preview"] = fname
                                st.success(f"✅ {fname} analysée !")
                st.session_state["pending_files"] = []
                st.rerun()
        with col_btn2:
            if st.button("🗑️ Annuler", use_container_width=True, key="cancel_pending"):
                for fname in st.session_state["pending_files"]:
                    st.session_state["uploaded_files_data"].pop(fname, None)
                st.session_state["pending_files"] = []
                st.rerun()

    if st.session_state["factures"]:
        col_prev, col_info, col_metrics = st.columns([1.6, 2, 1.4], gap="medium")

        with col_prev:
            st.markdown('<div class="section-title">🖼️ Prévisualisation</div>',
                        unsafe_allow_html=True)

            filenames = [f["filename"] for f in st.session_state["factures"]]
            if st.session_state["selected_preview"] not in filenames:
                st.session_state["selected_preview"] = filenames[0]

            selected_file = st.selectbox(
                "Choisir une facture",
                options=filenames,
                index=filenames.index(st.session_state["selected_preview"]),
                key="select_facture_preview",
                label_visibility="collapsed"
            )
            st.session_state["selected_preview"] = selected_file

            file_data = st.session_state["uploaded_files_data"].get(selected_file)
            if file_data:
                render_preview(file_data["bytes"], file_data["type"], selected_file)

        with col_info:
            st.markdown('<div class="section-title">🧾 Données extraites</div>',
                        unsafe_allow_html=True)

            facture_sel = next(
                (f for f in st.session_state["factures"]
                 if f.get("filename") == st.session_state["selected_preview"]),
                None
            )

            if facture_sel:
                champs = [
                    ("🏢 Fournisseur", facture_sel.get("fournisseur","—")),
                    ("📅 Date",        facture_sel.get("date","—")),
                    ("🔢 N° Facture",  facture_sel.get("numero_facture","—")),
                    ("💶 Montant HT",  f"{facture_sel.get('montant_ht',0):.2f} €"),
                    ("📊 TVA",         f"{facture_sel.get('tva',0):.2f} €"),
                    ("💰 Montant TTC", f"{facture_sel.get('montant_ttc',0):.2f} €"),
                    ("💱 Devise",      facture_sel.get("devise","EUR")),
                    ("📂 Catégorie",   facture_sel.get("categorie","—")),
                    ("📋 Description", facture_sel.get("description","—")),
                    ("✅ Statut",      facture_sel.get("statut","—")),
                ]
                for label, valeur in champs:
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:0.5rem 0.8rem;margin-bottom:0.4rem;
                                background:white;border-radius:10px;
                                border:1px solid rgba(200,149,108,0.2);">
                        <span style="color:#c8956c;font-size:0.82rem;font-weight:700;">{label}</span>
                        <span style="color:#a0522d;font-size:0.85rem;font-weight:800;
                                     max-width:55%;text-align:right;">{valeur}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("⏳ Sélectionnez une facture 🐾")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">📋 Toutes les factures</div>',
                        unsafe_allow_html=True)

            df = pd.DataFrame(st.session_state["factures"])
            cols_display = ["filename","fournisseur","date","numero_facture",
                            "montant_ht","tva","montant_ttc","statut"]
            df_display = df[[c for c in cols_display if c in df.columns]].copy()
            df_display.insert(0, "✅", False)

            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={{
                    "✅": st.column_config.CheckboxColumn("✅", default=False),
                    "statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸","À vérifier 🐱","Erreur 🙀","En attente 😺"]
                    ),
                }},
                key="table_factures"
            )
            for i, row in edited_df.iterrows():
                fname = df_display.iloc[i]["filename"]
                if fname:
                    st.session_state["selected_rows"][fname] = row["✅"]

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("☑️ Tout sélectionner", use_container_width=True):
                    for fname in df["filename"].tolist():
                        st.session_state["selected_rows"][fname] = True
                    st.rerun()
            with col_s2:
                if st.button("⬜ Tout désélectionner", use_container_width=True):
                    st.session_state["selected_rows"] = {}
                    st.rerun()

        with col_metrics:
            st.markdown('<div class="section-title">📊 Métriques</div>',
                        unsafe_allow_html=True)

            df = pd.DataFrame(st.session_state["factures"])
            selected_files = [f for f, c in st.session_state["selected_rows"].items() if c]

            if selected_files:
                df_metrics = df[df["filename"].isin(selected_files)]
                mode_label = f"✅ {len(selected_files)} sélectionnée(s)"
            elif st.session_state["selected_preview"]:
                df_metrics = df[df["filename"] == st.session_state["selected_preview"]]
                mode_label = "📄 Facture affichée"
            else:
                df_metrics = df
                mode_label = "📊 Toutes"

            st.markdown(f"<p style='color:#c8956c;font-size:0.78rem;text-align:center;"
                        f"margin-bottom:0.8rem;'>{mode_label}</p>",
                        unsafe_allow_html=True)

            total_ttc   = df_metrics["montant_ttc"].sum() if "montant_ttc" in df_metrics.columns else 0
            total_ht    = df_metrics["montant_ht"].sum()  if "montant_ht"  in df_metrics.columns else 0
            total_tva   = df_metrics["tva"].sum()          if "tva"         in df_metrics.columns else 0
            nb_factures = len(df_metrics)

            for val, label in [
                (f"{total_ttc:.2f} €", "Total TTC 🔥"),
                (f"{total_ht:.2f} €",  "Total HT 📊"),
                (f"{total_tva:.2f} €", "Total TVA 🧾"),
                (str(nb_factures),     "Nb Factures 📄"),
            ]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<div class="section-title">💾 Exports</div>',
                        unsafe_allow_html=True)

            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            st.download_button("📥 Excel", data=buffer,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="export_excel")

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button("📄 CSV", data=csv_data,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key="export_csv")

            if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_factures"):
                for k in ["factures","uploaded_files_data","selected_rows",
                          "selected_preview","pending_files","chat_history"]:
                    st.session_state[k] = [] if k != "selected_preview" else None
                    if k in ["uploaded_files_data","selected_rows"]:
                        st.session_state[k] = {}
                st.rerun()

    else:
        if not st.session_state.get("pending_files"):
            st.markdown(f"""
            <div style="text-align:center;padding:4rem 0;">
                <div class="cat-ascii" style="font-size:1rem !important;">
                    {ascii_to_html(CAT_ASCII_GRAND)}</div>
                <p style="font-size:1.3rem;font-weight:800;color:#a0522d;margin-top:1rem;">
                    Aucune facture importée !</p>
                <p style="color:#c8956c;">Glissez vos factures ci-dessus pour commencer 🐾</p>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE NOTES DE FRAIS
# ════════════════════════════════════════════════════════════════════════════
elif page == "💰 Notes de frais":

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-title">➕ Ajouter une dépense</div>',
                    unsafe_allow_html=True)

        with st.form("form_note_frais", clear_on_submit=True):
            date_depense = st.date_input("📅 Date", datetime.now())
            description  = st.text_input("📝 Description")

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                montant = st.number_input("💰 Montant (€)", min_value=0.0,
                                          step=0.01, format="%.2f")
            with col_f2:
                categorie = st.selectbox("📂 Catégorie", [
                    "Transport 🚗","Repas 🍽️","Hébergement 🏨",
                    "Fournitures 📦","Formation 🎓","Client 🤝","Autres"
                ])

            col_f3, col_f4 = st.columns(2)
            with col_f3:
                moyen_paiement = st.selectbox("💳 Paiement", [
                    "Carte bancaire","Espèces","Virement","Chèque"
                ])
            with col_f4:
                statut = st.selectbox("📊 Statut", [
                    "En attente 😺","Validé 😸","À vérifier 🐱","Refusé 🙀"
                ])

            justificatif = st.file_uploader("📎 Justificatif",
                                            type=["pdf","png","jpg","jpeg"])
            notes = st.text_area("📌 Notes", height=80)

            submitted = st.form_submit_button("🐾 Ajouter la dépense",
                                              use_container_width=True)
            if submitted:
                if not description:
                    st.error("❌ La description est obligatoire !")
                elif montant <= 0:
                    st.error("❌ Le montant doit être supérieur à 0 !")
                else:
                    note = {
                        "id":                len(st.session_state["notes_frais"]),
                        "Date":              date_depense.strftime("%d/%m/%Y"),
                        "Description":       description,
                        "Montant (€)":       montant,
                        "Catégorie":         categorie,
                        "Moyen de paiement": moyen_paiement,
                        "Statut":            statut,
                        "Justificatif":      justificatif.name if justificatif else "Aucun",
                        "Notes":             notes
                    }
                    st.session_state["notes_frais"].append(note)
                    st.success(f"✅ Dépense ajoutée ! 🐾 ({montant:.2f} €)")
                    st.rerun()

        if st.session_state["notes_frais"]:
            st.markdown("---")
            st.markdown('<div class="section-title">🤖 Analyse IA</div>',
                        unsafe_allow_html=True)
            if st.button("🐱 Analyser avec l'IA", use_container_width=True):
                with st.spinner("🐱 Analyse en cours..."):
                    try:
                        notes_ctx = json.dumps(st.session_state["notes_frais"],
                                               ensure_ascii=False, indent=2)
                        resp = model.generate_content(
                            f"Tu es FactureCat 🐱. Analyse ces notes de frais : "
                            f"total par catégorie, anomalies, conseils.\n{notes_ctx}\n"
                            f"Réponds en français avec emojis 🐾."
                        )
                        st.markdown(
                            f'<div style="background:white;border:2px solid rgba(200,149,108,0.3);'
                            f'border-radius:16px;padding:1rem;color:#5a3010;">'
                            f'🐱 {resp.text}</div>',
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

    with col2:
        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])
            df_nf = df_nf.drop(columns=["id"], errors="ignore")

            total_dep = df_nf["Montant (€)"].sum() if "Montant (€)" in df_nf.columns else 0
            nb_dep    = len(df_nf)

            st.markdown('<div class="section-title">📊 Tableau des dépenses</div>',
                        unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{total_dep:.2f} €</div>
                    <div class="metric-label">Total dépenses 💰</div></div>""",
                    unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{nb_}
