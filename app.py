import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Dashboard Yassir | BI, Supply & AM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FONCTIONS DE CHARGEMENT & NETTOYAGE ---
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, low_memory=False)
    
    # Conversion des types
    df['item total'] = pd.to_numeric(df['item total'], errors='coerce').fillna(0)
    df['delivery time(M)'] = pd.to_numeric(df['delivery time(M)'], errors='coerce')
    df['Discount Amount'] = pd.to_numeric(df['Discount Amount'], errors='coerce').fillna(0)
    df['Distance travel'] = pd.to_numeric(df['Distance travel'], errors='coerce')
    df['_date'] = pd.to_datetime(df['order day'], errors='coerce')
    
    # Préparation des dates pour les graphiques (Semaine, Mois)
    df['_week'] = df['_date'].dt.to_period('W-MON').dt.start_time
    df['_month'] = df['_date'].dt.to_period('M').dt.start_time
    
    # --- REGLES METIERS ---
    mots_a_bannir = ['test', 'fixe', 'p fixe', 'avance']
    pattern = '|'.join(mots_a_bannir)
    df = df[~df['restaurant name'].astype(str).str.contains(pattern, case=False, na=False)]
    
    # Regroupement des franchises (Chaînes)
    df['restaurant name'] = df['restaurant name'].astype(str).str.split(' - ').str[0].str.strip()

    return df

# Note: Pas de cache ici pour éviter le bug du pointeur de fichier vide sur Streamlit
def load_pipelines(files):
    pipelines = []
    for f in files:
        f.seek(0) # Sécurité : Remet le curseur de lecture du fichier à zéro
        try:
            temp = pd.read_csv(f)
            # Nettoyage des noms de colonnes (enlève les espaces invisibles et met en minuscules)
            temp.columns = temp.columns.str.strip().str.lower()
            
            # Vérification sécurisée
            if 'id' in temp.columns:
                am_name = f.name.split('-')[-1].replace('.csv', '').replace('.xlsx', '').strip()
                temp['AM'] = am_name.capitalize()
                temp['Id'] = temp['id'].astype(str) # Uniformisation en texte
                pipelines.append(temp[['Id', 'AM']])
        except Exception as e:
            continue
    
    if pipelines:
        df_p = pd.concat(pipelines, ignore_index=True).drop_duplicates(subset=['Id'])
        return df_p
    return pd.DataFrame()


def wow_delta(cw_val, pw_val):
    if pd.isna(pw_val) or pw_val == 0:
        return "0.0%"
    pct = ((cw_val - pw_val) / pw_val) * 100
    return f"{pct:+.1f}% vs préc."

# --- 3. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.subheader("1️⃣ Données Commandes (Export)")
    uploaded_file = st.file_uploader("Export CSV", type=['csv'], label_visibility="collapsed")
    
    st.subheader("2️⃣ Base Account Managers")
    st.markdown("*(Optionnel) Glissez ici les fichiers Pipeline AM pour activer l'onglet AM.*")
    pipeline_files = st.file_uploader("Pipelines AM (CSV)", type=['csv'], accept_multiple_files=True, label_visibility="collapsed")
    
    st.divider()

# --- 4. CORPS DE L'APPLICATION ---
if uploaded_file is None:
    st.title("Bienvenue sur votre Dashboard de Business Intelligence 👋")
    st.info("👈 Veuillez uploader l'export des commandes dans la barre latérale pour commencer.")
else:
    # 1. Chargement de la Data Globale
    df_global = load_data(uploaded_file)
    
    # 2. Chargement des Pipelines AM
    pipe_df = load_pipelines(pipeline_files) if pipeline_files else pd.DataFrame()
    
    # 3. FUSION GLOBALE SECURISÉE (Avant filtrage des dates)
    if not pipe_df.empty:
        df_global['Restaurant ID'] = df_global['Restaurant ID'].astype(str).str.strip()
        df_global = df_global.merge(pipe_df, left_on='Restaurant ID', right_on='Id', how='left')
        df_global['AM'] = df_global['AM'].fillna('Non Assigné')
    else:
        df_global['AM'] = 'Non Assigné'

    
    # --- FILTRE DE DATE (SIDEBAR) ---
    st.sidebar.subheader("📅 Période d'analyse")
    min_date = df_global['_date'].min().date()
    max_date = df_global['_date'].max().date()
    
    selected_dates = st.sidebar.date_input(
        "Sélectionnez une plage",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates[0]

    # --- FILTRAGE DES DONNÉES TEMPORELLES ---
    cw_df = df_global[(df_global['_date'].dt.date >= start_date) & (df_global['_date'].dt.date <= end_date)].copy()
    
    delta_days = (end_date - start_date).days + 1
    pw_end_date = start_date - datetime.timedelta(days=1)
    pw_start_date = pw_end_date - datetime.timedelta(days=delta_days - 1)
    
    pw_df = df_global[(df_global['_date'].dt.date >= pw_start_date) & (df_global['_date'].dt.date <= pw_end_date)].copy()

    # --- EN-TÊTE PRINCIPAL ---
    st.title("📊 Dashboard Yassir : 360° Operations & Strategy")
    st.markdown(f"**Période analysée :** du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')} ({len(cw_df):,} commandes)")
    st.write("") 

    tab_sales, tab_marketing, tab_ops, tab_am = st.tabs([
        "💰 Sales & Perf.", 
        "🎯 Marketing & Acq.", 
        "⚙️ Supply (Ops)",
        "🤝 Account Management"
    ])

    # ==========================================
    # ONGLET 1 : SALES
    # ==========================================
    with tab_sales:
        st.subheader("Indicateurs Clés de Performance (KPIs)")
        
        cw_req, pw_req = len(cw_df), len(pw_df)
        cw_del = len(cw_df[cw_df['status'] == 'Delivered'])
        pw_del = len(pw_df[pw_df['status'] == 'Delivered'])
        cw_gmv, pw_gmv = cw_df['item total'].sum(), pw_df['item total'].sum()
        cw_aov = cw_gmv / cw_req if cw_req > 0 else 0
        pw_aov = pw_gmv / pw_req if pw_req > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Requests (Total)", f"{cw_req:,}", wow_delta(cw_req, pw_req))
        col2.metric("Delivered (Livrées)", f"{cw_del:,}", wow_delta(cw_del, pw_del))
        col3.metric("GMV (MAD)", f"{cw_gmv:,.0f}", wow_delta(cw_gmv, pw_gmv))
        col4.metric("AOV (Panier Moyen)", f"{cw_aov:,.2f} MAD", wow_delta(cw_aov, pw_aov))
        st.markdown("---")

        if cw_req > 0:
            # --- City Charts ---
            st.subheader("📍 Performance par Ville")
            city_stats = cw_df.groupby('city').agg(Requests=('order id', 'count'), GMV=('item total', 'sum')).reset_index()
            city_stats['AOV'] = (city_stats['GMV'] / city_stats['Requests']).round(2)
            city_stats['GMV'] = city_stats['GMV'].round(2)

            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.plotly_chart(px.bar(city_stats.sort_values('GMV', ascending=False), x='city', y='GMV', title="GMV by City", template="plotly_white", color_discrete_sequence=['#2980B9']), use_container_width=True)
            with col_c2:
                st.plotly_chart(px.bar(city_stats.sort_values('AOV', ascending=False), x='city', y='AOV', title="AOV by City", template="plotly_white", color_discrete_sequence=['#27AE60']), use_container_width=True)
            with col_c3:
                st.plotly_chart(px.bar(city_stats.sort_values('Requests', ascending=False), x='city', y='Requests', title="Requests by City", template="plotly_white", color_discrete_sequence=['#E67E22']), use_container_width=True)
            st.markdown("---")

            # --- Area Charts ---
            st.subheader("🏘️ Performance par Quartier (Top 15)")
            area_stats = cw_df.groupby('Area').agg(Requests=('order id', 'count'), GMV=('item total', 'sum')).reset_index()
            area_stats['AOV'] = (area_stats['GMV'] / area_stats['Requests']).round(2)
            area_stats['GMV'] = area_stats['GMV'].round(2)
            top_areas = area_stats.nlargest(15, 'Requests')

            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.plotly_chart(px.bar(top_areas.sort_values('GMV', ascending=False), x='Area', y='GMV', title="GMV by Area", template="plotly_white", color_discrete_sequence=['#3498DB']), use_container_width=True)
            with col_a2:
                st.plotly_chart(px.bar(top_areas.sort_values('AOV', ascending=False), x='Area', y='AOV', title="AOV by Area", template="plotly_white", color_discrete_sequence=['#2ECC71']), use_container_width=True)
            with col_a3:
                st.plotly_chart(px.bar(top_areas.sort_values('Requests', ascending=False), x='Area', y='Requests', title="Requests by Area", template="plotly_white", color_discrete_sequence=['#F39C12']), use_container_width=True)
            st.markdown("---")

            # --- Top 15 Restaurants Charts ---
            st.subheader("🏆 Classement des Enseignes (Top 15 Chaînes)")
            rest_stats = cw_df.groupby('restaurant name').agg(Requests=('order id', 'count'), GMV=('item total', 'sum')).reset_index()
            rest_stats['AOV'] = (rest_stats['GMV'] / rest_stats['Requests']).round(2)
            rest_stats['GMV'] = rest_stats['GMV'].round(2)

            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                fig_r1 = px.bar(rest_stats.nlargest(15, 'GMV'), x='GMV', y='restaurant name', orientation='h', title="Top 15 par GMV", template="plotly_white", color_discrete_sequence=['#8E44AD'])
                fig_r1.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_r1, use_container_width=True)
            with col_r2:
                fig_r2 = px.bar(rest_stats.nlargest(15, 'AOV'), x='AOV', y='restaurant name', orientation='h', title="Top 15 par AOV", template="plotly_white", color_discrete_sequence=['#16A085'])
                fig_r2.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_r2, use_container_width=True)
            with col_r3:
                fig_r3 = px.bar(rest_stats.nlargest(15, 'Requests'), x='Requests', y='restaurant name', orientation='h', title="Top 15 par Requests", template="plotly_white", color_discrete_sequence=['#D35400'])
                fig_r3.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_r3, use_container_width=True)
            st.markdown("---")

            # --- TABLEAUX ---
            st.subheader("🏢 Résumé Global par Enseigne (Chaînes consolidées)")
            chain_summary = cw_df.groupby('restaurant name').agg(
                Requests=('order id', 'count'),
                Delivered=('status', lambda x: (x == 'Delivered').sum()),
                GMV=('item total', 'sum')
            ).reset_index()
            chain_summary['AOV (MAD)'] = (chain_summary['GMV'] / chain_summary['Requests']).round(2)
            chain_summary['Taux Livraison (%)'] = ((chain_summary['Delivered'] / chain_summary['Requests']) * 100).round(1)
            chain_summary['GMV'] = chain_summary['GMV'].round(2)
            st.dataframe(chain_summary.sort_values(by='GMV', ascending=False), use_container_width=True, hide_index=True)


    # ==========================================
    # ONGLET 2 : MARKETING
    # ==========================================
    with tab_marketing:
        st.subheader("Acquisition & Codes Promo")
        if cw_req > 0:
            cw_users = cw_df['customer Phone'].nunique()
            pw_users = pw_df['customer Phone'].nunique()
            cw_coup = len(cw_df[cw_df['coupon'].notna() & (cw_df['coupon'] != ' ')])
            pw_coup = len(pw_df[pw_df['coupon'].notna() & (pw_df['coupon'] != ' ')])
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("👥 New / Unique Users", f"{cw_users:,}", wow_delta(cw_users, pw_users))
            col_m2.metric("🎟️ Commandes Promo", f"{cw_coup:,}", wow_delta(cw_coup, pw_coup))
            col_m3.metric("📉 Taux Promo", f"{(cw_coup / cw_req * 100):.1f} %", wow_delta(cw_coup/cw_req, pw_coup/pw_req if pw_req else 0))
            st.markdown("---")
            
            df_coupons = cw_df[cw_df['coupon'].notna() & (cw_df['coupon'] != ' ')]
            if not df_coupons.empty:
                coupon_stats = df_coupons.groupby('coupon').agg(Utilisations=('order id', 'count'), Total_Discount=('Discount Amount', 'sum')).reset_index()
                
                col_m4, col_m5 = st.columns(2)
                with col_m4:
                    fig_coup1 = px.bar(coupon_stats.nlargest(10, 'Utilisations'), x='Utilisations', y='coupon', orientation='h', title="Top 10 Coupons (Utilisation)", template="plotly_white", color_discrete_sequence=['#8E44AD'])
                    fig_coup1.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_coup1, use_container_width=True)
                with col_m5:
                    fig_coup2 = px.bar(coupon_stats.nlargest(10, 'Total_Discount'), x='Total_Discount', y='coupon', orientation='h', title="Coût par Coupon (MAD)", template="plotly_white", color_discrete_sequence=['#C0392B'])
                    fig_coup2.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_coup2, use_container_width=True)


    # ==========================================
    # ONGLET 3 : SUPPLY & OPÉRATIONS
    # ==========================================
    with tab_ops:
        st.subheader("Performance de la Flotte (Supply)")
        if cw_req > 0:
            cw_del_time, pw_del_time = cw_df['delivery time(M)'].mean(), pw_df['delivery time(M)'].mean()
            cw_canc = len(cw_df[cw_df['status'] == 'Cancelled'])
            pw_canc = len(pw_df[pw_df['status'] == 'Cancelled'])
            cw_pay = pd.to_numeric(cw_df['driver payout'], errors='coerce').sum()
            pw_pay = pd.to_numeric(pw_df['driver payout'], errors='coerce').sum()
            
            col_o1, col_o2, col_o3 = st.columns(3)
            col_o1.metric("⏱️ Temps de Livraison", f"{cw_del_time:.1f} min", wow_delta(cw_del_time, pw_del_time), delta_color="inverse")
            col_o2.metric("📉 Taux d'Annulation (Total)", f"{(cw_canc / cw_req * 100):.2f} %", wow_delta(cw_canc/cw_req, pw_canc/pw_req if pw_req else 0), delta_color="inverse")
            col_o3.metric("💸 Driver Payout", f"{cw_pay:,.0f} MAD", wow_delta(cw_pay, pw_pay))
            st.markdown("---")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                cw_df['hour'] = pd.to_datetime(cw_df['order time'], format='%H:%M:%S', errors='coerce').dt.hour
                hour_stats = cw_df['hour'].value_counts().sort_index().reset_index()
                hour_stats.columns = ['Heure', 'Commandes']
                st.plotly_chart(px.bar(hour_stats, x='Heure', y='Commandes', title="Rush Hours", template="plotly_white", color_discrete_sequence=['#E74C3C']), use_container_width=True)
            with col_s2:
                st.plotly_chart(px.histogram(cw_df, x='delivery time(M)', nbins=40, title="Distribution des Temps", template="plotly_white", color_discrete_sequence=['#1ABC9C']), use_container_width=True)


    # ==========================================
    # ONGLET 4 : ACCOUNT MANAGEMENT (AM)
    # ==========================================
    with tab_am:
        if not pipeline_files:
            st.warning("⚠️ **Attention :** Pour exploiter cet onglet, veuillez uploader les fichiers 'Pipeline AM' dans la barre latérale.")
        else:
            st.subheader("🤝 Tableau de bord AM (Account Managers)")
            
            # --- FILTRE AM ---
            am_list = sorted([x for x in cw_df['AM'].unique() if x != 'Non Assigné'])
            selected_am = st.selectbox("👤 Choisir l'entité à analyser :", ["Global (Tous les AM)"] + am_list)
            
            if selected_am == "Global (Tous les AM)":
                am_df = cw_df.copy()
                groupby_col = 'AM'
            else:
                am_df = cw_df[cw_df['AM'] == selected_am].copy()
                groupby_col = 'restaurant name'

            if not am_df.empty:
                # --- CALCUL DES KPIs AM (Avec sécurité division par zéro) ---
                am_df['is_auto'] = am_df['Accepted By'].astype(str).str.lower().str.strip() == 'restaurant'
                am_df['is_delivered'] = am_df['status'] == 'Delivered'
                am_df['is_cancelled'] = am_df['status'] == 'Cancelled'

                total_req = len(am_df)
                am_gmv = am_df['item total'].sum()
                am_aov = am_gmv / total_req if total_req > 0 else 0
                succ_rate = (am_df['is_delivered'].sum() / total_req * 100) if total_req > 0 else 0
                canc_rate = (am_df['is_cancelled'].sum() / total_req * 100) if total_req > 0 else 0
                auto_rate = (am_df['is_auto'].sum() / total_req * 100) if total_req > 0 else 0

                # Affichage des KPIs globaux
                st.markdown(f"### 📈 Performance : {selected_am}")
                ca1, ca2, ca3, ca4, ca5 = st.columns(5)
                ca1.metric("💰 GMV", f"{am_gmv:,.0f} MAD")
                ca2.metric("🛒 AOV", f"{am_aov:.1f} MAD")
                ca3.metric("✅ Success Rate", f"{succ_rate:.1f} %")
                ca4.metric("❌ Cancel Rate", f"{canc_rate:.1f} %")
                ca5.metric("🤖 Automatisation", f"{auto_rate:.1f} %")
                
                st.markdown("---")

                # --- TABLEAU RESUME GLOBAL (LIVE) ---
                st.subheader(f"📋 Résumé Global par {groupby_col}")
                am_table = am_df.groupby(groupby_col).agg(
                    Requests=('order id', 'count'),
                    GMV=('item total', 'sum'),
                    Delivered=('is_delivered', 'sum'),
                    Cancelled=('is_cancelled', 'sum'),
                    Automated=('is_auto', 'sum')
                ).reset_index()
                
                am_table['AOV (MAD)'] = (am_table['GMV'] / am_table['Requests']).fillna(0).round(1)
                am_table['Success Rate (%)'] = (am_table['Delivered'] / am_table['Requests'] * 100).fillna(0).round(1)
                am_table['Cancel Rate (%)'] = (am_table['Cancelled'] / am_table['Requests'] * 100).fillna(0).round(1)
                am_table['Automatisation (%)'] = (am_table['Automated'] / am_table['Requests'] * 100).fillna(0).round(1)
                am_table['GMV'] = am_table['GMV'].round(0)
                
                cols_to_show = [groupby_col, 'Requests', 'GMV', 'AOV (MAD)', 'Success Rate (%)', 'Cancel Rate (%)', 'Automatisation (%)']
                st.dataframe(am_table[cols_to_show].sort_values(by='GMV', ascending=False), use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- DECORTICAGE TEMPOREL ---
                st.subheader("📉 Décorticage Temporel (Time Series)")
                time_granularity = st.radio("Sélectionnez la granularité temporelle :", ["Jour", "Semaine", "Mois"], horizontal=True)
                
                if time_granularity == "Jour":
                    time_col = '_date'
                elif time_granularity == "Semaine":
                    time_col = '_week'
                else:
                    time_col = '_month'

                # Agregation par temps
                time_df = am_df.groupby(time_col).agg(
                    Requests=('order id', 'count'),
                    GMV=('item total', 'sum'),
                    Delivered=('is_delivered', 'sum'),
                    Cancelled=('is_cancelled', 'sum'),
                    Automated=('is_auto', 'sum')
                ).reset_index()
                
                # Remplissage par 0 des erreurs de division
                time_df['AOV'] = (time_df['GMV'] / time_df['Requests']).fillna(0)
                time_df['Success Rate'] = (time_df['Delivered'] / time_df['Requests'] * 100).fillna(0)
                time_df['Cancel Rate'] = (time_df['Cancelled'] / time_df['Requests'] * 100).fillna(0)
                time_df['Automatisation'] = (time_df['Automated'] / time_df['Requests'] * 100).fillna(0)

                # Tracé des graphiques temporels
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    fig_gmv_time = px.line(time_df, x=time_col, y='GMV', title=f"Évolution GMV ({time_granularity})", markers=True, template="plotly_white", color_discrete_sequence=['#8E44AD'])
                    st.plotly_chart(fig_gmv_time, use_container_width=True)
                    
                    fig_succ_time = px.line(time_df, x=time_col, y='Success Rate', title=f"Success Rate (%) ({time_granularity})", markers=True, template="plotly_white", color_discrete_sequence=['#27AE60'])
                    fig_succ_time.update_yaxes(range=[0, 105])
                    st.plotly_chart(fig_succ_time, use_container_width=True)

                with col_t2:
                    fig_aov_time = px.line(time_df, x=time_col, y='AOV', title=f"Évolution AOV ({time_granularity})", markers=True, template="plotly_white", color_discrete_sequence=['#2980B9'])
                    st.plotly_chart(fig_aov_time, use_container_width=True)
                    
                    fig_canc_auto = px.line(time_df, x=time_col, y=['Cancel Rate', 'Automatisation'], title=f"Cancel Rate vs Automatisation ({time_granularity})", markers=True, template="plotly_white")
                    st.plotly_chart(fig_canc_auto, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour cet AM sur la période sélectionnée.")
