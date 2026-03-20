import streamlit as st
from supabase import Client
import google.generativeai as genai
import pandas as pd
import json
import re
from datetime import datetime
from PIL import Image
import io

def extract_note_with_gemini(file_bytes, file_type, api_key):
    """Analyse un reçu/ticket avec Gemini"""
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = """Tu es un expert comptable. Analyse ce reçu ou ticket de caisse et extrais les informations en JSON strict.

Retourne UNIQUEMENT ce JSON, sans markdown :

{
    "date": "date au format YYYY-MM-DD ou null",
    "montant": "montant total en float",
    "montant_tva": "montant TVA en float ou null",
    "devise": "EUR par défaut",
    "fournisseur": "nom du commerce ou fournisseur",
    "description": "description de l'achat",
    "categorie": "une parmi: Repas, Transport, Hébergement, Fournitures, Télécom, Formation, Autre",
    "mode_paiement": "mode de paiement ou null",
    "justification": "raison professionnelle probable ou null"
}"""

    try:
        if file_type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            image = Image.open(io.BytesIO(file_bytes))
            response = model.generate_content([prompt, image])
        else:
            import base64
            pdf_data = base64.standard_b64encode(file_bytes).decode("utf-8")
            response = model.generate_content([
                prompt,
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_data
                    }
                }
            ])
        
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        return data, None
    
    except json.JSONDecodeError as e:
        return None, f"Erreur parsing JSON : {e}"
    except Exception as e:
        return None, f"Erreur Gemini : {e}"


def show_notes(supabase: Client):
    
    user_id = st.session_state.user["id"]
    api_key = st.session_state.get("gemini_api_key", "")
    
    st.markdown("<div class='main-title'>📝 Notes de frais</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Gérez vos dépenses professionnelles</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📋 Liste", "📊 Analyse"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — AJOUTER
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### ➕ Nouvelle note de frais")
        
        mode = st.radio(
            "Mode de saisie",
            ["🤖 Analyser un reçu (IA)", "✏️ Saisie manuelle"],
            horizontal=True
        )
        
        extracted = {}
        
        # ── MODE IA ───────────────────────────────────────────
        if "IA" in mode:
            if not api_key:
                st.warning("⚠️ Clé API Gemini manquante. Configurez-la dans les **Paramètres**.")
                return
            
            uploaded = st.file_uploader(
                "Importez votre reçu ou ticket",
                type=["jpg", "jpeg", "png", "webp", "pdf"],
                help="Photo de ticket, reçu, facturette..."
            )
            
            if uploaded:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if uploaded.type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
                        st.image(uploaded, caption="Aperçu", use_column_width=True)
                    else:
                        st.markdown(f"""
                        <div class='card' style='text-align:center; padding:2rem; color:#888;'>
                            📄 {uploaded.name}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🤖 Analyser avec Gemini", type="primary", use_container_width=True):
                        with st.spinner("🔍 Analyse du reçu..."):
                            file_bytes = uploaded.read()
                            data, error = extract_note_with_gemini(file_bytes, uploaded.type, api_key)
                        
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.session_state.note_extracted = data
                            st.success("✅ Reçu analysé !")
            
            if "note_extracted" in st.session_state and st.session_state.note_extracted:
                extracted = st.session_state.note_extracted
        
        # ── FORMULAIRE ────────────────────────────────────────
        st.markdown("---")
        st.markdown("### ✏️ Détails de la dépense")
        
        with st.form("note_form"):
            c1, c2 = st.columns(2)
            
            with c1:
                date_n = st.text_input(
                    "Date (YYYY-MM-DD) *",
                    value=extracted.get("date") or datetime.now().strftime("%Y-%m-%d")
                )
                fournisseur = st.text_input(
                    "Fournisseur / Commerce *",
                    value=extracted.get("fournisseur") or ""
                )
                montant = st.number_input(
                    "Montant (€) *",
                    value=float(extracted.get("montant") or 0),
                    step=0.01,
                    min_value=0.0
                )
                montant_tva = st.number_input(
                    "Dont TVA (€)",
                    value=float(extracted.get("montant_tva") or 0),
                    step=0.01,
                    min_value=0.0
                )
            
            with c2:
                categories = ["Repas", "Transport", "Hébergement", "Fournitures",
                              "Télécom", "Formation", "Autre"]
                cat_val = extracted.get("categorie", "Autre")
                cat_idx = categories.index(cat_val) if cat_val in categories else 6
                categorie = st.selectbox("Catégorie *", categories, index=cat_idx)
                
                mode_paiement = st.selectbox(
                    "Mode de paiement",
                    ["Carte bancaire", "Espèces", "Virement", "Chèque", "Autre"],
                    index=0
                )
                
                statuts = ["en_attente", "validée", "remboursée", "refusée"]
                statut = st.selectbox("Statut", statuts)
            
            description = st.text_area(
                "Description *",
                value=extracted.get("description") or "",
                height=80,
                placeholder="Déjeuner client, billet train Paris-Lyon..."
            )
            
            justification = st.text_area(
                "Justification professionnelle",
                value=extracted.get("justification") or "",
                height=60,
                placeholder="Réunion avec client X, déplacement pour projet Y..."
            )
            
            submitted = st.form_submit_button(
                "💾 Enregistrer la dépense",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not fournisseur or not description:
                    st.error("Fournisseur et description sont obligatoires.")
                elif montant <= 0:
                    st.error("Le montant doit être supérieur à 0.")
                elif not date_n:
                    st.error("La date est obligatoire.")
                else:
                    payload = {
                        "user_id": user_id,
                        "date": date_n,
                        "fournisseur": fournisseur,
                        "montant": montant,
                        "montant_tva": montant_tva,
                        "devise": extracted.get("devise", "EUR"),
                        "categorie": categorie,
                        "description": description,
                        "justification": justification or None,
                        "mode_paiement": mode_paiement,
                        "statut": statut,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    try:
                        supabase.table("notes_frais").insert(payload).execute()
                        st.success("✅ Note de frais enregistrée !")
                        st.session_state.note_extracted = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur Supabase : {e}")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — LISTE
    # ══════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📋 Mes notes de frais")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_statut = st.selectbox(
                "Statut",
                ["Tous", "en_attente", "validée", "remboursée", "refusée"],
                key="nf_statut"
            )
        with col_f2:
            filtre_cat = st.selectbox(
                "Catégorie",
                ["Toutes", "Repas", "Transport", "Hébergement",
                 "Fournitures", "Télécom", "Formation", "Autre"],
                key="nf_cat"
            )
        
        try:
            query = supabase.table("notes_frais").select("*").eq("user_id", user_id)
            
            if filtre_statut != "Tous":
                query = query.eq("statut", filtre_statut)
            if filtre_cat != "Toutes":
                query = query.eq("categorie", filtre_cat)
            
            notes = query.order("date", desc=True).execute().data or []
        
        except Exception as e:
            st.error(f"Erreur : {e}")
            notes = []
        
        if notes:
            total = sum(n.get("montant", 0) or 0 for n in notes)
            total_tva = sum(n.get("montant_tva", 0) or 0 for n in notes)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total dépenses", f"{total:,.2f} €")
            c2.metric("Dont TVA", f"{total_tva:,.2f} €")
            c3.metric("Nombre", len(notes))
            
            st.markdown("---")
            
            for n in notes:
                statut_emoji = {
                    "validée": "✅",
                    "en_attente": "⏳",
                    "remboursée": "💰",
                    "refusée": "❌"
                }.get(n.get("statut"), "❓")
                
                cat_emoji = {
                    "Repas": "🍽️",
                    "Transport": "🚆",
                    "Hébergement": "🏨",
                    "Fournitures": "📦",
                    "Télécom": "📱",
                    "Formation": "📚",
                    "Autre": "📌"
                }.get(n.get("categorie"), "📌")
                
                with st.expander(
                    f"{statut_emoji} {cat_emoji} {n.get('fournisseur', 'N/A')} — "
                    f"{n.get('montant', 0):,.2f} € — {n.get('date', 'N/A')}"
                ):
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown(f"**Date :** {n.get('date', 'N/A')}")
                        st.markdown(f"**Fournisseur :** {n.get('fournisseur', 'N/A')}")
                        st.markdown(f"**Catégorie :** {cat_emoji} {n.get('categorie', 'N/A')}")
                        st.markdown(f"**Montant :** {n.get('montant', 0):,.2f} €")
                        st.markdown(f"**TVA :** {n.get('montant_tva', 0):,.2f} €")
                    
                    with c2:
                        st.markdown(f"**Mode paiement :** {n.get('mode_paiement', 'N/A')}")
                        st.markdown(f"**Statut :** {statut_emoji} {n.get('statut', 'N/A')}")
                        st.markdown(f"**Description :** {n.get('description', 'N/A')}")
                        if n.get("justification"):
                            st.markdown(f"**Justification :** {n['justification']}")
                    
                    col_edit, col_del = st.columns(2)
                    
                    with col_edit:
                        new_statut = st.selectbox(
                            "Changer statut",
                            ["en_attente", "validée", "remboursée", "refusée"],
                            index=["en_attente", "validée", "remboursée", "refusée"].index(
                                n.get("statut", "en_attente")
                            ),
                            key=f"nf_statut_{n['id']}"
                        )
                        if st.button("💾 Mettre à jour", key=f"nf_update_{n['id']}"):
                            try:
                                supabase.table("notes_frais").update(
                                    {"statut": new_statut}
                                ).eq("id", n["id"]).execute()
                                st.success("Statut mis à jour !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    
                    with col_del:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Supprimer", key=f"nf_del_{n['id']}", type="secondary"):
                            try:
                                supabase.table("notes_frais").delete().eq("id", n["id"]).execute()
                                st.success("Note supprimée.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
        else:
            st.markdown("""
            <div class='card' style='text-align:center; color:#888; padding:3rem;'>
                📭 Aucune note de frais trouvée
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # TAB 3 — ANALYSE
    # ══════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📊 Analyse des dépenses")
        
        try:
            all_notes = supabase.table("notes_frais").select("*").eq("user_id", user_id).execute().data or []
        except:
            all_notes = []
        
        if all_notes:
            df = pd.DataFrame(all_notes)
            
            # Par catégorie
            st.markdown("#### 📊 Dépenses par catégorie")
            if "categorie" in df.columns and "montant" in df.columns:
                cat_group = df.groupby("categorie")["montant"].sum().reset_index()
                cat_group.columns = ["Catégorie", "Montant (€)"]
                cat_group = cat_group.sort_values("Montant (€)", ascending=False)
                st.bar_chart(cat_group.set_index("Catégorie"))
            
            # Par mois
            st.markdown("#### 📅 Dépenses par mois")
            if "date" in df.columns:
                df["mois"] = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").astype(str)
                mois_group = df.groupby("mois")["montant"].sum().reset_index()
                mois_group.columns = ["Mois", "Montant (€)"]
                mois_group = mois_group.sort_values("Mois")
                st.bar_chart(mois_group.set_index("Mois"))
            
            # Export
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Exporter en CSV",
                data=csv,
                file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Aucune donnée à analyser.")
