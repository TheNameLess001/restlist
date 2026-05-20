import streamlit as st
import pandas as pd
import io

# Configuration de la page en mode LARGE pour agrandir l'affichage
st.set_page_config(page_title="Rapport 12 Mois", layout="wide")

# CSS personnalisé pour agrandir la police du tableau et des textes
st.markdown("""
    <style>
    /* Agrandir la police globale des tableaux Streamlit */
    .stDataFrame div {
        font-size: 16pt !important;
    }
    /* Style pour les sous-titres */
    .grand-titre {
        font-size: 20pt !important;
        font-weight: bold;
        color: #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Analyse des Créations de Restaurants (12 Derniers Mois)")

@st.cache_data
def load_and_process_data(file):
    # 1. Lecture du fichier
    df = pd.read_csv(file, sep=';')
    
    # 2. Nettoyage : Exclure STRICTEMENT les lignes contenant "test" (insensible à la casse)
    df = df.dropna(subset=['Restaurant Name'])
    df = df[~df['Restaurant Name'].str.lower().str.contains('test', na=False)]
    
    # 3. Traitement des dates
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Created At'])
    
    # Créer la colonne Année-Mois
    df['Mois de Création'] = df['Created At'].dt.to_period('M').astype(str)
    
    # 4. Calcul du résumé par mois
    df_summary = df.groupby('Mois de Création').size().reset_index(name='Nombre de créations')
    
    # Trier du plus récent au plus ancien
    df_summary = df_summary.sort_values(by='Mois de Création', ascending=False).reset_index(drop=True)
    
    # 5. Sélectionner uniquement les 12 derniers mois de data disponibles
    df_12_mois = df_summary.head(12)
    
    return df_12_mois, df

# Zone d'upload du fichier
fichier_upload = st.file_uploader("1. Glissez-déposez votre fichier CSV ici", type=['csv'])

if fichier_upload is not None:
    try:
        # Traitement des données
        df_12_mois, df_complet = load_and_process_data(fichier_upload)
        
        st.success("Fichier chargé ! Les restaurants de 'test' ont été automatiquement retirés.")
        
        # --- SECTION AFFICHAGE DU TABLEAU AGRANDI ---
        st.markdown('<p class="grand-titre">📈 Tableau récapitulatif des 12 derniers mois :</p>', unsafe_allow_html=True)
        
        # Affichage du tableau (il prend toute la largeur et l'écriture est agrandie via le CSS)
        st.dataframe(df_12_mois, use_container_width=True, height=460)
        
        st.divider()
        
        # --- SECTION EXPORTATION EXCEL ---
        st.markdown('<p class="grand-titre">📥 Exportation des données :</p>', unsafe_allow_html=True)
        
        # Filtrer le gros fichier pour ne garder que le détail des restaurants appartenant à ces 12 mois
        liste_12_mois = df_12_mois['Mois de Création'].tolist()
        df_details_12_mois = df_complet[df_complet['Mois de Création'].isin(liste_12_mois)].copy()
        # Supprimer la colonne technique avant l'export
        df_details_12_mois = df_details_12_mois.drop(columns=['Mois de Création'], errors='ignore')
        
        # Création du fichier Excel avec 2 onglets (Résumé + Détails)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_12_mois.to_excel(writer, index=False, sheet_name="Résumé 12 Mois")
            df_details_12_mois.to_excel(writer, index=False, sheet_name="Détails des Restaurants")
        
        # Bouton de téléchargement
        st.download_button(
            label="🚀 Télécharger le rapport Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="rapport_creations_12_mois.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Veuillez charger le fichier CSV pour afficher le tableau et le bouton de téléchargement.")
