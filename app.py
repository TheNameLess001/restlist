import streamlit as st
import pandas as pd

# Titre de l'application
st.title("Filtre des Restaurants par Mois de Création")

# Fonction pour charger les données avec mise en cache pour plus de performance
@st.cache_data
def load_data(file_path):
    # Charger le fichier CSV (avec le séparateur point-virgule)
    df = pd.read_csv(file_path, sep=';')
    
    # Convertir la colonne 'Created At' en format datetime (en gérant les erreurs éventuelles)
    # Le format attendu semble être jour/mois/année (ex: 30/6/2019)
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    
    # Créer une nouvelle colonne combinant l'Année et le Mois pour faciliter le filtrage (ex: '2019-06')
    df['Mois de Création'] = df['Created At'].dt.to_period('M')
    
    return df

# Chemin vers votre fichier (assurez-vous qu'il est dans le même dossier ou mettez le bon chemin)
FILE_PATH = 'restaurant-list-1778670885898.csv'

try:
    df = load_data(FILE_PATH)
    
    # Vérifier s'il y a des dates valides
    if df['Mois de Création'].notna().any():
        # Obtenir la liste des mois uniques, triés de manière chronologique
        mois_disponibles = df['Mois de Création'].dropna().unique()
        mois_disponibles = sorted(mois_disponibles, reverse=True)
        
        # Formater les mois pour l'affichage dans la liste déroulante
        mois_str = [str(m) for m in mois_disponibles]
        
        st.subheader("Filtrage")
        
        # Widget pour sélectionner le mois
        mois_selectionne_str = st.selectbox("Sélectionnez le mois de création (Année-Mois) :", ['Tous'] + mois_str)
        
        # Appliquer le filtre
        if mois_selectionne_str == 'Tous':
            df_filtre = df
            st.write(f"Affichage de **tous les restaurants** ({len(df_filtre)} résultats)")
        else:
            df_filtre = df[df['Mois de Création'].astype(str) == mois_selectionne_str]
            st.write(f"Affichage des restaurants créés en **{mois_selectionne_str}** ({len(df_filtre)} résultats)")
        
        # Nettoyer l'affichage : on peut masquer la colonne technique 'Mois de Création' si souhaité
        colonnes_a_afficher = ['Id', 'Restaurant Name', 'Main City', 'Created At', 'Status']
        # Si on veut afficher toutes les colonnes : 
        # colonnes_a_afficher = [col for col in df.columns if col != 'Mois de Création']
        
        st.dataframe(df_filtre[colonnes_a_afficher], use_container_width=True)
        
    else:
        st.warning("Aucune date de création valide n'a pu être trouvée dans la colonne 'Created At'.")

except FileNotFoundError:
    st.error(f"Le fichier '{FILE_PATH}' est introuvable. Veuillez vérifier le nom et l'emplacement du fichier.")
except Exception as e:
    st.error(f"Une erreur s'est produite : {e}")
