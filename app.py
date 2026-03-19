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
                        st.success("✅ Connexion réussie ! 🐾")
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
    padding-left: 2rem !important;
    padding-right: 2rem !important;
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
    box-shadow: 0 2px 8px rgba(200,149,108,0.2) !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: #fdf6f0 !important;
    border-color: #e8856a !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(200,149,108,0.4) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #f0a070, #e8856a) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(200,149,108,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(200,149,108,0.6) !important;
}

.card {
    background: white;
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(160,82,45,0.12);
    border: 1px solid rgba(200,149,108,0.2);
    margin-bottom: 1rem;
}

.metric-card {
    background: linear-gradient(135deg, #fff9f5, #fdf0e8);
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(160,82,45,0.1);
}
.metric-value {
    font-size: 2rem;
    font-weight: 900;
    color: #a0522d;
}
.metric-label {
    font-size: 0.85rem;
    color: #c8956c;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.chat-user {
    background: linear-gradient(135deg, #f0a070, #e8856a);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    max-width: 80%;
    margin-left: auto;
    box-shadow: 0 4px 15px rgba(200,149,108,0.3);
}
.chat-bot {
    background: white;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 18px 18px 18px 4px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    max-width: 80%;
    box-shadow: 0 4px 15px rgba(160,82,45,0.1);
}

.badge { display: inline-block; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
.badge-ok { background: #d4edda; color: #155724; }
.badge-warn { background: #fff3cd; color: #856404; }
.badge-error { background: #f8d7da; color: #721c24; }

.section-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #a0522d;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #f0a070;
}

[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #f0a070;
    border-radius: 16px;
    padding: 1rem;
}

.cat-ascii {
    font-family: monospace;
    font-size: 0.7rem !important;
    line-height: 1.2;
    color: #c8956c;
    white-space: pre;
}

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    border: 2px solid rgba(200,149,108,0.3) !important;
    border-radius: 12px !important;
    background: white !important;
}
.stTextInput > div > div > input:focus {
    border-color: #f0a070 !important;
    box-shadow: 0 0 0 3px rgba(240,160,112,0.2) !important;
}

hr { border-color: rgba(200,149,108,0.3) !important; }

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #fdf6f0; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(#f0a070, #c8956c);
    border-radius: 4px;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(200,149,108,0.2);
}

.preview-container {
    background: #fdf6f0;
    border: 2px solid rgba(200,149,108,0.3);
    border-radius: 16px;
    padding: 1rem;
    margin-top: 1rem;
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

# ─── PAGE FACTURES ────────────────────────────────────────────────────────────
if page == "📄 Factures":

    if "factures" not in st.session_state:
        st.session_state["factures"] = []
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "uploaded_files_data" not in st.session_state:
        st.session_state["uploaded_files_data"] = {}

    col1, col2 = st.columns([1, 1], gap="large")

    # ── Colonne gauche : upload + prévisualisation + chat ───────────────────
    with col1:

        # ── Upload ──
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
                        # Stocker les bytes pour prévisualisation
                        st.session_state["uploaded_files_data"][uploaded_file.name] = {
                            "bytes": file_bytes,
                            "type": uploaded_file.type
                        }
                        result = analyze_invoice(file_bytes, uploaded_file.type, uploaded_file.name)
                        if result:
                            result["filename"] = uploaded_file.name
                            result["id"] = len(st.session_state["factures"])
                            st.session_state["factures"].append(result)
                            st.success(f"✅ {uploaded_file.name} analysée ! 🐾")
                        else:
                            st.error(f"❌ Échec pour {uploaded_file.name}")
                else:
                    # Mettre à jour les bytes si le fichier existe déjà
                    if uploaded_file.name not in st.session_state["uploaded_files_data"]:
                        file_bytes = uploaded_file.read()
                        st.session_state["uploaded_files_data"][uploaded_file.name] = {
                            "bytes": file_bytes,
                            "type": uploaded_file.type
                        }

        # ── Prévisualisation ──
        if st.session_state["uploaded_files_data"]:
            st.markdown('<div class="section-title">👁️ Prévisualisation</div>', unsafe_allow_html=True)

            filenames = list(st.session_state["uploaded_files_data"].keys())
            selected_file = st.selectbox(
                "Choisir une facture à prévisualiser",
                filenames,
                label_visibility="collapsed"
            )

            if selected_file:
                file_data = st.session_state["uploaded_files_data"][selected_file]
                file_bytes = file_data["bytes"]
                file_type = file_data["type"]

                st.markdown(f"**📄 {selected_file}**")

                if file_type == "application/pdf":
                    try:
                        images = extract_pdf_images(file_bytes)
                        if images:
                            # Afficher toutes les pages
                            for i, img in enumerate(images):
                                if len(images) > 1:
                                    st.caption(f"Page {i+1}/{len(images)}")
                                st.image(img, use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Erreur prévisualisation PDF : {e}")
                else:
                    try:
                        img = Image.open(io.BytesIO(file_bytes))
                        st.image(img, use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Erreur prévisualisation image : {e}")

                # Bouton téléchargement
                st.download_button(
                    label=f"📥 Télécharger {selected_file}",
                    data=file_bytes,
                    file_name=selected_file,
                    mime=file_type,
                    use_container_width=True
                )

        st.markdown("---")

        # ── Chat ──
        st.markdown('<div class="section-title">💬 Chat avec FactureCat</div>', unsafe_allow_html=True)

        chat_container = st.container()
        with chat_container:
            if not st.session_state["chat_history"]:
                st.markdown(f"""
                <div class="chat-bot">
                    <div class="cat-ascii">{ascii_to_html(CAT_ASCII_PETIT)}</div>
                    <b>Miaou ! 🐾</b> Je suis FactureCat, votre assistant comptable félin !<br>
                    Importez des factures et posez-moi vos questions !
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state["chat_history"]:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>',
                                    unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-bot">🐱 {msg["content"]}</div>',
                                    unsafe_allow_html=True)

        user_input = st.text_input("Votre question...", key="chat_input",
                                   placeholder="Ex: Quel est le total de mes factures ?")

        if st.button("🐾 Envoyer", use_container_width=True) and user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})

            factures_context = json.dumps(st.session_state["factures"], ensure_ascii=False, indent=2)
            prompt_chat = f"""Tu es FactureCat 🐱, expert comptable félin sympa et professionnel.
Voici les factures de l'utilisateur :
{factures_context}

Question : {user_input}

Réponds en français, de façon concise et utile, avec des emojis 🐾."""

            with st.spinner("🐱 FactureCat réfléchit..."):
                try:
                    response = model.generate_content(prompt_chat)
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": response.text
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    # ── Colonne droite : métriques + tableau ────────────────────────────────
        # ── Colonne droite : métriques + tableau ────────────────────────────────
    with col2:
        if st.session_state["factures"]:
            df = pd.DataFrame(st.session_state["factures"])

            # ── Sélection de la facture prévisualisée ──
            selected_file = None
            filenames = list(st.session_state["uploaded_files_data"].keys())
            if filenames:
                if "selected_preview" not in st.session_state:
                    st.session_state["selected_preview"] = filenames[0]
                selected_file = st.session_state.get("selected_preview", filenames[0])

            # ── Tableau avec cases à cocher ──
            st.markdown('<div class="section-title">📋 Tableau des factures</div>', unsafe_allow_html=True)

            # Ajouter colonne sélection
            if "selected_rows" not in st.session_state:
                st.session_state["selected_rows"] = {}

            cols_display = ["filename", "fournisseur", "date", "montant_ht", "tva", "montant_ttc", "categorie", "statut"]
            cols_present = [c for c in cols_display if c in df.columns]
            df_display = df[cols_present].copy()

            # Ajouter colonne checkbox
            df_display.insert(0, "✅ Sélect.", [
                st.session_state["selected_rows"].get(row["filename"], False)
                for _, row in df[cols_present].iterrows()
            ])

            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "✅ Sélect.": st.column_config.CheckboxColumn("✅", default=False),
                    "statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸", "À vérifier 🐱", "Erreur 🙀", "En attente 😺"]
                    ),
                    "categorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=["Transport 🚗", "Repas 🍽️", "Hébergement 🏨",
                                 "Fournitures 📦", "Formation 🎓", "Client 🤝", "Autres"]
                    )
                }
            )

            # Mettre à jour les sélections
            for i, row in edited_df.iterrows():
                fname = df_display.iloc[i]["filename"] if "filename" in df_display.columns else None
                if fname:
                    st.session_state["selected_rows"][fname] = row["✅ Sélect."]

            # ── Métriques dynamiques ──
            selected_files = [fname for fname, checked in st.session_state["selected_rows"].items() if checked]

            # Si aucune case cochée → montrer la facture prévisualisée
            if not selected_files and selected_file:
                df_metrics = df[df["filename"] == selected_file]
                mode_label = f"📄 {selected_file}"
            elif selected_files:
                df_metrics = df[df["filename"].isin(selected_files)]
                mode_label = f"✅ {len(selected_files)} facture(s) sélectionnée(s)"
            else:
                df_metrics = df
                mode_label = "📊 Toutes les factures"

            total_ttc = df_metrics["montant_ttc"].sum() if "montant_ttc" in df_metrics.columns else 0
            total_ht  = df_metrics["montant_ht"].sum()  if "montant_ht"  in df_metrics.columns else 0
            total_tva = df_metrics["tva"].sum()          if "tva"         in df_metrics.columns else 0
            nb_factures = len(df_metrics)

            st.markdown(f"<p style='color:#c8956c; font-size:0.85rem; text-align:center;'>Mode : <b>{mode_label}</b></p>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_ttc:.2f} €</div>
                    <div class="metric-label">Total TTC 🔥</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{nb_factures}</div>
                    <div class="metric-label">Factures 📄</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            c3, c4 = st.columns(2)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_ht:.2f} €</div>
                    <div class="metric-label">Total HT 📊</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_tva:.2f} €</div>
                    <div class="metric-label">Total TVA 🧾</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Bouton tout sélectionner / désélectionner ──
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                if st.button("☑️ Tout sélectionner", use_container_width=True):
                    for fname in df["filename"].tolist():
                        st.session_state["selected_rows"][fname] = True
                    st.rerun()
            with col_sel2:
                if st.button("⬜ Tout désélectionner", use_container_width=True):
                    st.session_state["selected_rows"] = {}
                    st.rerun()

            st.markdown("---")

            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button(
                    label="📥 Exporter Excel",
                    data=buffer,
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_act2:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📄 Exporter CSV",
                    data=csv_data,
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col_act3:
                if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_factures"):
                    st.session_state["factures"] = []
                    st.session_state["uploaded_files_data"] = {}
                    st.session_state["selected_rows"] = {}
                    st.rerun()

        else:
            st.markdown(f"""
            <div style="text-align:center; padding:4rem 0;">
                <div class="cat-ascii" style="font-size:1rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
                <p style="font-size:1.3rem; font-weight:800; color:#a0522d; margin-top:1rem;">
                    Aucune facture importée !
                </p>
                <p style="color:#c8956c;">Glissez vos factures à gauche pour commencer 🐾</p>
            </div>
            """, unsafe_allow_html=True)


            # Tableau
            st.markdown('<div class="section-title">📋 Tableau des factures</div>', unsafe_allow_html=True)

            cols_display = ["filename", "fournisseur", "date", "montant_ht",
                            "tva", "montant_ttc", "categorie", "statut"]
            cols_present = [c for c in cols_display if c in df.columns]
            df_display = df[cols_present].copy()
            df_display.columns = [c.replace("_", " ").title() for c in cols_present]

            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut",
                        options=["Validé 😸", "À vérifier 🐱", "Erreur 🙀", "En attente 😺"]
                    ),
                    "Categorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=["Transport 🚗", "Repas 🍽️", "Hébergement 🏨",
                                 "Fournitures 📦", "Formation 🎓", "Client 🤝", "Autres"]
                    )
                }
            )

            st.markdown("---")

            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button(
                    label="📥 Exporter Excel",
                    data=buffer,
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_act2:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📄 Exporter CSV",
                    data=csv_data,
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

             with col_act3:
                if st.button("🗑️ Effacer tout", use_container_width=True, key="clear_factures"):
                    st.session_state["factures"] = []
                    st.session_state["uploaded_files_data"] = {}
                    st.session_state["selected_rows"] = {}
                    st.rerun()

    else:
        st.markdown(f"""
        <div style="text-align:center; padding:4rem 0;">
            <div class="cat-ascii" style="font-size:1rem !important;">{ascii_to_html(CAT_ASCII_GRAND)}</div>
            <p style="font-size:1.3rem; font-weight:800; color:#a0522d; margin-top:1rem;">
                Aucune facture importée !
            </p>
            <p style="color:#c8956c;">Glissez vos factures à gauche pour commencer 🐾</p>
        </div>
        """, unsafe_allow_html=True)


# ─── PAGE NOTES DE FRAIS ──────────────────────────────────────────────────────
elif page == "💰 Notes de frais":

    if "notes_frais" not in st.session_state:
        st.session_state["notes_frais"] = []

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-title">➕ Ajouter une dépense</div>', unsafe_allow_html=True)

        with st.form("form_note_frais", clear_on_submit=True):
            date_depense = st.date_input("📅 Date", datetime.now())
            description = st.text_input("📝 Description")

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
                moyen_paiement = st.selectbox("💳 Moyen de paiement", [
                    "Carte bleue", "Espèces", "Virement", "Chèque", "Autres"
                ])
            with col_f4:
                statut = st.selectbox("📊 Statut", [
                    "En attente 😺", "Validé 😸", "À vérifier 🐱", "Refusé 🙀"
                ])

            justificatif = st.file_uploader("📎 Justificatif (optionnel)",
                                            type=["pdf", "png", "jpg", "jpeg"])
            notes = st.text_area("📌 Notes", placeholder="Informations complémentaires...")

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

        # ── Analyse IA ──
        if st.session_state["notes_frais"]:
            st.markdown("---")
            st.markdown('<div class="section-title">🤖 Analyse IA des dépenses</div>', unsafe_allow_html=True)

            if st.button("🐱 Analyser mes dépenses avec l'IA", use_container_width=True):
                notes_context = json.dumps(st.session_state["notes_frais"], ensure_ascii=False, indent=2)
                prompt_analyse = f"""Tu es FactureCat 🐱, expert comptable félin.
Analyse ces notes de frais et fournis :
1. Un résumé des dépenses par catégorie
2. Les dépenses inhabituellement élevées
3. Des conseils pour optimiser les dépenses
4. Un commentaire général sur la gestion des frais

Notes de frais :
{notes_context}

Réponds en français avec des emojis 🐾 et sois concis mais utile."""

                with st.spinner("🐱 FactureCat analyse vos dépenses..."):
                    try:
                        response = model.generate_content(prompt_analyse)
                        st.markdown(f'<div class="chat-bot">🐱 {response.text}</div>',
                                    unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

    with col2:
        if st.session_state["notes_frais"]:
            df_nf = pd.DataFrame(st.session_state["notes_frais"])
            df_nf = df_nf.drop(columns=["id"], errors="ignore")

            total_nf = df_nf["Montant (€)"].sum() if "Montant (€)" in df_nf.columns else 0
            nb_nf = len(df_nf)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_nf:.2f} €</div>
                    <div class="metric-label">Total dépenses 💰</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{nb_nf}</div>
                    <div class="metric-label">Dépenses 📝</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if "Catégorie" in df_nf.columns and "Montant (€)" in df_nf.columns:
                cat_totals = df_nf.groupby("Catégorie")["Montant (€)"].sum().reset_index()
                st.bar_chart(cat_totals.set_index("Catégorie"))

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">📋 Tableau des dépenses</div>', unsafe_allow_html=True)

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
                    label="📥 Exporter Excel",
                    data=buffer_nf,
                    file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_e2:
                csv_nf = df_nf.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📄 Exporter CSV",
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
                    Aucune dépense enregistrée !
                </p>
                <p style="color:#c8956c;">Ajoutez votre première dépense à gauche 🐾</p>
            </div>
            """, unsafe_allow_html=True)
