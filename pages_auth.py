import streamlit as st
from supabase import Client
import re

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def show_auth(supabase: Client):
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 3rem 0 2rem 0;'>
            <div style='font-size: 5rem;'>🐱</div>
            <h1 style='font-size:2.5rem; font-weight:700; color:#1a1a2e;'>FactureCat</h1>
            <p style='color:#888; font-size:1.1rem;'>Votre comptabilité, simplement.</p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

        # ── CONNEXION ──────────────────────────────────────────
        with tab1:
            with st.form("login_form"):
                st.markdown("### Bon retour ! 👋")
                email = st.text_input("Email", placeholder="vous@exemple.fr")
                password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Se connecter", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Veuillez remplir tous les champs.")
                    elif not is_valid_email(email):
                        st.error("Email invalide.")
                    else:
                        try:
                            response = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": password
                            })
                            if response.user:
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id": response.user.id,
                                    "email": response.user.email
                                }
                                st.success("Connexion réussie !")
                                st.rerun()
                            else:
                                st.error("Email ou mot de passe incorrect.")
                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")

        # ── INSCRIPTION ────────────────────────────────────────
        with tab2:
            with st.form("register_form"):
                st.markdown("### Créer un compte 🚀")
                email_r = st.text_input("Email", placeholder="vous@exemple.fr", key="reg_email")
                password_r = st.text_input("Mot de passe", type="password", placeholder="8 caractères minimum", key="reg_pass")
                password_r2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="••••••••", key="reg_pass2")
                submit_r = st.form_submit_button("Créer mon compte", use_container_width=True)

                if submit_r:
                    if not email_r or not password_r or not password_r2:
                        st.error("Veuillez remplir tous les champs.")
                    elif not is_valid_email(email_r):
                        st.error("Email invalide.")
                    elif len(password_r) < 8:
                        st.error("Le mot de passe doit contenir au moins 8 caractères.")
                    elif password_r != password_r2:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        try:
                            response = supabase.auth.sign_up({
                                "email": email_r,
                                "password": password_r
                            })
                            if response.user:
                                st.success("✅ Compte créé ! Vérifiez votre email pour confirmer votre inscription.")
                            else:
                                st.error("Erreur lors de la création du compte.")
                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")

        st.markdown("""
        <div style='text-align:center; margin-top:2rem; color:#bbb; font-size:0.8rem;'>
            🐱 FactureCat — Votre assistant comptable intelligent
        </div>
        """, unsafe_allow_html=True)
