import streamlit as st
import pandas as pd
import io

# Affichage en pleine largeur pour avoir un grand tableau
st.set_page_config(page_title="Détails des Restaurants", layout="wide")

# CSS pour agrandir la police du tableau
st.markdown("""
    <style>
    .stDataFrame div {
        font-size: 16pt !important;
    }
    .grand-titre {
        font-size: 20pt !important;
        font-weight: bold;
        color: #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍽️ Détails des Créations de Restaurants (12 Derniers Mois)")

@st.cache_data
def load_and_process_data(file):
    # 1. Lecture du fichier
    df = pd.read_csv(file, sep=';')
    
    # 2. Nettoyage : Exclure STRICTEMENT les "test"
    df = df.dropna(subset=['Restaurant Name'])
    df = df[~df['Restaurant Name'].str.lower().str.contains('test', na=False)]
    
    # 3. Traitement des dates pour le tri
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Created At'])
    
    # 4. Trier de la création la plus récente à la plus ancienne
    df = df.sort_values(by='Created At', ascending=False)
    
    # Création temporaire d'une colonne "Mois" juste pour isoler les 12 derniers mois
    df['Mois_temp'] = df['Created At'].dt.to_period('M').astype(str)
    mois_uniques = df['Mois_temp'].unique()
    12_derniers_mois = mois_uniques[:12] # On prend les 12 mois les plus récents
    
    # Garder uniquement le détail des restaurants de ces 12 mois
    df_details = df[df['Mois_temp'].isin(12_derniers_mois)].copy()
    
    # Supprimer la colonne temporaire pour avoir un fichier propre
    df_details = df_details.drop(columns=['Mois_temp'])
    
    # Remettre la date au format lisible JJ/MM/AAAA pour l'affichage et l'export
    df_details['Created At'] = df_details['Created At'].dt.strftime('%d/%m/%Y')
    
    return df_details

# Zone d'upload du fichier
fichier_upload = st.file_uploader("1. Chargez votre fichier CSV", type=['csv'])

if fichier_upload is not None:
    try:
        # Récupération de la liste détaillée
        df_details = load_and_process_data(fichier_upload)
        
        st.success(f"Fichier chargé ! Les données 'test' ont été retirées.")
        
        # --- AFFICHAGE DE LA LISTE DÉTAILLÉE (PLUS GRAND) ---
        st.markdown('<p class="grand-titre">📋 Liste détaillée des restaurants :</p>', unsafe_allow_html=True)
        
        # On affiche le détail complet dans un grand tableau (vous pouvez ajouter d'autres colonnes si besoin)
        colonnes_a_afficher = ['Id', 'Restaurant Name', 'Main City', 'Address', 'phone', 'Created At']
        st.dataframe(df_details[colonnes_a_afficher], use_container_width=True, height=500)
        
        st.divider()
        
        # --- EXPORTATION EXCEL DES DÉTAILS ---
        st.markdown('<p class="grand-titre">📥 Exporter le détail complet :</p>', unsafe_allow_html=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # On exporte toutes les colonnes du détail dans une seule feuille Excel
            df_details.to_excel(writer, index=False, sheet_name="Détails Restaurants")
        
        # Le bouton pour télécharger uniquement les détails
        st.download_button(
            label="🚀 Télécharger les détails (Fichier Excel)",
            data=buffer.getvalue(),
            file_name="details_restaurants_12_mois.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Veuillez charger le fichier CSV pour afficher la liste.")
