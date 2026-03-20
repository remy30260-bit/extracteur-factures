import streamlit as st
from supabase import Client
from datetime import datetime, timedelta
import pandas as pd

def show_dashboard(supabase: Client):
    
    user_id = st.session_state.user["id"]
    
    st.markdown("<div class='main-title'>📊 Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Vue d'ensemble de votre comptabilité</div>", unsafe_allow_html=True)

    # ── RÉCUPÉRATION DES DONNÉES ───────────────────────────────
    try:
        factures = supabase.table("factures").select("*").eq("user_id", user_id).execute().data or []
        notes = supabase.table("notes_frais").select("*").eq("user_id", user_id).execute().data or []
    except Exception as e:
        st.error(f"Erreur de connexion Supabase : {e}")
        factures = []
        notes = []

    # ── CALCULS ────────────────────────────────────────────────
    total_factures = sum(f.get("montant_ttc", 0) or 0 for f in factures)
    total_tva = sum(f.get("montant_tva", 0) or 0 for f in factures)
    total_notes = sum(n.get("montant", 0) or 0 for n in notes)
    
    factures_ce_mois = [
        f for f in factures
        if f.get("date_facture") and
        datetime.fromisoformat(f["date_facture"]).month == datetime.now().month
        and datetime.fromisoformat(f["date_facture"]).year == datetime.now().year
    ]
    total_mois = sum(f.get("montant_ttc", 0) or 0 for f in factures_ce_mois)

    en_attente = [f for f in factures if f.get("statut") == "en_attente"]
    payees = [f for f in factures if f.get("statut") == "payée"]

    # ── MÉTRIQUES ──────────────────────────────────────────────
    st.markdown("### 💡 Résumé")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_factures:,.2f} €</div>
            <div class='metric-label'>Total factures (TTC)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:#4CAF50;'>
            <div class='metric-value'>{total_mois:,.2f} €</div>
            <div class='metric-label'>Ce mois-ci</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:#2196F3;'>
            <div class='metric-value'>{total_tva:,.2f} €</div>
            <div class='metric-label'>TVA collectée</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:#FF9800;'>
            <div class='metric-value'>{total_notes:,.2f} €</div>
            <div class='metric-label'>Notes de frais</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── GRAPHIQUES ─────────────────────────────────────────────
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### 📈 Évolution mensuelle")
        
        if factures:
            df = pd.DataFrame(factures)
            df["date_facture"] = pd.to_datetime(df["date_facture"], errors="coerce")
            df = df.dropna(subset=["date_facture"])
            df["mois"] = df["date_facture"].dt.to_period("M").astype(str)
            monthly = df.groupby("mois")["montant_ttc"].sum().reset_index()
            monthly.columns = ["Mois", "Montant (€)"]
            monthly = monthly.sort_values("Mois").tail(6)
            st.bar_chart(monthly.set_index("Mois"))
        else:
            st.markdown("""
            <div class='card' style='text-align:center; color:#888; padding:3rem;'>
                📭 Aucune facture pour afficher le graphique
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 📋 Statuts")
        
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex; justify-content:space-between; margin-bottom:0.75rem;'>
                <span>✅ Payées</span>
                <strong style='color:#4CAF50;'>{len(payees)}</strong>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:0.75rem;'>
                <span>⏳ En attente</span>
                <strong style='color:#FF9800;'>{len(en_attente)}</strong>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span>📝 Notes de frais</span>
                <strong style='color:#2196F3;'>{len(notes)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔔 Alertes")
        
        if len(en_attente) > 0:
            st.warning(f"⚠️ {len(en_attente)} facture(s) en attente de paiement")
        else:
            st.success("✅ Aucune facture en attente")
        
        # Factures > 30 jours
        vieilles = []
        for f in en_attente:
            try:
                date_f = datetime.fromisoformat(f["date_facture"])
                if (datetime.now() - date_f).days > 30:
                    vieilles.append(f)
            except:
                pass
        
        if vieilles:
            st.error(f"🚨 {len(vieilles)} facture(s) impayée(s) depuis +30 jours !")

    # ── DERNIÈRES FACTURES ─────────────────────────────────────
    st.markdown("### 🧾 Dernières factures")
    
    if factures:
        df_display = pd.DataFrame(factures)
        cols = ["numero_facture", "fournisseur", "date_facture", "montant_ttc", "statut"]
        cols_exist = [c for c in cols if c in df_display.columns]
        df_display = df_display[cols_exist].sort_values(
            "date_facture", ascending=False
        ).head(5)
        
        df_display.columns = [c.replace("_", " ").title() for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        if st.button("Voir toutes les factures →"):
            st.session_state.page = "factures"
            st.rerun()
    else:
        st.markdown("""
        <div class='card' style='text-align:center; color:#888; padding:2rem;'>
            📭 Aucune facture enregistrée.<br>
            <small>Commencez par importer une facture !</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Importer ma première facture"):
            st.session_state.page = "factures"
            st.rerun()
