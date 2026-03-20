import streamlit as st
from supabase import Client
import pandas as pd
from datetime import datetime, date
import io

def show_comptabilite(supabase: Client):
    
    user_id = st.session_state.user["id"]
    
    st.markdown("<div class='main-title'>📊 Comptabilité</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Rapports, TVA et exports comptables</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Bilan", "🧾 TVA", "📅 Par période", "📥 Export"])

    # ── CHARGEMENT DONNÉES ────────────────────────────────────
    try:
        factures = supabase.table("factures").select("*").eq("user_id", user_id).execute().data or []
        notes = supabase.table("notes_frais").select("*").eq("user_id", user_id).execute().data or []
    except Exception as e:
        st.error(f"Erreur Supabase : {e}")
        factures, notes = [], []

    df_f = pd.DataFrame(factures) if factures else pd.DataFrame()
    df_n = pd.DataFrame(notes) if notes else pd.DataFrame()

    # ══════════════════════════════════════════════════════════
    # TAB 1 — BILAN
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📈 Bilan général")
        
        # Métriques globales
        total_factures_ttc = df_f["montant_ttc"].sum() if not df_f.empty and "montant_ttc" in df_f else 0
        total_factures_ht = df_f["montant_ht"].sum() if not df_f.empty and "montant_ht" in df_f else 0
        total_tva_factures = df_f["montant_tva"].sum() if not df_f.empty and "montant_tva" in df_f else 0
        total_notes = df_n["montant"].sum() if not df_n.empty and "montant" in df_n else 0
        total_tva_notes = df_n["montant_tva"].sum() if not df_n.empty and "montant_tva" in df_n else 0
        
        solde = total_factures_ttc - total_notes
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total factures (TTC)", f"{total_factures_ttc:,.2f} €")
        c2.metric("📝 Total notes de frais", f"{total_notes:,.2f} €")
        c3.metric(
            "⚖️ Solde net",
            f"{solde:,.2f} €",
            delta=f"{solde:,.2f} €",
            delta_color="normal"
        )
        
        st.markdown("---")
        c4, c5, c6 = st.columns(3)
        c4.metric("📊 Factures HT", f"{total_factures_ht:,.2f} €")
        c5.metric("🏛️ TVA collectée", f"{total_tva_factures:,.2f} €")
        c6.metric("🏛️ TVA déductible", f"{total_tva_notes:,.2f} €")
        
        st.markdown("---")
        
        # Évolution mensuelle
        st.markdown("#### 📅 Évolution mensuelle")
        
        if not df_f.empty and "date_facture" in df_f.columns:
            df_f["mois"] = pd.to_datetime(df_f["date_facture"], errors="coerce").dt.to_period("M").astype(str)
            monthly_f = df_f.groupby("mois")["montant_ttc"].sum().reset_index()
            monthly_f.columns = ["Mois", "Factures TTC (€)"]
            monthly_f = monthly_f.sort_values("Mois")
            
            if not df_n.empty and "date" in df_n.columns:
                df_n["mois"] = pd.to_datetime(df_n["date"], errors="coerce").dt.to_period("M").astype(str)
                monthly_n = df_n.groupby("mois")["montant"].sum().reset_index()
                monthly_n.columns = ["Mois", "Notes de frais (€)"]
                
                merged = pd.merge(monthly_f, monthly_n, on="Mois", how="outer").fillna(0)
                merged = merged.sort_values("Mois")
                st.line_chart(merged.set_index("Mois"))
            else:
                st.bar_chart(monthly_f.set_index("Mois"))
        else:
            st.info("Aucune donnée disponible pour le graphique.")
        
        # Répartition par catégorie
        st.markdown("#### 🗂️ Répartition des factures par catégorie")
        if not df_f.empty and "categorie" in df_f.columns:
            cat_f = df_f.groupby("categorie")["montant_ttc"].sum().reset_index()
            cat_f.columns = ["Catégorie", "Montant TTC (€)"]
            cat_f = cat_f.sort_values("Montant TTC (€)", ascending=False)
            st.bar_chart(cat_f.set_index("Catégorie"))
        else:
            st.info("Aucune donnée de catégorie disponible.")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — TVA
    # ══════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🧾 Déclaration TVA")
        
        st.markdown("""
        <div class='card' style='background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #4a90d9;'>
            <h4 style='color:#4a90d9; margin:0 0 0.5rem 0;'>ℹ️ Comment lire ce tableau</h4>
            <p style='color:#aaa; margin:0; font-size:0.9rem;'>
                <strong>TVA collectée</strong> = TVA sur vos achats/factures fournisseurs<br>
                <strong>TVA déductible</strong> = TVA sur vos notes de frais<br>
                <strong>TVA nette à déclarer</strong> = TVA collectée − TVA déductible
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sélection période
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            annee = st.selectbox(
                "Année",
                list(range(datetime.now().year, datetime.now().year - 5, -1))
            )
        with col_p2:
            trimestre = st.selectbox(
                "Trimestre",
                ["Annuel", "T1 (Jan-Mar)", "T2 (Avr-Jun)", "T3 (Jul-Sep)", "T4 (Oct-Déc)"]
            )
        
        # Filtrage par période
        trimestre_mois = {
            "T1 (Jan-Mar)": [1, 2, 3],
            "T2 (Avr-Jun)": [4, 5, 6],
            "T3 (Jul-Sep)": [7, 8, 9],
            "T4 (Oct-Déc)": [10, 11, 12],
            "Annuel": list(range(1, 13))
        }
        mois_filtre = trimestre_mois[trimestre]
        
        def filter_by_period(df, date_col, annee, mois_list):
            if df.empty or date_col not in df.columns:
                return df
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            return df[
                (df[date_col].dt.year == annee) &
                (df[date_col].dt.month.isin(mois_list))
            ]
        
        df_f_period = filter_by_period(df_f, "date_facture", annee, mois_filtre)
        df_n_period = filter_by_period(df_n, "date", annee, mois_filtre)
        
        tva_collectee = df_f_period["montant_tva"].sum() if not df_f_period.empty and "montant_tva" in df_f_period else 0
        tva_deductible = df_n_period["montant_tva"].sum() if not df_n_period.empty and "montant_tva" in df_n_period else 0
        tva_nette = tva_collectee - tva_deductible
        base_ht = df_f_period["montant_ht"].sum() if not df_f_period.empty and "montant_ht" in df_f_period else 0
        
        # Tableau TVA
        st.markdown("#### 📋 Résumé TVA")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🏛️ TVA collectée", f"{tva_collectee:,.2f} €")
        c2.metric("✅ TVA déductible", f"{tva_deductible:,.2f} €")
        c3.metric(
            "💸 TVA nette à payer",
            f"{tva_nette:,.2f} €",
            delta=f"{'-' if tva_nette < 0 else ''}{abs(tva_nette):,.2f} €",
            delta_color="inverse"
        )
        
        st.markdown("---")
        
        tva_data = {
            "Libellé": [
                "Base HT (factures)",
                "TVA collectée (factures)",
                "TVA déductible (notes de frais)",
                "TVA nette à déclarer",
                "Nombre de factures",
                "Nombre de notes de frais"
            ],
            "Montant": [
                f"{base_ht:,.2f} €",
                f"{tva_collectee:,.2f} €",
                f"{tva_deductible:,.2f} €",
                f"{tva_nette:,.2f} €",
                str(len(df_f_period)),
                str(len(df_n_period))
            ]
        }
        
        st.dataframe(
            pd.DataFrame(tva_data),
            use_container_width=True,
            hide_index=True
        )
        
        # Export TVA
        tva_df = pd.DataFrame(tva_data)
        csv_tva = tva_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Exporter le rapport TVA",
            data=csv_tva,
            file_name=f"tva_{annee}_{trimestre.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ══════════════════════════════════════════════════════════
    # TAB 3 — PAR PÉRIODE
    # ══════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📅 Analyse par période")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            date_debut = st.date_input("Date début", value=date(datetime.now().year, 1, 1))
        with col_d2:
            date_fin = st.date_input("Date fin", value=date.today())
        
        if date_debut <= date_fin:
            def filter_by_dates(df, date_col, d1, d2):
                if df.empty or date_col not in df.columns:
                    return df
                df = df.copy()
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                return df[(df[date_col].dt.date >= d1) & (df[date_col].dt.date <= d2)]
            
            df_f_range = filter_by_dates(df_f, "date_facture", date_debut, date_fin)
            df_n_range = filter_by_dates(df_n, "date", date_debut, date_fin)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Factures TTC", f"{df_f_range['montant_ttc'].sum() if not df_f_range.empty and 'montant_ttc' in df_f_range else 0:,.2f} €")
            c2.metric("Notes de frais", f"{df_n_range['montant'].sum() if not df_n_range.empty and 'montant' in df_n_range else 0:,.2f} €")
            c3.metric("Nb factures", len(df_f_range))
            c4.metric("Nb notes", len(df_n_range))
            
            st.markdown("---")
            
            if not df_f_range.empty:
                st.markdown("#### 🧾 Factures sur la période")
                cols_show = [c for c in ["numero_facture", "fournisseur", "date_facture",
                                          "montant_ht", "montant_tva", "montant_ttc", "statut"]
                             if c in df_f_range.columns]
                st.dataframe(df_f_range[cols_show], use_container_width=True, hide_index=True)
            
            if not df_n_range.empty:
                st.markdown("#### 📝 Notes de frais sur la période")
                cols_show = [c for c in ["date", "fournisseur", "categorie",
                                          "montant", "montant_tva", "statut"]
                             if c in df_n_range.columns]
                st.dataframe(df_n_range[cols_show], use_container_width=True, hide_index=True)
        else:
            st.error("La date de début doit être antérieure à la date de fin.")

    # ══════════════════════════════════════════════════════════
    # TAB 4 — EXPORT
    # ══════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 📥 Export comptable")
        
        st.markdown("""
        <div class='card'>
            <h4 style='margin:0 0 0.5rem 0;'>📦 Exports disponibles</h4>
            <p style='color:#aaa; margin:0; font-size:0.9rem;'>
                Exportez vos données pour votre expert-comptable ou logiciel de comptabilité.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.markdown("#### 🧾 Factures")
            if not df_f.empty:
                csv_f = df_f.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Exporter toutes les factures (CSV)",
                    data=csv_f,
                    file_name=f"factures_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Export Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_f.to_excel(writer, index=False, sheet_name="Factures")
                st.download_button(
                    "📊 Exporter en Excel",
                    data=buffer.getvalue(),
                    file_name=f"factures_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.info("Aucune facture à exporter.")
        
        with col_e2:
            st.markdown("#### 📝 Notes de frais")
            if not df_n.empty:
                csv_n = df_n.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Exporter toutes les notes (CSV)",
                    data=csv_n,
                    file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                buffer2 = io.BytesIO()
                with pd.ExcelWriter(buffer2, engine="openpyxl") as writer:
                    df_n.to_excel(writer, index=False, sheet_name="Notes de frais")
                st.download_button(
                    "📊 Exporter en Excel",
                    data=buffer2.getvalue(),
                    file_name=f"notes_frais_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.info("Aucune note de frais à exporter.")
        
        # Export consolidé
        st.markdown("---")
        st.markdown("#### 📦 Export consolidé (tout en un)")
        
        if not df_f.empty or not df_n.empty:
            buffer3 = io.BytesIO()
            with pd.ExcelWriter(buffer3, engine="openpyxl") as writer:
                if not df_f.empty:
                    df_f.to_excel(writer, index=False, sheet_name="Factures")
                if not df_n.empty:
                    df_n.to_excel(writer, index=False, sheet_name="Notes de frais")
                
                # Résumé
                resume_data = {
                    "Indicateur": [
                        "Total factures TTC",
                        "Total factures HT",
                        "TVA collectée",
                        "Total notes de frais",
                        "TVA déductible",
                        "TVA nette",
                        "Solde net",
                        "Date export"
                    ],
                    "Valeur": [
                        f"{df_f['montant_ttc'].sum() if 'montant_ttc' in df_f else 0:,.2f} €",
                        f"{df_f['montant_ht'].sum() if 'montant_ht' in df_f else 0:,.2f} €",
                        f"{df_f['montant_tva'].sum() if 'montant_tva' in df_f else 0:,.2f} €",
                        f"{df_n['montant'].sum() if 'montant' in df_n else 0:,.2f} €",
                        f"{df_n['montant_tva'].sum() if 'montant_tva' in df_n else 0:,.2f} €",
                        f"{(df_f['montant_tva'].sum() if 'montant_tva' in df_f else 0) - (df_n['montant_tva'].sum() if 'montant_tva' in df_n else 0):,.2f} €",
                        f"{(df_f['montant_ttc'].sum() if 'montant_ttc' in df_f else 0) - (df_n['montant'].sum() if 'montant' in df_n else 0):,.2f} €",
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    ]
                }
                pd.DataFrame(resume_data).to_excel(writer, index=False, sheet_name="Résumé")
            
            st.download_button(
                "📦 Télécharger le rapport complet (Excel)",
                data=buffer3.getvalue(),
                file_name=f"rapport_comptable_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
