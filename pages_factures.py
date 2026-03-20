import streamlit as st
from supabase import Client
import google.generativeai as genai
import pandas as pd
import json
import re
from datetime import datetime
import base64
from PIL import Image
import io

def extract_facture_with_gemini(file_bytes, file_type, api_key):
    """Analyse une facture avec Gemini et extrait les données structurées"""
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = """Tu es un expert comptable. Analyse cette facture et extrais les informations suivantes en JSON strict.

Retourne UNIQUEMENT ce JSON, sans markdown, sans explication :

{
    "numero_facture": "numéro de la facture ou null",
    "fournisseur": "nom du fournisseur ou émetteur",
    "fournisseur_siret": "SIRET fournisseur ou null",
    "fournisseur_adresse": "adresse fournisseur ou null",
    "client": "nom du client ou null",
    "date_facture": "date au format YYYY-MM-DD ou null",
    "date_echeance": "date échéance au format YYYY-MM-DD ou null",
    "montant_ht": "montant HT en float ou null",
    "taux_tva": "taux TVA en float (ex: 20.0) ou null",
    "montant_tva": "montant TVA en float ou null",
    "montant_ttc": "montant TTC en float ou null",
    "devise": "EUR par défaut",
    "description": "description des prestations ou produits",
    "categorie": "une parmi: Fournitures, Services, Transport, Restauration, Hébergement, Télécom, Logiciel, Formation, Autre",
    "mode_paiement": "mode de paiement ou null",
    "statut": "en_attente"
}"""

    try:
        if file_type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            image = Image.open(io.BytesIO(file_bytes))
            response = model.generate_content([prompt, image])
        else:
            # PDF → base64
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
        
        # Nettoyage markdown si présent
        raw = re.sub(r"```json|```", "", raw).strip()
        
        data = json.loads(raw)
        return data, None
    
    except json.JSONDecodeError as e:
        return None, f"Erreur parsing JSON : {e}"
    except Exception as e:
        return None, f"Erreur Gemini : {e}"


def show_factures(supabase: Client):
    
    user_id = st.session_state.user["id"]
    api_key = st.session_state.get("gemini_api_key", "")
    
    st.markdown("<div class='main-title'>🧾 Factures</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Importez et gérez vos factures</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📤 Importer", "📋 Liste", "🔍 Détail"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — IMPORT
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📤 Importer une facture")
        
        if not api_key:
            st.warning("⚠️ Clé API Gemini manquante. Configurez-la dans les **Paramètres**.")
            if st.button("⚙️ Aller aux paramètres"):
                st.session_state.page = "settings"
                st.rerun()
            return

        uploaded = st.file_uploader(
            "Glissez votre facture ici",
            type=["pdf", "jpg", "jpeg", "png", "webp"],
            help="Formats acceptés : PDF, JPG, PNG, WEBP"
        )

        if uploaded:
            col_prev, col_info = st.columns([1, 1])
            
            with col_prev:
                st.markdown("**Aperçu**")
                if uploaded.type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
                    st.image(uploaded, use_column_width=True)
                else:
                    st.markdown(f"""
                    <div class='card' style='text-align:center; padding:3rem; color:#888;'>
                        📄 <br><br>
                        <strong>{uploaded.name}</strong><br>
                        <small>{uploaded.size / 1024:.1f} Ko</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_info:
                st.markdown("**Informations**")
                st.markdown(f"""
                <div class='card'>
                    <div><b>Fichier :</b> {uploaded.name}</div>
                    <div><b>Type :</b> {uploaded.type}</div>
                    <div><b>Taille :</b> {uploaded.size / 1024:.1f} Ko</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🤖 Analyser avec Gemini", use_container_width=True, type="primary"):
                    with st.spinner("🔍 Analyse en cours..."):
                        file_bytes = uploaded.read()
                        data, error = extract_facture_with_gemini(file_bytes, uploaded.type, api_key)
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state.facture_extracted = data
                        st.success("✅ Analyse terminée !")

        # ── FORMULAIRE DE VALIDATION ───────────────────────────
        if "facture_extracted" in st.session_state and st.session_state.facture_extracted:
            data = st.session_state.facture_extracted
            
            st.markdown("---")
            st.markdown("### ✏️ Vérifier et sauvegarder")
            
            with st.form("facture_form"):
                c1, c2 = st.columns(2)
                
                with c1:
                    numero = st.text_input("N° Facture", value=data.get("numero_facture") or "")
                    fournisseur = st.text_input("Fournisseur *", value=data.get("fournisseur") or "")
                    siret = st.text_input("SIRET fournisseur", value=data.get("fournisseur_siret") or "")
                    adresse = st.text_area("Adresse fournisseur", value=data.get("fournisseur_adresse") or "", height=80)
                    client = st.text_input("Client", value=data.get("client") or "")
                
                with c2:
                    date_f = st.text_input("Date facture (YYYY-MM-DD)", value=data.get("date_facture") or "")
                    date_e = st.text_input("Date échéance (YYYY-MM-DD)", value=data.get("date_echeance") or "")
                    montant_ht = st.number_input("Montant HT (€)", value=float(data.get("montant_ht") or 0), step=0.01)
                    taux_tva = st.number_input("Taux TVA (%)", value=float(data.get("taux_tva") or 20.0), step=0.1)
                    montant_tva = st.number_input("Montant TVA (€)", value=float(data.get("montant_tva") or 0), step=0.01)
                    montant_ttc = st.number_input("Montant TTC (€) *", value=float(data.get("montant_ttc") or 0), step=0.01)
                
                description = st.text_area("Description", value=data.get("description") or "", height=80)
                
                c3, c4 = st.columns(2)
                with c3:
                    categories = ["Fournitures", "Services", "Transport", "Restauration", 
                                  "Hébergement", "Télécom", "Logiciel", "Formation", "Autre"]
                    cat_val = data.get("categorie", "Autre")
                    cat_idx = categories.index(cat_val) if cat_val in categories else 8
                    categorie = st.selectbox("Catégorie", categories, index=cat_idx)
                
                with c4:
                    statuts = ["en_attente", "payée", "annulée"]
                    statut = st.selectbox("Statut", statuts)
                
                mode_paiement = st.text_input("Mode de paiement", value=data.get("mode_paiement") or "")
                
                submitted = st.form_submit_button("💾 Sauvegarder la facture", use_container_width=True, type="primary")
                
                if submitted:
                    if not fournisseur:
                        st.error("Le fournisseur est obligatoire.")
                    elif montant_ttc <= 0:
                        st.error("Le montant TTC doit être supérieur à 0.")
                    else:
                        payload = {
                            "user_id": user_id,
                            "numero_facture": numero or None,
                            "fournisseur": fournisseur,
                            "fournisseur_siret": siret or None,
                            "fournisseur_adresse": adresse or None,
                            "client": client or None,
                            "date_facture": date_f or None,
                            "date_echeance": date_e or None,
                            "montant_ht": montant_ht,
                            "taux_tva": taux_tva,
                            "montant_tva": montant_tva,
                            "montant_ttc": montant_ttc,
                            "devise": data.get("devise", "EUR"),
                            "description": description or None,
                            "categorie": categorie,
                            "mode_paiement": mode_paiement or None,
                            "statut": statut,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        try:
                            supabase.table("factures").insert(payload).execute()
                            st.success("✅ Facture sauvegardée !")
                            st.session_state.facture_extracted = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur Supabase : {e}")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — LISTE
    # ══════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📋 Mes factures")
        
        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtre_statut = st.selectbox("Statut", ["Tous", "en_attente", "payée", "annulée"])
        with col_f2:
            filtre_cat = st.selectbox("Catégorie", ["Toutes", "Fournitures", "Services", 
                                                      "Transport", "Restauration", "Hébergement",
                                                      "Télécom", "Logiciel", "Formation", "Autre"])
        with col_f3:
            filtre_search = st.text_input("🔍 Rechercher", placeholder="Fournisseur, numéro...")
        
        try:
            query = supabase.table("factures").select("*").eq("user_id", user_id)
            
            if filtre_statut != "Tous":
                query = query.eq("statut", filtre_statut)
            if filtre_cat != "Toutes":
                query = query.eq("categorie", filtre_cat)
            
            factures = query.order("date_facture", desc=True).execute().data or []
            
            # Filtre recherche client-side
            if filtre_search:
                search_lower = filtre_search.lower()
                factures = [
                    f for f in factures
                    if search_lower in (f.get("fournisseur") or "").lower()
                    or search_lower in (f.get("numero_facture") or "").lower()
                ]
        
        except Exception as e:
            st.error(f"Erreur : {e}")
            factures = []
        
        if factures:
            st.markdown(f"**{len(factures)} facture(s) trouvée(s)**")
            
            for f in factures:
                statut_color = {
                    "payée": "#4CAF50",
                    "en_attente": "#FF9800",
                    "annulée": "#f44336"
                }.get(f.get("statut"), "#888")
                
                statut_emoji = {
                    "payée": "✅",
                    "en_attente": "⏳",
                    "annulée": "❌"
                }.get(f.get("statut"), "❓")
                
                with st.expander(
                    f"{statut_emoji} {f.get('fournisseur', 'N/A')} — "
                    f"{f.get('montant_ttc', 0):,.2f} € — "
                    f"{f.get('date_facture', 'N/A')}"
                ):
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown(f"**N° Facture :** {f.get('numero_facture', 'N/A')}")
                        st.markdown(f"**Fournisseur :** {f.get('fournisseur', 'N/A')}")
                        st.markdown(f"**Client :** {f.get('client', 'N/A')}")
                        st.markdown(f"**Catégorie :** {f.get('categorie', 'N/A')}")
                    
                    with c2:
                        st.markdown(f"**Montant HT :** {f.get('montant_ht', 0):,.2f} €")
                        st.markdown(f"**TVA ({f.get('taux_tva', 0)}%) :** {f.get('montant_tva', 0):,.2f} €")
                        st.markdown(f"**Montant TTC :** {f.get('montant_ttc', 0):,.2f} €")
                        st.markdown(f"**Mode paiement :** {f.get('mode_paiement', 'N/A')}")
                    
                    with c3:
                        st.markdown(f"**Date :** {f.get('date_facture', 'N/A')}")
                        st.markdown(f"**Échéance :** {f.get('date_echeance', 'N/A')}")
                        st.markdown(f"**Statut :** <span style='color:{statut_color};'>{f.get('statut', 'N/A')}</span>", unsafe_allow_html=True)
                    
                    if f.get("description"):
                        st.markdown(f"**Description :** {f['description']}")
                    
                    col_edit, col_del = st.columns(2)
                    
                    with col_edit:
                        new_statut = st.selectbox(
                            "Changer le statut",
                            ["en_attente", "payée", "annulée"],
                            index=["en_attente", "payée", "annulée"].index(f.get("statut", "en_attente")),
                            key=f"statut_{f['id']}"
                        )
                        if st.button("💾 Mettre à jour", key=f"update_{f['id']}"):
                            try:
                                supabase.table("factures").update({"statut": new_statut}).eq("id", f["id"]).execute()
                                st.success("Statut mis à jour !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    
                    with col_del:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Supprimer", key=f"del_{f['id']}", type="secondary"):
                            try:
                                supabase.table("factures").delete().eq("id", f["id"]).execute()
                                st.success("Facture supprimée.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
        else:
            st.markdown("""
            <div class='card' style='text-align:center; color:#888; padding:3rem;'>
                📭 Aucune facture trouvée
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # TAB 3 — EXPORT
    # ══════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🔍 Export des données")
        
        try:
            all_factures = supabase.table("factures").select("*").eq("user_id", user_id).execute().data or []
        except:
            all_factures = []
        
        if all_factures:
            df = pd.DataFrame(all_factures)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Aucune donnée à exporter.")
