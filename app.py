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

# CONFIG GEMINI
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def pdf_to_image(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    mat  = fitz.Matrix(2,2)
    pix  = page.get_pixmap(matrix=mat)
    return Image.open(io.BytesIO(pix.tobytes("png")))

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
        txt  = resp.text.strip()
        txt  = txt.replace("```json","").replace("```","").strip()
        return json.loads(txt)
    except Exception as e:
        st.error(f"Erreur analyse : {e}")
        return None

def render_chat_widget(notes_frais_data=None):
    notes_json = json.dumps(notes_frais_data or [])
    html = f"""
    <style>
    #fab{{
        position:fixed;bottom:2rem;right:2rem;width:60px;height:60px;
        border-radius:50%;background:linear-gradient(135deg,#f0a070,#e07040);
        border:none;cursor:pointer;font-size:1.8rem;
        box-shadow:0 4px 20px rgba(240,112,64,0.4);
        z-index:9999;transition:transform .2s;display:flex;
        align-items:center;justify-content:center;
    }}
    #fab:hover{{transform:scale(1.1);}}
    #chatbox{{
        position:fixed;bottom:5.5rem;right:2rem;width:340px;
        background:white;border-radius:20px;
        box-shadow:0 10px 40px rgba(0,0,0,0.15);
        z-index:9998;display:none;flex-direction:column;
        max-height:480px;overflow:hidden;
        border:1px solid rgba(240,160,112,0.3);
    }}
    #chat-header{{
        background:linear-gradient(135deg,#f0a070,#e07040);
        padding:1rem 1.2rem;border-radius:20px 20px 0 0;
        color:white;font-weight:800;font-size:1rem;
        display:flex;align-items:center;gap:0.5rem;
    }}
    #chat-messages{{
        flex:1;overflow-y:auto;padding:1rem;
        display:flex;flex-direction:column;gap:0.7rem;
        max-height:300px;
    }}
    .msg-bot{{
        background:#fff8f0;border-radius:12px 12px 12px 0;
        padding:0.7rem 1rem;font-size:0.85rem;color:#a0522d;
        border:1px solid rgba(240,160,112,0.2);max-width:85%;
    }}
    .msg-user{{
        background:linear-gradient(135deg,#f0a070,#e07040);
        border-radius:12px 12px 0 12px;
        padding:0.7rem 1rem;font-size:0.85rem;color:white;
        max-width:85%;align-self:flex-end;
    }}
    #chat-input-area{{
        padding:0.8rem;border-top:1px solid rgba(240,160,112,0.2);
        display:flex;gap:0.5rem;
    }}
    #chat-input{{
        flex:1;border:1px solid rgba(240,160,112,0.4);
        border-radius:20px;padding:0.5rem 1rem;
        font-size:0.85rem;outline:none;
        font-family:inherit;
    }}
    #chat-send{{
        background:linear-gradient(135deg,#f0a070,#e07040);
        border:none;border-radius:50%;width:36px;height:36px;
        cursor:pointer;color:white;font-size:1rem;
        display:flex;align-items:center;justify-content:center;
    }}
    </style>
    <button id="fab" onclick="toggleChat()">🐱</button>
    <div id="chatbox">
        <div id="chat-header">😻 FactureCat Assistant</div>
        <div id="chat-messages">
            <div class="msg-bot">Miaou ! 🐾 Je suis FactureCat, ton assistant comptable félin ! Comment puis-je t'aider ?</div>
        </div>
        <div id="chat-input-area">
            <input id="chat-input" placeholder="Pose une question..." onkeypress="if(event.key==='Enter')sendMsg()"/>
            <button id="chat-send" onclick="sendMsg()">➤</button>
        </div>
    </div>

    <script>
    const notesData = {notes_json};

    function toggleChat(){{
        const box = document.getElementById('chatbox');
        box.style.display = box.style.display === 'flex' ? 'none' : 'flex';
    }}

    function addMsg(text, type){{
        const msgs = document.getElementById('chat-messages');
        const d = document.createElement('div');
        d.className = type === 'user' ? 'msg-user' : 'msg-bot';
        d.innerHTML = text;
        msgs.appendChild(d);
        msgs.scrollTop = msgs.scrollHeight;
    }}

    function sendMsg(){{
        const inp = document.getElementById('chat-input');
        const txt = inp.value.trim();
        if(!txt) return;
        addMsg(txt, 'user');
        inp.value = '';
        setTimeout(() => addMsg(getReply(txt), 'bot'), 400);
    }}

    function getReply(msg){{
        const m = msg.toLowerCase();

        if(m.includes('total') || m.includes('combien') || m.includes('dépense')){{
            if(notesData.length === 0) return "Aucune dépense enregistrée pour le moment 🐱";
            const total = notesData.reduce((s,n) => s + (parseFloat(n.montant)||0), 0);
            return `💰 Total de tes dépenses : <b>${{total.toFixed(2)}} €</b> pour ${{notesData.length}} entrée(s) 🐾`;
        }}

        if(m.includes('catégor') || m.includes('categor')){{
            if(notesData.length === 0) return "Aucune dépense enregistrée 🐱";
            const cats = {{}};
            notesData.forEach(n => {{
                const c = n.categorie || 'Autre';
                cats[c] = (cats[c]||0) + (parseFloat(n.montant)||0);
            }});
            const lines = Object.entries(cats).map(([c,v]) => `• ${{c}}: ${{v.toFixed(2)}} €`).join('<br>');
            return `📂 Répartition par catégorie :<br>${{lines}}`;
        }}

        if(m.includes('plus') && (m.includes('gros') || m.includes('élevé') || m.includes('grand'))){{
            if(notesData.length === 0) return "Aucune dépense enregistrée 🐱";
            const max = notesData.reduce((a,b) => (parseFloat(a.montant)||0) > (parseFloat(b.montant)||0) ? a : b);
            return `🏆 La plus grosse dépense : <b>${{max.description||max.categorie}}</b> à <b>${{parseFloat(max.montant).toFixed(2)}} €</b> 🐾`;
        }}

        if(m.includes('aide') || m.includes('help') || m.includes('commande')){{
            return `🐱 Voici ce que je sais faire :<br>
            • <b>total</b> — voir le total des dépenses<br>
            • <b>catégories</b> — répartition par catégorie<br>
            • <b>plus grosse</b> — la dépense la plus élevée<br>
            • <b>combien</b> — nombre de dépenses`;
        }}

        const replies = [
            "Miaou ! 🐱 Je ne comprends pas encore cette question. Tape <b>aide</b> pour voir ce que je sais faire !",
            "Purrrr... 🐾 Essaie de me demander le <b>total</b> ou les <b>catégories</b> !",
            "🐱 Je suis encore en train d'apprendre ! Tape <b>aide</b> pour les commandes disponibles."
        ];
        return replies[Math.floor(Math.random()*replies.length)];
    }}
    </script>
    """
    components.html(html, height=0)

# CSS GLOBAL
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
* { font-family: 'Nunito', sans-serif !important; }
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #fdf6f0 0%, #fdebd0 50%, #fdf6f0 100%);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }
.nav-container {
    display: flex; justify-content: center; align-items: center;
    gap: 1rem; padding: 1.5rem 0 1rem 0; margin-bottom: 1rem;
}
.nav-title { font-size: 2rem; font-weight: 900; color: #a0522d; margin-right: 2rem; white-space: nowrap; }
.section-title {
    font-size: 0.95rem; font-weight: 800; color: #a0522d;
    margin: 1rem 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em;
}
.upload-zone {
    border: 2px dashed rgba(240,160,112,0.5); border-radius: 16px;
    padding: 2rem; text-align: center; background: rgba(255,255,255,0.6); margin: 0.5rem 0;
}
.file-card {
    background: white; border-radius: 12px; padding: 0.6rem 1rem; margin: 0.4rem 0;
    border: 1px solid rgba(240,160,112,0.25); display: flex; align-items: center;
    gap: 0.5rem; font-size: 0.82rem; color: #a0522d; font-weight: 700;
    box-shadow: 0 2px 8px rgba(240,112,64,0.06);
}
.metric-card {
    background: white; border-radius: 14px; padding: 0.8rem 1rem; margin: 0.4rem 0;
    border: 1px solid rgba(240,160,112,0.2); box-shadow: 0 2px 12px rgba(240,112,64,0.07); text-align: center;
}
.metric-value { font-size: 1.3rem; font-weight: 900; color: #a0522d; }
.metric-label { font-size: 0.72rem; color: #c8956c; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.cat-container { display: flex; align-items: flex-start; gap: 0.8rem; padding: 1rem 0; }
.cat-avatar { font-size: 2.2rem; flex-shrink: 0; }
.cat-bubble {
    background: white; border-radius: 0 16px 16px 16px; padding: 0.9rem 1.2rem;
    border: 1px solid rgba(240,160,112,0.25); box-shadow: 0 2px 12px rgba(240,112,64,0.07); flex: 1;
}
.cat-bubble-title { font-weight: 800; color: #a0522d; font-size: 0.95rem; margin-bottom: 0.2rem; }
.cat-bubble-sub { color: #c8956c; font-size: 0.82rem; }
.info-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.5rem 0; border-bottom: 1px solid rgba(240,160,112,0.1); font-size: 0.85rem;
}
.info-label { color: #c8956c; font-weight: 700; }
.info-value { color: #a0522d; font-weight: 800; }
.stButton > button {
    background: linear-gradient(135deg, #f0a070, #e07040) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-weight: 800 !important; font-size: 0.88rem !important; padding: 0.6rem 1.2rem !important;
    transition: all 0.2s !important; box-shadow: 0 3px 10px rgba(240,112,64,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important; box-shadow: 0 5px 15px rgba(240,112,64,0.35) !important;
}
.dash-card {
    background: white; border-radius: 18px; padding: 1.5rem;
    border: 1px solid rgba(240,160,112,0.2); box-shadow: 0 4px 20px rgba(240,112,64,0.08);
    text-align: center; margin: 0.3rem 0;
}
.dash-card-icon { font-size: 2.2rem; margin-bottom: 0.5rem; }
.dash-card-value { font-size: 1.8rem; font-weight: 900; color: #a0522d; }
.dash-card-label { font-size: 0.78rem; color: #c8956c; font-weight: 700; text-transform: uppercase; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
[data-testid="stFileUploader"] > div { border-radius: 12px !important; }
.stSelectbox > div > div { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# SESSION STATE
for k,v in [
    ("factures",[]),
    ("page","Factures"),
    ("notes_frais",[]),
    ("uploaded_files_data",{}),
    ("pending_files",[]),
    ("selected_preview",None),
    ("extraction_done", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# NAVIGATION
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
c0,c1,c2,c3,c4 = st.columns([2,1,1,1,2])
with c0:
    st.markdown('<span class="nav-title">🐱 FactureCat</span>', unsafe_allow_html=True)
with c1:
    if st.button("📄 Factures", use_container_width=True, key="nav_fac"):
        st.session_state["page"] = "Factures"
        st.rerun()
with c2:
    if st.button("🔥 Notes de frais", use_container_width=True, key="nav_notes"):
        st.session_state["page"] = "Notes"
        st.rerun()
with c3:
    if st.button("🚪 Déco", use_container_width=True, key="nav_deco"):
        st.session_state["authenticated"] = False
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# PAGE FACTURES
# ─────────────────────────────────────────
if st.session_state["page"] == "Factures":

    col_left, col_center, col_metrics = st.columns([1.2, 2, 1.2])

    with col_left:
        st.markdown('<div class="section-title">📤 Import</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Déposez vos factures",
            type=["pdf","png","jpg","jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded:
            for f in uploaded:
                if f.name not in st.session_state["uploaded_files_data"]:
                    st.session_state["uploaded_files_data"][f.name] = {
                        "bytes": f.read(),
                        "type":  f.type
                    }
                if f.name not in st.session_state["pending_files"]:
                    st.session_state["pending_files"].append(f.name)

        if st.session_state["pending_files"]:
            st.markdown('<div class="section-title">📋 Fichiers</div>', unsafe_allow_html=True)
            for fname in st.session_state["pending_files"]:
                ext  = fname.split(".")[-1].upper()
                icon = "📄" if ext == "PDF" else "🖼️"
                st.markdown(f'<div class="file-card">{icon} {fname}</div>', unsafe_allow_html=True)

            if st.button("🐾 Lancer l'extraction !", use_container_width=True, key="btn_run"):
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
                st.session_state["pending_files"]   = []
                st.session_state["extraction_done"] = True
                st.rerun()

        if st.session_state["factures"]:
            st.markdown("---")
            st.markdown('<div class="section-title">🔍 Aperçu</div>', unsafe_allow_html=True)
            fnames = [f["filename"] for f in st.session_state["factures"]]
            sel = st.selectbox("Choisir une facture", fnames, label_visibility="collapsed")
            if sel:
                st.session_state["selected_preview"] = sel

            st.markdown("---")
            st.markdown('<div class="section-title">💾 Exports</div>', unsafe_allow_html=True)
            df_exp = pd.DataFrame(st.session_state["factures"])
            c1e, c2e = st.columns(2)
            with c1e:
                buf = io.BytesIO()
                df_exp.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button("📥 Excel", data=buf,
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with c2e:
                st.download_button("📄 CSV",
                    data=df_exp.to_csv(index=False).encode("utf-8"),
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True)

            if st.button("🗑️ Tout effacer", use_container_width=True, key="clear_fac"):
                st.session_state["factures"]           = []
                st.session_state["uploaded_files_data"] = {}
                st.session_state["pending_files"]       = []
                st.session_state["selected_preview"]    = None
                st.session_state["extraction_done"]     = False
                st.rerun()

    with col_center:
        if st.session_state.get("extraction_done") and st.session_state["factures"]:
            st.markdown("""
            <div class="cat-container">
                <div class="cat-avatar">😻</div>
                <div class="cat-bubble">
                    <div class="cat-bubble-title">Purrrfect ! Voici ce que j'ai trouvé 🐾</div>
                    <div class="cat-bubble-sub">Vous pouvez modifier directement dans le tableau !</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state["factures"]:
            df = pd.DataFrame(st.session_state["factures"])
            cols_order = ["filename","fournisseur","date","numero_facture",
                          "montant_ht","tva","montant_ttc","categorie","description","statut"]
            df = df.reindex(columns=[c for c in cols_order if c in df.columns])

            edited = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "filename":       st.column_config.TextColumn("📄 Fichier"),
                    "fournisseur":    st.column_config.TextColumn("🏢 Fournisseur"),
                    "date":           st.column_config.TextColumn("📅 Date"),
                    "numero_facture": st.column_config.TextColumn("🔢 N° Facture"),
                    "montant_ht":     st.column_config.NumberColumn("💶 HT", format="%.2f"),
                    "tva":            st.column_config.NumberColumn("📊 TVA", format="%.2f"),
                    "montant_ttc":    st.column_config.NumberColumn("💰 TTC", format="%.2f"),
                    "categorie":      st.column_config.TextColumn("📂 Catégorie"),
                    "description":    st.column_config.TextColumn("📝 Description"),
                    "statut":         st.column_config.SelectboxColumn(
                        "🔖 Statut",
                        options=["En attente","Validé","Payé","Annulé"]
                    ),
                },
                key="editor_factures"
            )
            st.session_state["factures"] = edited.to_dict("records")
        else:
            st.markdown("""
            <div style="text-align:center;padding:5rem 0;">
                <div style="font-size:5rem;">🐱</div>
                <p style="font-size:1.2rem;font-weight:800;color:#a0522d;margin-top:1rem;">
                    Prêt à analyser vos factures !
                </p>
                <p style="color:#c8956c;">Importez un fichier à gauche puis lancez l'extraction 🐾</p>
            </div>
            """, unsafe_allow_html=True)

    with col_metrics:
        st.markdown('<div class="section-title">📊 Métriques</div>', unsafe_allow_html=True)

        fac_sel = next(
            (f for f in st.session_state["factures"]
             if f.get("filename") == st.session_state.get("selected_preview")),
            None
        )

        if fac_sel:
            ttc_sel = fac_sel.get("montant_ttc", 0) or 0
            ht_sel  = fac_sel.get("montant_ht",  0) or 0
            tva_sel = fac_sel.get("tva",         0) or 0

            st.markdown("""
            <div style="background:rgba(240,160,112,0.1);border-radius:12px;
                        padding:0.4rem 0.8rem;margin-bottom:0.8rem;
                        border:1px solid rgba(240,160,112,0.3);">
                <span style="font-size:0.72rem;color:#c8956c;font-weight:800;">
                    📄 Facture sélectionnée
                </span>
            </div>
            """, unsafe_allow_html=True)

            for val, lbl in [
                (f"{ttc_sel:.2f} €", "TTC 🔥"),
                (f"{ht_sel:.2f} €",  "HT 📊"),
                (f"{tva_sel:.2f} €", "TVA 🧾"),
                (fac_sel.get("fournisseur","—"), "Fournisseur 🏢"),
                (fac_sel.get("date","—"),        "Date 📅"),
                (fac_sel.get("categorie","—"),   "Catégorie 📂"),
            ]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size:1.1rem;">{val}</div>
                    <div class="metric-label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        if st.session_state["factures"]:
            st.markdown("---")
            df_all = pd.DataFrame(st.session_state["factures"])
            total_ttc = df_all["montant_ttc"].sum() if "montant_ttc" in df_all else 0
            total_ht  = df_all["montant_ht"].sum()  if "montant_ht"  in df_all else 0
            nb_fac    = len(df_all)

            for val, lbl in [
                (f"{total_ttc:.2f} €", "Total TTC 💰"),
                (f"{total_ht:.2f} €",  "Total HT 📊"),
                (str(nb_fac),          "Factures 📄"),
            ]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# PAGE NOTES DE FRAIS
# ─────────────────────────────────────────
elif st.session_state["page"] == "Notes":

    col_left2, col_right2 = st.columns([1.2, 2.8])

    with col_left2:
        st.markdown('<div class="section-title">➕ Nouvelle dépense</div>', unsafe_allow_html=True)

        with st.form("form_note", clear_on_submit=True):
            desc   = st.text_input("📝 Description")
            mont   = st.number_input("💶 Montant (€)", min_value=0.0, step=0.01)
            cat    = st.selectbox("📂 Catégorie", [
                "Repas","Transport","Hébergement","Matériel",
                "Formation","Communication","Autre"
            ])
            date_n = st.date_input("📅 Date", value=datetime.today())
            just   = st.file_uploader("📎 Justificatif", type=["pdf","png","jpg","jpeg"])
            submit = st.form_submit_button("✅ Ajouter", use_container_width=True)

            if submit and desc and mont > 0:
                st.session_state["notes_frais"].append({
                    "description": desc,
                    "montant":     mont,
                    "categorie":   cat,
                    "date":        date_n.strftime("%d/%m/%Y"),
                    "justificatif": just.name if just else "—",
                    "statut":      "En attente",
                })
                st.success("✅ Dépense ajoutée !")
                st.rerun()

        if st.session_state["notes_frais"]:
            st.markdown("---")
            st.markdown('<div class="section-title">📊 Stats</div>', unsafe_allow_html=True)
            df_stats = pd.DataFrame(st.session_state["notes_frais"])
            total_n  = df_stats["montant"].sum()
            nb_n     = len(df_stats)

            for val, lbl in [
                (f"{total_n:.2f} €", "Total 💰"),
                (str(nb_n),          "Dépenses 📄"),
            ]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

    with col_right2:
        st.markdown('<div class="section-title">📋 Mes dépenses</div>', unsafe_allow_html=True)

        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])

            edited_nf = st.data_editor(
                df_nf,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "description":  st.column_config.TextColumn("📝 Description"),
                    "montant":      st.column_config.NumberColumn("💶 Montant", format="%.2f"),
                    "categorie":    st.column_config.TextColumn("📂 Catégorie"),
                    "date":         st.column_config.TextColumn("📅 Date"),
                    "justificatif": st.column_config.TextColumn("📎 Justificatif"),
                    "statut":       st.column_config.SelectboxColumn(
                        "🔖 Statut",
                        options=["En attente","Validé","Remboursé","Refusé"]
                    ),
                },
                key="editor_notes"
            )
            st.session_state["notes_frais"] = edited_nf.to_dict("records")

            st.markdown("---")
            st.markdown('<div class="section-title">💾 Exports</div>', unsafe_allow_html=True)
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                buf = io.BytesIO()
                df_nf.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button("📥 Excel", data=buf,
                    file_name=f"notes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with ce2:
                st.download_button("📄 CSV",
                    data=df_nf.to_csv(index=False).encode("utf-8"),
                    file_name=f"notes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True)
            with ce3:
                if st.button("🗑️ Effacer", use_container_width=True, key="clear_notes"):
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

# Chat flottant
render_chat_widget(st.session_state.get("notes_frais", []))
