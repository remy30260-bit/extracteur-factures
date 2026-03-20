import streamlit as st
from supabase import Client
from datetime import datetime

def show_parametres(supabase: Client):
    
    user_id = st.session_state.user["id"]
    user_email = st.session_state.user.get("email", "")
    
    st.markdown("<div class='main-title'>⚙️ Paramètres</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Configuration de votre compte</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Profil", "🔑 API & Intégrations", "🗄️ Données"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — PROFIL
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 👤 Informations du profil")
        
        # Chargement profil existant
        try:
            profil = supabase.table("profils").select("*").eq("user_id", user_id).execute().data
            profil = profil[0] if profil else {}
        except:
            profil = {}
        
        with st.form("form_profil"):
            c1, c2 = st.columns(2)
            
            with c1:
                nom = st.text_input("Nom", value=profil.get("nom", ""))
                prenom = st.text_input("Prénom", value=profil.get("prenom", ""))
                email_display = st.text_input("Email", value=user_email, disabled=True)
            
            with c2:
                entreprise = st.text_input("Entreprise", value=profil.get("entreprise", ""))
                siret = st.text_input("SIRET", value=profil.get("siret", ""))
                telephone = st.text_input("Téléphone", value=profil.get("telephone", ""))
            
            adresse = st.text_area("Adresse", value=profil.get("adresse", ""), height=80)
            
            c3, c4 = st.columns(2)
            with c3:
                tva_number = st.text_input("N° TVA intracommunautaire", value=profil.get("tva_number", ""))
            with c4:
                devise = st.selectbox(
                    "Devise par défaut",
                    ["EUR", "USD", "GBP", "CHF"],
                    index=["EUR", "USD", "GBP", "CHF"].index(profil.get("devise", "EUR"))
                )
            
            submitted = st.form_submit_button("💾 Sauvegarder", use_container_width=True, type="primary")
            
            if submitted:
                try:
                    data = {
                        "user_id": user_id,
                        "nom": nom,
                        "prenom": prenom,
                        "entreprise": entreprise,
                        "siret": siret,
                        "telephone": telephone,
                        "adresse": adresse,
                        "tva_number": tva_number,
                        "devise": devise,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    if profil:
                        supabase.table("profils").update(data).eq("user_id", user_id).execute()
                    else:
                        supabase.table("profils").insert(data).execute()
                    
                    st.success("✅ Profil sauvegardé !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — API & INTÉGRATIONS
    # ══════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🔑 Clés API")
        
        # Gemini API Key
        st.markdown("""
        <div class='card' style='border: 1px solid #f0a500;'>
            <h4 style='color:#f0a500; margin:0 0 0.5rem 0;'>🤖 Google Gemini</h4>
            <p style='color:#aaa; margin:0; font-size:0.9rem;'>
                Nécessaire pour l'analyse automatique des factures et reçus.<br>
                Obtenez votre clé sur <a href='https://makersuite.google.com/app/apikey' 
                target='_blank' style='color:#4a90d9;'>Google AI Studio</a>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        current_key = st.session_state.get("gemini_api_key", "")
        
        with st.form("form_api"):
            api_key_input = st.text_input(
                "Clé API Gemini",
                value=current_key,
                type="password",
                placeholder="AIzaSy..."
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                save_api = st.form_submit_button("💾 Sauvegarder", use_container_width=True, type="primary")
            with col_b:
                test_api = st.form_submit_button("🧪 Tester", use_container_width=True)
            
            if save_api and api_key_input:
                st.session_state.gemini_api_key = api_key_input
                # Sauvegarde en base (chiffrée idéalement)
                try:
                    supabase.table("profils").upsert({
                        "user_id": user_id,
                        "gemini_api_key": api_key_input,
                        "updated_at": datetime.now().isoformat()
                    }).execute()
                except:
                    pass
                st.success("✅ Clé API sauvegardée !")
            
            if test_api and api_key_input:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key_input)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content("Réponds juste 'OK' en un mot.")
                    if response.text:
                        st.success(f"✅ API fonctionnelle ! Réponse : {response.text.strip()}")
                    else:
                        st.error("❌ Pas de réponse")
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
        
        # Statut actuel
        st.markdown("---")
        st.markdown("#### 📊 Statut des intégrations")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.session_state.get("gemini_api_key"):
                st.success("🤖 Gemini AI : **Configuré** ✅")
            else:
                st.warning("🤖 Gemini AI : **Non configuré** ⚠️")
        with col_s2:
            st.success("🗄️ Supabase : **Connecté** ✅")

    # ══════════════════════════════════════════════════════════
    # TAB 3 — DONNÉES
    # ══════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🗄️ Gestion des données")
        
        # Stats
        try:
            nb_factures = len(supabase.table("factures").select("id").eq("user_id", user_id).execute().data or [])
            nb_notes = len(supabase.table("notes_frais").select("id").eq("user_id", user_id).execute().data or [])
        except:
            nb_factures, nb_notes = 0, 0
        
        c1, c2 = st.columns(2)
        c1.metric("🧾 Factures stockées", nb_factures)
        c2.metric("📝 Notes de frais", nb_notes)
        
        st.markdown("---")
        
        # Zone danger
        st.markdown("""
        <div class='card' style='border: 1px solid #e74c3c;'>
            <h4 style='color:#e74c3c; margin:0 0 0.5rem 0;'>⚠️ Zone dangereuse</h4>
            <p style='color:#aaa; margin:0; font-size:0.9rem;'>
                Ces actions sont irréversibles. Procédez avec précaution.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("**🗑️ Supprimer toutes les factures**")
            confirm_f = st.checkbox("Je confirme la suppression des factures", key="confirm_del_factures")
            if st.button("🗑️ Supprimer factures", disabled=not confirm_f, use_container_width=True):
                try:
                    supabase.table("factures").delete().eq("user_id", user_id).execute()
                    st.success("✅ Toutes les factures ont été supprimées.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
        
        with col_d2:
            st.markdown("**🗑️ Supprimer toutes les notes de frais**")
            confirm_n = st.checkbox("Je confirme la suppression des notes", key="confirm_del_notes")
            if st.button("🗑️ Supprimer notes", disabled=not confirm_n, use_container_width=True):
                try:
                    supabase.table("notes_frais").delete().eq("user_id", user_id).execute()
                    st.success("✅ Toutes les notes ont été supprimées.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
        
        st.markdown("---")
        
        # Déconnexion
        st.markdown("**🚪 Déconnexion**")
        if st.button("🚪 Se déconnecter", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
