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
</style>
""", unsafe_allow_html=True)

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
CAT_ASCII_PETIT = (
    "  /\\_/\\\n"
    " ( ^.^ )\n"
    "  > 🐾 <"
)

def ascii_to_html(ascii_art: str) -> str:
    return ascii_art.replace("\n", "<br>")

# ─── CHATBOT FLOTTANT HTML/JS ──────────────────────────────────────────────────
def render_chat_widget(notes_frais_data=None, factures_data=None):
    """Chatbot flottant qui suit le défilement — HTML/JS pur via components.html"""

    ctx_factures = json.dumps(factures_data or [], ensure_ascii=False)
    ctx_notes    = json.dumps(notes_frais_data or [], ensure_ascii=False)
    api_key      = st.secrets["GEMINI_API_KEY"]

    components.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Nunito',sans-serif; }}

  /* ── Bouton flottant ── */
  #fab {{
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0a070, #e8856a);
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 24px rgba(200,149,108,0.6);
    font-size: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999999;
    transition: transform 0.3s, box-shadow 0.3s;
    user-select: none;
  }}
  #fab:hover {{
    transform: scale(1.13) translateY(-3px);
    box-shadow: 0 8px 32px rgba(200,149,108,0.8);
  }}
  #fab .badge {{
    position: absolute;
    top: -4px; right: -4px;
    background: #e05050;
    color: white;
    border-radius: 50%;
    width: 22px; height: 22px;
    font-size: 0.65rem;
    font-weight: 800;
    display: none;
    align-items: center;
    justify-content: center;
    border: 2px solid white;
  }}

  /* ── Fenêtre chat ── */
  #chatbox {{
    position: fixed;
    bottom: 7rem;
    right: 2rem;
    width: 360px;
    height: 520px;
    background: #fff8f3;
    border-radius: 24px;
    box-shadow: 0 12px 50px rgba(200,149,108,0.4);
    border: 2px solid #f0d5c0;
    z-index: 999998;
    flex-direction: column;
    overflow: hidden;
    display: none;
    opacity: 0;
    transform: scale(0.85) translateY(20px);
    transition: opacity 0.3s cubic-bezier(.34,1.56,.64,1),
                transform 0.3s cubic-bezier(.34,1.56,.64,1);
  }}
  #chatbox.open {{
    display: flex;
  }}
  #chatbox.visible {{
    opacity: 1;
    transform: scale(1) translateY(0);
  }}

  /* Header */
  #chat-header {{
    background: linear-gradient(135deg, #f0a070, #e8856a);
    padding: 0.9rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    flex-shrink: 0;
  }}
  #chat-header .avatar {{
    font-size: 2rem;
    line-height: 1;
  }}
  #chat-header .info {{ flex:1; }}
  #chat-header .info .name {{
    color: white; font-weight: 800; font-size: 1rem; margin:0;
  }}
  #chat-header .info .status {{
    color: #fff8f3; font-size: 0.72rem; margin:0;
    display: flex; align-items: center; gap: 0.3rem;
  }}
  #chat-header .info .status::before {{
    content:''; width:7px; height:7px;
    background:#7fff7f; border-radius:50%; display:inline-block;
  }}
  #btn-close {{
    background: rgba(255,255,255,0.25);
    border: none; border-radius: 50%;
    width: 30px; height: 30px;
    color: white; font-size: 1rem; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.2s;
  }}
  #btn-close:hover {{ background: rgba(255,255,255,0.45); }}

  /* Messages */
  #chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    scroll-behavior: smooth;
  }}
  #chat-messages::-webkit-scrollbar {{ width: 4px; }}
  #chat-messages::-webkit-scrollbar-track {{ background: transparent; }}
  #chat-messages::-webkit-scrollbar-thumb {{
    background: #f0d5c0; border-radius: 4px;
  }}

  .msg-row {{
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
  }}
  .msg-row.user {{ flex-direction: row-reverse; }}

  .msg-avatar {{
    font-size: 1.4rem;
    flex-shrink: 0;
    width: 32px;
    text-align: center;
  }}

  .bubble {{
    max-width: 75%;
    padding: 0.65rem 1rem;
    border-radius: 18px;
    font-size: 0.88rem;
    line-height: 1.5;
    word-break: break-word;
  }}
  .bubble.bot {{
    background: white;
    border: 1.5px solid #f0d5c0;
    color: #5a3e2b;
    border-radius: 4px 18px 18px 18px;
    box-shadow: 0 2px 8px rgba(200,149,108,0.12);
  }}
  .bubble.user {{
    background: linear-gradient(135deg, #f0a070, #e8856a);
    color: white;
    border-radius: 18px 18px 4px 18px;
    box-shadow: 0 2px 8px rgba(200,149,108,0.3);
  }}

  /* Typing */
  .typing-dots {{
    display: flex; gap: 4px; padding: 0.5rem 0.2rem; align-items: center;
  }}
  .typing-dots span {{
    width: 7px; height: 7px;
    background: #c8956c; border-radius: 50%;
    animation: bounce 1.2s infinite;
  }}
  .typing-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
  .typing-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
  @keyframes bounce {{
    0%,60%,100% {{ transform: translateY(0); }}
    30% {{ transform: translateY(-6px); }}
  }}

  /* Suggestions */
  #suggestions {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    padding: 0 1rem 0.5rem 1rem;
  }}
  .chip {{
    background: white;
    border: 1.5px solid #f0d5c0;
    color: #c8956c;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }}
  .chip:hover {{
    background: #f0a070;
    color: white;
    border-color: #f0a070;
    transform: translateY(-1px);
  }}

  /* Input zone */
  #chat-input-zone {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.8rem 1rem;
    background: white;
    border-top: 1.5px solid #f0d5c0;
    flex-shrink: 0;
  }}
  #chat-input {{
    flex: 1;
    border: 1.5px solid #f0d5c0;
    border-radius: 20px;
    padding: 0.55rem 1rem;
    font-size: 0.88rem;
    font-family: 'Nunito', sans-serif;
    outline: none;
    background: #fff8f3;
    color: #5a3e2b;
    transition: border 0.2s;
  }}
  #chat-input:focus {{ border-color: #f0a070; }}
  #btn-send {{
    background: linear-gradient(135deg, #f0a070, #e8856a);
    border: none; border-radius: 50%;
    width: 38px; height: 38px;
    color: white; font-size: 1.1rem;
    cursor: pointer; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 10px rgba(200,149,108,0.4);
  }}
  #btn-send:hover {{
    transform: scale(1.1);
    box-shadow: 0 4px 16px rgba(200,149,108,0.6);
  }}
  #btn-clear {{
    background: none; border: none;
    font-size: 1rem; cursor: pointer;
    color: #c8956c; opacity: 0.6;
    transition: opacity 0.2s;
    flex-shrink: 0;
  }}
  #btn-clear:hover {{ opacity: 1; }}
</style>
</head>
<body>

<!-- Bouton flottant -->
<button id="fab" onclick="toggleChat()" title="FactureCat Assistant">
  <span id="fab-icon">🐱🕶️</span>
  <span class="badge" id="badge">0</span>
</button>

<!-- Fenêtre chat -->
<div id="chatbox">

  <!-- Header -->
  <div id="chat-header">
    <div class="avatar">🐱🕶️</div>
    <div class="info">
      <p class="name">FactureCat Assistant</p>
      <p class="status">En ligne — prêt à miauder</p>
    </div>
    <button id="btn-close" onclick="toggleChat()">✕</button>
  </div>

  <!-- Messages -->
  <div id="chat-messages">
    <div class="msg-row bot">
      <div class="msg-avatar">🐱</div>
      <div class="bubble bot">
        Miaou ! 👓 Je suis <strong>FactureCat</strong>, votre assistant comptable félin !<br><br>
        Je connais vos factures et notes de frais. Posez-moi n'importe quelle question 🐾
      </div>
    </div>
  </div>

  <!-- Suggestions -->
  <div id="suggestions">
    <span class="chip" onclick="askSuggestion('Quel est le total TTC ?')">💶 Total TTC</span>
    <span class="chip" onclick="askSuggestion('Quels sont mes fournisseurs ?')">🏢 Fournisseurs</span>
    <span class="chip" onclick="askSuggestion('Combien de factures ?')">📄 Nb factures</span>
    <span class="chip" onclick="askSuggestion('Résume mes notes de frais')">💳 Notes de frais</span>
    <span class="chip" onclick="askSuggestion('Quelles factures sont en attente ?')">⏳ En attente</span>
  </div>

  <!-- Input -->
  <div id="chat-input-zone">
    <button id="btn-clear" onclick="clearChat()" title="Effacer">🗑️</button>
    <input
      id="chat-input"
      type="text"
      placeholder="Posez votre question à FactureCat... 🐾"
      onkeydown="if(event.key==='Enter') sendMsg()"
      autocomplete="off"
    />
    <button id="btn-send" onclick="sendMsg()">➤</button>
  </div>

</div>

<script>
  // ── Données contexte ──
  const FACTURES = {ctx_factures};
  const NOTES    = {ctx_notes};
  const API_KEY  = "{api_key}";
  const API_URL  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + API_KEY;

  let isOpen  = false;
  let unread  = 0;
  let history = [];
  let typingEl = null;

  // Contexte système injecté dans Gemini
  const SYSTEM_PROMPT = `Tu es FactureCat 🐱🕶️, un assistant comptable félin sympathique et expert.
Tu réponds TOUJOURS en français, de façon concise, claire et avec des emojis félins.
Tu connais ces données :
FACTURES: ${{JSON.stringify(FACTURES)}}
NOTES DE FRAIS: ${{JSON.stringify(NOTES)}}
Utilise ces données pour répondre précisément aux questions chiffrées.`;

  history.push({{
    role: "user",
    parts: [{{ text: SYSTEM_PROMPT }}]
  }});
  history.push({{
    role: "model",
    parts: [{{ text: "Compris ! Je suis prêt à vous aider avec vos factures et notes de frais 🐾" }}]
  }});

  // ── Toggle fenêtre ──
  function toggleChat() {{
    const box = document.getElementById('chatbox');
    isOpen = !isOpen;
    if (isOpen) {{
      box.classList.add('open');
      setTimeout(() => box.classList.add('visible'), 10);
      unread = 0;
      updateBadge();
      scrollToBottom();
      setTimeout(() => document.getElementById('chat-input').focus(), 300);
    }} else {{
      box.classList.remove('visible');
      setTimeout(() => box.classList.remove('open'), 300);
    }}
  }}

  // ── Badge ──
  function updateBadge() {{
    const badge = document.getElementById('badge');
    if (unread > 0) {{
      badge.style.display = 'flex';
      badge.textContent = unread > 9 ? '9+' : unread;
    }} else {{
      badge.style.display = 'none';
    }}
  }}

  // ── Ajouter bulle ──
  function addBubble(text, role) {{
    const msgs = document.getElementById('chat-messages');
    const row  = document.createElement('div');
    row.className = `msg-row ${{role}}`;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = role === 'bot' ? '🐱' : '👤';

    const bubble = document.createElement('div');
    bubble.className = `bubble ${{role}}`;
    // Convertir **gras** basique
    bubble.innerHTML = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    if (role === 'bot') {{
      row.appendChild(avatar);
      row.appendChild(bubble);
    }} else {{
      row.appendChild(bubble);
      row.appendChild(avatar);
    }}

    msgs.appendChild(row);
    scrollToBottom();
  }}

  // ── Typing indicator ──
  function showTyping() {{
    const msgs = document.getElementById('chat-messages');
    const row  = document.createElement('div');
    row.className = 'msg-row bot';
    row.id = 'typing-row';
    row.innerHTML = `
      <div class="msg-avatar">🐱</div>
      <div class="bubble bot">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>`;
    msgs.appendChild(row);
    scrollToBottom();
  }}
  function hideTyping() {{
    const t = document.getElementById('typing-row');
    if (t) t.remove();
  }}

  // ── Scroll bas ──
  function scrollToBottom() {{
    const msgs = document.getElementById('chat-messages');
    setTimeout(() => {{ msgs.scrollTop = msgs.scrollHeight; }}, 50);
  }}

  // ── Réponses locales rapides ──
  function localAnswer(q) {{
    q = q.toLowerCase();

    if (FACTURES.length === 0 && NOTES.length === 0) {{
      if (q.includes('total') || q.includes('facture') || q.includes('note'))
        return "Aucune donnée chargée pour l'instant 🐱 Uploadez des factures ou ajoutez des notes de frais !";
    }}

    // Total TTC factures
    if ((q.includes('total') || q.includes('montant')) && !q.includes('note')) {{
      if (FACTURES.length > 0) {{
        const total = FACTURES.reduce((s, f) => {{
          const v = parseFloat(String(f.montant_ttc || f['Montant TTC (€)'] || 0).replace(',','.'));
          return s + (isNaN(v) ? 0 : v);
        }}, 0);
        return `💶 Total TTC de vos **${{FACTURES.length}} facture(s)** : **${{total.toFixed(2)}} €** 🐾`;
      }}
    }}

    // Nombre factures
    if (q.includes('combien') && (q.includes('facture') || q.includes('nombre'))) {{
      return `📄 Vous avez **${{FACTURES.length}} facture(s)** extraite(s) 🐱`;
    }}

    // Fournisseurs
    if (q.includes('fournisseur')) {{
      if (FACTURES.length > 0) {{
        const fours = [...new Set(FACTURES.map(f => f.fournisseur || f['Fournisseur'] || '?'))];
        return `🏢 Vos fournisseurs :\n${{fours.map(f => `• ${{f}}`).join('\n')}}`;
      }}
    }}

    // Notes de frais total
    if (q.includes('note') && (q.includes('total') || q.includes('montant') || q.includes('résume') || q.includes('resume'))) {{
      if (NOTES.length > 0) {{
        const total = NOTES.reduce((s, n) => {{
          const v = parseFloat(String(n.montant_ttc || n['Montant TTC (€)'] || 0).replace(',','.'));
          return s + (isNaN(v) ? 0 : v);
        }}, 0);
        return `💳 Vous avez **${{NOTES.length}} note(s) de frais** pour un total de **${{total.toFixed(2)}} €** TTC 🐾`;
      }}
    }}

    // Aide
    if (q.includes('aide') || q.includes('help') || q.includes('que sais')) {{
      return ("Je peux vous aider avec 🐾 :\n"
        + "• **Total TTC** → montant total de vos factures\n"
        + "• **Fournisseurs** → liste de vos fournisseurs\n"
        + "• **Combien** → nombre de factures\n"
        + "• **Notes de frais** → résumé de vos dépenses\n"
        + "• **En attente** → factures à vérifier\n"
        + "• Toute question sur vos données 😸");
    }}

    return null;
  }}

  // ── Appel Gemini ──
  async function callGemini(msg) {{
    try {{
      history.push({{ role:"user", parts:[{{ text: msg }}] }});
      const resp = await fetch(API_URL, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ contents: history }})
      }});
      const data = await resp.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text
                   || "Je n'arrive pas à répondre 🙀";
      history.push({{ role:"model", parts:[{{ text }}] }});
      return text;
    }} catch(e) {{
      return "Miaou... Erreur de connexion 🙀 Réessayez !";
    }}
  }}

  // ── Envoyer message ──
  async function sendMsg() {{
    const input = document.getElementById('chat-input');
    const msg   = input.value.trim();
    if (!msg) return;
    input.value = '';

    document.getElementById('suggestions').style.display = 'none';
    addBubble(msg, 'user');
    showTyping();

    await new Promise(r => setTimeout(r, 400));
    const local = localAnswer(msg);

    if (local) {{
      hideTyping();
      addBubble(local, 'bot');
    }} else {{
      const reponse = await callGemini(msg);
      hideTyping();
      addBubble(reponse, 'bot');
    }}

    if (!isOpen) {{ unread++; updateBadge(); }}
  }}

  // ── Suggestion chip ──
  function askSuggestion(text) {{
    document.getElementById('chat-input').value = text;
    sendMsg();
  }}

  // ── Effacer ──
  function clearChat() {{
    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = `
      <div class="msg-row bot">
        <div class="msg-avatar">🐱</div>
        <div class="bubble bot">
          Conversation effacée 🗑️ Comment puis-je vous aider ? 😸
        </div>
      </div>`;
    document.getElementById('suggestions').style.display = 'flex';
    history = history.slice(0, 2);
  }}
</script>
</body>
</html>
    """, height=0, scrolling=False)


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
    mois_choisi   = mois_list[now.month - 1]
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
            image  = images[0]
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

        genai.configure(api_key=api_key)
        model_ai = genai.GenerativeModel("gemini-2.5-flash")
        response = model_ai.generate_content([prompt, image])
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    if fichiers:
        ids_actuels = [f.name for f in fichiers]
        if "fichiers_ids" in st.session_state:
            anciens = st.session_state["fichiers_ids"]
            retires = [n for n in anciens if n not in ids_actuels]
            if retires:
                st.session_state["resultats"] = [
                    r for r in st.session_state.get("resultats", [])
                    if r.get("fichier") not in retires
                ]

        col_ext1, col_ext2, col_ext3 = st.columns([1, 2, 1])
        with col_ext2:
            if st.button("🚀 Extraire les données", use_container_width=True):
                if "resultats" not in st.session_state:
                    st.session_state["resultats"] = []

                progress = st.progress(0, text="🐱 FactureCat analyse vos factures...")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                deja_extraits = [r.get("fichier","") for r in st.session_state["resultats"]]

                for i, fichier in enumerate(fichiers):
                    if fichier.name not in deja_extraits:
                        try:
                            data = extraire_facture(fichier, model, mois_choisi, annee_choisie)
                            data["fichier"] = fichier.name
                            data["statut"]  = "À vérifier 🐱"
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
                st.session_state["mois"]  = mois_choisi
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

        # Tableau stylé header
        st.markdown("""
        <div style="
            background:white; border-radius:20px;
            box-shadow:0 4px 20px rgba(200,149,108,0.15);
            border:2px solid #f0d5c0; overflow:hidden; margin-bottom:0.5rem;
        ">
            <div style="
                background:linear-gradient(135deg,#f0a070,#e8856a);
                padding:0.8rem 1.5rem;
            ">
                <span style="color:white;font-weight:800;font-size:1rem;">
                    📋 Factures extraites — cliquez pour modifier
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
                "Montant HT (€)":  st.column_config.NumberColumn("Montant HT (€)",  format="%.2f €"),
                "TVA (€)":         st.column_config.NumberColumn("TVA (€)",          format="%.2f €"),
                "Montant TTC (€)": st.column_config.NumberColumn("Montant TTC (€)",  format="%.2f €"),
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

        # KPIs
        st.markdown("---")
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        try:
            total_ttc = sum(
                float(str(r.get("montant_ttc","0") or "0").replace(",","."))
                for r in resultats
            )
            total_ht  = sum(
                float(str(r.get("montant_ht","0") or "0").replace(",","."))
                for r in resultats
            )
            total_tva = sum(
                float(str(r.get("tva","0") or "0").replace(",","."))
                for r in resultats
            )
        except:
            total_ttc = total_ht = total_tva = 0.0

        nb_valides   = sum(1 for r in resultats if "Validé"    in str(r.get("statut","")))
        nb_attente   = sum(1 for r in resultats if "vérifier"  in str(r.get("statut","")))
        nb_erreurs   = sum(1 for r in resultats if "Erreur"    in str(r.get("statut","")))

        for col, label, val, color in [
            (col_k1, "💶 Total TTC",    f"{total_ttc:.2f} €", "#a0522d"),
            (col_k2, "📊 Total HT",     f"{total_ht:.2f} €",  "#c8956c"),
            (col_k3, "🧾 TVA totale",   f"{total_tva:.2f} €", "#d4a882"),
            (col_k4, "📄 Nb factures",  str(len(resultats)),  "#a0522d"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <p style="color:#c8956c;font-size:0.85rem;margin:0;">{label}</p>
                    <div style="font-size:1.6rem;font-weight:800;color:{color};">{val}</div>
                </div>""", unsafe_allow_html=True)

        col_s1, col_s2, col_s3 = st.columns(3)
        for col, nb, label, color in [
            (col_s1, nb_valides, "Validées",    "#2d5a2d"),
            (col_s2, nb_attente, "À vérifier",  "#a0522d"),
            (col_s3, nb_erreurs, "Erreurs",      "#8b0000"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card-green" style="text-align:center;">
                    <div style="font-size:1.4rem;font-weight:800;color:{color};">{nb}</div>
                    <div style="color:{color};">{label}</div>
                </div>""", unsafe_allow_html=True)

        # Visualisation PDF
        if fichiers:
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

        # Export Excel
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
else:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:4rem;">💳</div>
        <h1 style="margin:0;">Notes de Frais</h1>
        <p style="color:#c8956c;margin:0.5rem 0 0 0;font-size:1.1rem;">
            Gérez vos dépenses professionnelles 🐾
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    with st.form("form_note_frais", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nf_date           = st.date_input("📅 Date", value=datetime.now())
            nf_employe        = st.text_input("👤 Employé")
            nf_categorie      = st.selectbox("📂 Catégorie",
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
                st.error("❌ Veuillez renseigner l'employé !")
            elif nf_montant_ht <= 0:
                st.error("❌ Montant HT doit être supérieur à 0 !")
            else:
                note = {
                    "date":            nf_date.strftime("%d/%m/%Y"),
                    "employe":         nf_employe,
                    "categorie":       nf_categorie,
                    "description":     nf_description,
                    "montant_ht":      nf_montant_ht,
                    "tva_pct":         nf_tva,
                    "montant_tva":     nf_montant_tva,
                    "montant_ttc":     nf_montant_ttc,
                    "moyen_paiement":  nf_moyen_paiement,
                    "justificatif":    nf_justificatif.name if nf_justificatif else "",
                    "statut":          "À valider 🐱"
                }
                st.session_state["notes_frais"].append(note)
                st.success("✅ Dépense ajoutée ! 🐾")
                st.rerun()

    # Tableau notes de frais
    if st.session_state["notes_frais"]:
        notes = st.session_state["notes_frais"]

        # KPIs
        total_nf = sum(float(str(n.get("montant_ttc",0)).replace(",",".")) for n in notes)
        col_nf1, col_nf2, col_nf3 = st.columns(3)
        with col_nf1:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <p style="color:#c8956c;font-size:0.85rem;margin:0;">💶 Total TTC</p>
                <div style="font-size:1.6rem;font-weight:800;color:#a0522d;">{total_nf:.2f} €</div>
            </div>""", unsafe_allow_html=True)
        with col_nf2:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <p style="color:#c8956c;font-size:0.85rem;margin:0;">📝 Nb dépenses</p>
                <div style="font-size:1.6rem;font-weight:800;color:#a0522d;">{len(notes)}</div>
            </div>""", unsafe_allow_html=True)
        with col_nf3:
            cats = list(set(n.get("categorie","") for n in notes))
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <p style="color:#c8956c;font-size:0.85rem;margin:0;">📂 Catégories</p>
                <div style="font-size:1.6rem;font-weight:800;color:#a0522d;">{len(cats)}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="
            background:white; border-radius:20px;
            box-shadow:0 4px 20px rgba(200,149,108,0.15);
            border:2px solid #f0d5c0; overflow:hidden; margin-bottom:0.5rem;
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

        df_nf = pd.DataFrame(notes)
        df_nf = df_nf.rename(columns={
            "date":"Date","employe":"Employé","categorie":"Catégorie",
            "description":"Description","montant_ht":"Montant HT (€)",
            "tva_pct":"TVA (%)","montant_tva":"TVA (€)","montant_ttc":"Montant TTC (€)",
            "moyen_paiement":"Moyen de paiement","justificatif":"Justificatif","statut":"Statut"
        })

        df_nf_edit = st.data_editor(
            df_nf, use_container_width=True, hide_index=True,
            column_config={
                "Statut": st.column_config.SelectboxColumn(
                    "Statut 🏷️",
                    options=["Validé 😸","À valider 🐱","Refusé 🙀","En attente 😺"]
                ),
                "Catégorie": st.column_config.SelectboxColumn(
                    "Catégorie 📂",
                    options=["Transport","Repas","Hébergement","Fournitures","Services","Autres"]
                ),
                "Montant HT (€)":  st.column_config.NumberColumn("Montant HT (€)",  format="%.2f €"),
                "TVA (€)":         st.column_config.NumberColumn("TVA (€)",          format="%.2f €"),
                "Montant TTC (€)": st.column_config.NumberColumn("Montant TTC (€)",  format="%.2f €"),
            },
            key="editor_notes"
        )

        # Export
        st.markdown("---")
        col_act1, col_act2, col_act3 = st.columns(3)
        buffer_nf = io.BytesIO()
        df_nf_edit.to_excel(buffer_nf, index=False, engine="openpyxl")
        buffer_nf.seek(0)
        with col_act1:
            st.download_button(
                "📥 Télécharger Excel",
                data=buffer_nf,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_act2:
            st.download_button(
                "📄 Télécharger CSV",
                data=df_nf_edit.to_csv(index=False).encode("utf-8"),
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_act3:
            if st.button("🗑️ Effacer tout", use_container_width=True):
                st.session_state["notes_frais"] = []
                st.rerun()

    else:
        st.markdown("""
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
# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:1rem 0;">
    <p style="font-weight:900;color:#a0522d;font-size:1rem;">
        🐱 FactureCat — Votre assistant comptable félin 🐾
    </p>
    <p style="color:#d4a882;font-size:0.75rem;">
        Propulsé par Gemini AI ✨
    </p>
</div>
""", unsafe_allow_html=True)

# ─── CHATBOT FLOTTANT ─────────────────────────────────────────────────────────
factures_ctx   = st.session_state.get("resultats", [])
notes_ctx      = st.session_state.get("notes_frais", [])
render_chat_widget(notes_frais_data=notes_ctx, factures_data=factures_ctx)

