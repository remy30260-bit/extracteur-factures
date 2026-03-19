import streamlit as st
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
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Mot de passe", type="password")

        if mode == "🔑 Se connecter":
            if st.button("🐾 Se connecter", use_container_width=True):
                try:
                    supabase = get_supabase()
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
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
                    st.session_state["user_email"] = email
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

[data-testid="stSidebar"] { display: none; }
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
.chat-user {
    background: linear-gradient(135deg, #f0a070, #c8956c);
    color: white;
    border-radius: 16px 16px 4px 16px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-weight: 600;
}
.chat-bot {
    background: white;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px 16px 16px 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
}
.cat-ascii {
    font-family: monospace !important;
    font-size: 0.7rem !important;
    line-height: 1.3 !important;
    color: #a0522d;
}
.preview-box {
    background: white;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px;
    padding: 1rem;
    height: 100%;
}
.info-box {
    background: white;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px;
    padding: 1rem;
    height: 100%;
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
    <div style="display:flex; align-items:center; gap:1.5rem;">
        <span style="color:#f5e6d8; font-size:0.85rem;">🐾 {user_email}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── NAVIGATION ───────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "📄 Factures"

col_n1, col_n2, col_n3, col_n4 = st.columns([1, 2, 2, 1])
with col_n2:
    if st.button("📄 Factures", use_container_width=True,
                 type="primary" if st.session_state["page"] == "📄 Factures" else "secondary"):
        st.session_state["page"] = "📄 Factures"
        st.rerun()
with col_n3:
    if st.button("💰 Notes de frais", use_container_width=True,
                 type="primary" if st.session_state["page"] == "💰 Notes de frais" else "secondary"):
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

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def analyze_invoice(file_bytes, file_type, filename=""):
    prompt = """Tu es FactureCat 🐱, un expert comptable félin. Analyse cette facture et extrais ces informations en JSON strict :
{
  "fournisseur": "nom du fournisseur",
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
Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

    try:
        if file_type == "application/pdf":
            images = extract_pdf_images(file_bytes)
            if not images:
                return None
            img_bytes = image_to_bytes(images[0])
            response = model.generate_content([
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

# ════════════════════════════════════════════════════════════════════════════
# PAGE FACTURES
# ════════════════════════════════════════════════════════════════════════════
if page == "📄 Factures":

    if "factures" not in st.session_state:
        st.session_state["factures"] = []
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "uploaded_files_data" not in st.session_state:
        st.session_state["uploaded_files_data"] = {}
    if "selected_rows" not in st.session_state:
        st.session_state["selected_rows"] = {}
    if "selected_preview" not in st.session_state:
        st.session_state["selected_preview"] = None

    # ── ZONE UPLOAD (pleine largeur) ─────────────────────────────────────────
    st.markdown('<div class="section-title">📤 Importer des factures</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Glissez vos factures ici",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            already = any(f.get("filename") == uploaded_file.name
                          for f in st.session_state["factures"])
            if not already:
                with st.spinner(f"🐱 Analyse de {uploaded_file.name}..."):
                    file_bytes = uploaded_file.read()
                    st.session_state["uploaded_files_data"][uploaded_file.name] = {
                        "bytes": file_bytes,
                        "type": uploaded_file.type
                    }
                    result = analyze_invoice(file_bytes, uploaded_file.type, uploaded_file.name)
                    if result:
                        result["filename"] = uploaded_file.name
                        result["id"] = len(st.session_state["factures"])
                        st.session_state["factures"].append(result)
                        # Auto-sélection de la dernière facture importée
                        st.session_state["selected_preview"] = uploaded_file.name
                        st.success(f"✅ {uploaded_file.name} analysée ! 🐾")
                    else:
                        st.error(f"❌ Échec pour {uploaded_file.name}")
            else:
                if uploaded_file.name not in st.session_state["uploaded_files_data"]:
                    file_bytes = uploaded_file.read()
                    st.session_state["uploaded_files_data"][uploaded_file.name] = {
                        "bytes": file_bytes,
                        "type": uploaded_file.type
                    }

    st.markdown("---")

    # ── ZONE PRINCIPALE : 3 colonnes ─────────────────────────────────────────
    # col_prev = prévisualisation | col_info = données facture | col_metrics = métriques
    if st.session_state["factures"]:

        col_prev, col_info, col_metrics = st.columns([1.2, 1.2, 1], gap="medium")

        # ────────────────────────────────────────────────────────────────────
        # COLONNE 1 : Prévisualisation
        # ────────────────────────────────────────────────────────────────────
        with col_prev:
            st.markdown('<div class="section-title">👁️ Prévisualisation</div>', unsafe_allow_html=True)

            filenames = list(st.session_state["uploaded_files_data"].keys())

            if st.session_state["selected_preview"] not in filenames and filenames:
                st.session_state["selected_preview"] = filenames[0]

            selected_file = st.selectbox(
                "Facture",
                filenames,
                index=filenames.index(st.session_state["selected_preview"])
                      if st.session_state["selected_preview"] in filenames else 0,
                label_visibility="collapsed",
                key="preview_select"
            )

            if selected_file != st.session_state["selected_preview"]:
                st.session_state["selected_preview"] = selected_file
                st.rerun()

            if selected_file:
                file_data = st.session_state["uploaded_files_data"][selected_file]
                file_bytes = file_data["bytes"]
                file_type  = file_data["type"]

                with st.container():
                    st.markdown(f"<p style='color:#c8956c; font-size:0.8rem;'>📄 {selected_file}</p>",
                                unsafe_allow_html=True)

                    if file_type == "application/pdf":
                        try:
                            images = extract_pdf_images(file_bytes)
                            if images:
                                for i, img in enumerate(images):
                                    if len(images) > 1:
                                        st.caption(f"Page {i+1}/{len(images)}")
                                    st.image(img, use_container_width=True)
                        except Exception as e:
                            st.error(f"❌ Erreur PDF : {e}")
                    else:
                        try:
                            img = Image.open(io.BytesIO(file_bytes))
                            st.image(img, use_container_width=True)
                        except Exception as e:
                            st.error(f"❌ Erreur image : {e}")

                    st.download_button(
                        label="📥 Télécharger",
                        data=file_bytes,
                        file_name=selected_file,
                        mime=file_type,
                        use_container_width=True,
                        key="dl_preview"
                    )

        # ────────────────────────────────────────────────────────────────────
        # COLONNE 2 : Données extraites de la facture sélectionnée
        # ────────────────────────────────────────────────────────────────────
        with col_info:
            st.markdown('<div class="section-title">🧾 Données extraites</div>', unsafe_allow_html=True)

            # Trouver la facture correspondante
            facture_selectionnee = None
            for f in st.session_state["factures"]:
                if f.get("filename") == st.session_state["selected_preview"]:
                    facture_selectionnee = f
                    break

            if facture_selectionnee:
                # Affichage des infos clés
                champs = [
                    ("🏢 Fournisseur",    facture_selectionnee.get("fournisseur", "—")),
                    ("📅 Date",           facture_selectionnee.get("date", "—")),
                    ("🔢 N° Facture",     facture_selectionnee.get("numero_facture", "—")),
                    ("💶 Montant HT",     f"{facture_selectionnee.get('montant_ht', 0):.2f} €"),
                    ("📊 TVA",            f"{facture_selectionnee.get('tva', 0):.2f} €"),
                    ("💰 Montant TTC",    f"{facture_selectionnee.get('montant_ttc', 0):.2f} €"),
                    ("💱 Devise",         facture_selectionnee.get("devise", "EUR")),
                    ("📂 Catégorie",      facture_selectionnee.get("categorie", "—")),
                    ("📋 Description",    facture_selectionnee.get("description", "—")),
                    ("✅ Statut",         facture_selectionnee.get("statut", "—")),
                ]

                for label, valeur in champs:
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                padding:0.5rem 0.8rem; margin-bottom:0.4rem;
                                background:white; border-radius:10px;
                                border:1px solid rgba(200,149,108,0.2);">
                        <span style="color:#c8956c; font-size:0.82rem; font-weight:700;">{label}</span>
                        <span style="color:#a0522d; font-size:0.85rem; font-weight:800;
                                     max-width:55%; text-align:right;">{valeur}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Sélectionnez une facture pour voir ses données 🐾")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Tableau complet (toutes les factures) ──
            st.markdown('<div class="section-title">📋 Toutes les factures</div>', unsafe_allow_html=True)

            df = pd.DataFrame(st.session_state["factures"])
            cols_display = ["filename", "fournisseur", "date", "numero_facture",
                            "montant_ht", "tva", "montant_ttc", "statut"]
            df_display = df[[c for c in cols_display if c in df.columns]].copy()
            df_display.insert(0, "✅", False)

            for fname in df_display["filename"]:
                if fname not in st.session_state["selected_rows"]:
                    st.session_state["selected_rows"][fname] = False

            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "✅": st.column_config.CheckboxColumn("✅", default=False),
                    "statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸", "À vérifier 🐱", "Erreur 🙀", "En attente 😺"]
                    ),
                },
                key="table_factures"
            )

            # Sync sélections + clic pour changer la prévisualisation
            for i, row in edited_df.iterrows():
                fname = df_display.iloc[i]["filename"]
                if fname:
                    st.session_state["selected_rows"][fname] = row["✅"]

            # Boutons sélection rapide
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("☑️ Tout sélectionner", use_container_width=True, key="sel_all"):
                    for fname in df["filename"].tolist():
                        st.session_state["selected_rows"][fname] = True
                    st.rerun()
            with col_s2:
                if st.button("⬜ Tout désélectionner", use_container_width=True, key="desel_all"):
                    st.session_state["selected_rows"] = {}
                    st.rerun()

        # ────────────────────────────────────────────────────────────────────
        # COLONNE 3 : Métriques + Actions + Chat
        # ────────────────────────────────────────────────────────────────────
        with col_metrics:
            st.markdown('<div class="section-title">📊 Métriques</div>', unsafe_allow_html=True)

            df = pd.DataFrame(st.session_state["factures"])
            selected_files = [fname for fname, checked in st.session_state["selected_rows"].items() if checked]

            if selected_files:
                df_metrics = df[df["filename"].isin(selected_files)]
                mode_label = f"✅ {len(selected_files)} sélectionnée(s)"
            elif st.session_state["selected_preview"]:
                df_metrics = df[df["filename"] == st.session_state["selected_preview"]]
                mode_label = f"📄 Facture affichée"
            else:
                df_metrics = df
                mode_label = "📊 Toutes"

            st.markdown(f"<p style='color:#c8956c; font-size:0.78rem; text-align:center; margin-bottom:0.8rem;'>{mode_label}</p>",
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

            # ── Exports ──
            st.markdown('<div class="section-title">💾 Exports</div>', unsafe_allow_html=True)

            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            st.download_button(
                label="📥 Excel",
                data=buffer,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="export_excel"
            )

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 CSV",
                data=csv_data,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_csv"
            )

            if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_factures"):
                st.session_state["factures"] = []
                st.session_state["uploaded_files_data"] = {}
                st.session_state["selected_rows"] = {}
                st.session_state["selected_preview"] = None
                st.rerun()

            st.markdown("---")

            # ── Chat ──
            st.markdown('<div class="section-title">💬 FactureCat Chat</div>', unsafe_allow_html=True)

            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []

            chat_box = st.container()
            with chat_box:
                if not st.session_state["chat_history"]:
                    st.markdown(f"""
                    <div class="chat-bot">
                        <div class="cat-ascii">{ascii_to_html(CAT_ASCII_PETIT)}</div>
                        <b>Miaou ! 🐾</b> Posez-moi vos questions sur vos factures !
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    for msg in st.session_state["chat_history"][-6:]:  # 6 derniers messages
                        if msg["role"] == "user":
                            st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-bot">🐱 {msg["content"]}</div>',
                                        unsafe_allow_html=True)

            user_input = st.text_input("Question...", key="chat_input",
                                       placeholder="Ex: Total des factures ?")

            if st.button("🐾 Envoyer", use_container_width=True, key="send_chat") and user_input:
                st.session_state["chat_history"].append({"role": "user", "content": user_input})
                factures_context = json.dumps(st.session_state["factures"], ensure_ascii=False, indent=2)
                prompt_chat = f"""Tu es FactureCat 🐱, expert comptable félin.
Factures : {factures_context}
Question : {user_input}
Réponds en français, concis, avec des emojis 🐾."""
                with st.spinner("🐱 Réflexion..."):
                    try:
                        response = model.generate_content(prompt_chat)
                        st.session_state["chat_history"].append({
                            "role": "assistant", "content": response.text
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

    else:
        # ── État vide ──
        st.markdown(f"""
        <div style="text-align:center; padding:4rem 0;">
            <div class="cat-ascii" style="font-size:1rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
            <p style="font-size:1.3rem; font-weight:800; color:#a0522d; margin-top:1rem;">
                Aucune facture importée !
            </p>
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
        st.markdown('<div class="section-title">➕ Ajouter une dépense</div>', unsafe_allow_html=True)

        with st.form("form_note_frais", clear_on_submit=True):
            date_depense = st.date_input("📅 Date", datetime.now())
            description  = st.text_input("📝 Description")

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                montant = st.number_input("💰 Montant (€)", min_value=0.0, step=0.01, format="%.2f")
            with col_f2:
                categorie = st.selectbox("📂 Catégorie", [
                    "Transport 🚗", "Repas 🍽️", "Hébergement 🏨",
                    "Fournitures 📦", "Formation 🎓", "Client 🤝", "Autres"
                ])

            col_f3, col_f4 = st.columns(2)
            with col_f3:
                moyen_paiement = st.selectbox("💳 Paiement", [
                    "Carte bancaire", "Espèces", "Virement", "Chèque"
                ])
            with col_f4:
                statut = st.selectbox("📊 Statut", [
                    "En attente 😺", "Validé 😸", "À vérifier 🐱", "Refusé 🙀"
                ])

            justificatif = st.file_uploader("📎 Justificatif", type=["pdf", "png", "jpg", "jpeg"])
            notes = st.text_area("📌 Notes", height=80)

            submitted = st.form_submit_button("🐾 Ajouter la dépense", use_container_width=True)

            if submitted:
                if not description:
                    st.error("❌ La description est obligatoire !")
                elif montant <= 0:
                    st.error("❌ Le montant doit être supérieur à 0 !")
                else:
                    note = {
                        "id": len(st.session_state["notes_frais"]),
                        "Date": date_depense.strftime("%d/%m/%Y"),
                        "Description": description,
                        "Montant (€)": montant,
                        "Catégorie": categorie,
                        "Moyen de paiement": moyen_paiement,
                        "Statut": statut,
                        "Justificatif": justificatif.name if justificatif else "Aucun",
                        "Notes": notes
                    }
                    st.session_state["notes_frais"].append(note)
                    st.success(f"✅ Dépense ajoutée ! 🐾 ({montant:.2f} €)")
                    st.rerun()

        if st.session_state["notes_frais"]:
            st.markdown("---")
            st.markdown('<div class="section-title">🤖 Analyse IA</div>', unsafe_allow_html=True)

            if st.button("🐱 Analyser avec l'IA", use_container_width=True):
                with st.spinner("🐱 Analyse en cours..."):
                    try:
                        notes_context  = json.dumps(st.session_state["notes_frais"], ensure_ascii=False, indent=2)
                        prompt_analyse = f"""Tu es FactureCat 🐱, expert comptable félin.
Analyse ces notes de frais : total par catégorie, dépenses inhabituelles, conseils.
{notes_context}
Réponds en français avec des emojis 🐾."""
                        response = model.generate_content(prompt_analyse)
                        st.markdown(f'<div class="chat-bot">🐱 {response.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

    with col2:
        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])
            df_nf = df_nf.drop(columns=["id"], errors="ignore")

            total_depenses = df_nf["Montant (€)"].sum() if "Montant (€)" in df_nf.columns else 0
            nb_depenses    = len(df_nf)

            st.markdown('<div class="section-title">📊 Tableau des dépenses</div>', unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_depenses:.2f} €</div>
                    <div class="metric-label">Total dépenses 💰</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{nb_depenses}</div>
                    <div class="metric-label">Nb dépenses 📋</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            edited_nf = st.data_editor(
                df_nf,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["En attente 😺", "Validé 😸", "À vérifier 🐱", "Refusé 🙀"]
                    ),
                    "Catégorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=["Transport 🚗", "Repas 🍽️", "Hébergement 🏨",
                                 "Fournitures 📦", "Formation 🎓", "Client 🤝", "Autres"]
                    )
                }
            )

            st.markdown("---")

            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                buffer_nf = io.BytesIO()
                df_nf.to_excel(buffer_nf, index=False, engine="openpyxl")
                buffer_nf.seek(0)
                st.download_button(
                    label="📥 Excel",
                    data=buffer_nf,
                    file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col_e2:
                csv_nf = df_nf.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📄 CSV",
                    data=csv_nf,
                    file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_e3:
                if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_notes"):
                    st.session_state["notes_frais"] = []
                    st.rerun()

        else:
            st.markdown(f"""
            <div style="text-align:center; padding:4rem 0;">
                <div class="cat-ascii" style="font-size:1rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
                <p style="font-size:1.3rem; font-weight:800; color:#a0522d; margin-top:1rem;">
                    Aucune dépense ajoutée !
                </p>
                <p style="color:#c8956c;">Ajoutez vos dépenses à gauche pour commencer 🐾</p>
            </div>
            """, unsafe_allow_html=True)
