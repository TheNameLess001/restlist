import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Filtre Restaurants", layout="wide")

# Titre de l'application
st.title("Filtre des Restaurants par Mois de Création")

# Fonction pour charger et préparer les données
@st.cache_data
def load_data(file):
    # Charger le fichier CSV uploadé (avec le séparateur point-virgule)
    df = pd.read_csv(file, sep=';')
    
    # Convertir la colonne 'Created At' en format datetime
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    
    # Créer une nouvelle colonne combinant l'Année et le Mois (ex: '2019-06')
    df['Mois de Création'] = df['Created At'].dt.to_period('M')
    
    return df

# 1. Ajout du composant pour uploader le fichier
fichier_upload = st.file_uploader("Choisissez votre fichier de restaurants (format CSV)", type=['csv'])

# 2. Si un fichier a été uploadé, on affiche le reste de l'application
if fichier_upload is not None:
    try:
        # Lire les données du fichier uploadé
        df = load_data(fichier_upload)
        
        # Vérifier s'il y a des dates valides
        if df['Mois de Création'].notna().any():
            # Obtenir la liste des mois uniques, triés de manière chronologique
            mois_disponibles = df['Mois de Création'].dropna().unique()
            mois_disponibles = sorted(mois_disponibles, reverse=True)
            
            # Formater les mois pour l'affichage
            mois_str = [str(m) for m in mois_disponibles]
            
            st.divider() # Ligne de séparation
            st.subheader("Filtrage des données")
            
            # Widget pour sélectionner le mois
            mois_selectionne_str = st.selectbox("Sélectionnez le mois de création (Année-Mois) :", ['Tous'] + mois_str)
            
            # Appliquer le filtre
            if mois_selectionne_str == 'Tous':
                df_filtre = df
                st.success(f"Affichage de **tous les restaurants** ({len(df_filtre)} résultats)")
            else:
                df_filtre = df[df['Mois de Création'].astype(str) == mois_selectionne_str]
                st.success(f"Affichage des restaurants créés en **{mois_selectionne_str}** ({len(df_filtre)} résultats)")
            
            # Colonnes que vous souhaitez afficher (vous pouvez modifier cette liste)
            colonnes_a_afficher = ['Id', 'Restaurant Name', 'Main City', 'Sub City', 'Created At', 'Status']
            
            # Afficher le tableau de données
            st.dataframe(df_filtre[colonnes_a_afficher], use_container_width=True)
            
        else:
            st.warning("Aucune date de création valide n'a pu être trouvée dans la colonne 'Created At'.")

    except Exception as e:
        st.error(f"Une erreur s'est produite lors de la lecture du fichier : {e}")

# Si aucun fichier n'est uploadé, on invite l'utilisateur à le faire
else:
    st.info("Veuillez uploader un fichier CSV pour commencer l'analyse.")
