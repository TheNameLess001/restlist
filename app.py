import streamlit as st
import pandas as pd

st.set_page_config(page_title="Créations par mois", layout="centered")
st.title("📊 Nombre de restaurants créés par mois")

@st.cache_data
def load_and_process_data(file):
    # 1. Charger les données
    df = pd.read_csv(file, sep=';')
    
    # 2. Exclure les restaurants de test
    # On s'assure d'abord qu'il n'y a pas de valeurs vides dans la colonne 'Restaurant Name'
    # Ensuite on filtre pour exclure les lignes contenant le mot "test" (insensible à la casse)
    df = df.dropna(subset=['Restaurant Name'])
    df = df[~df['Restaurant Name'].str.lower().str.contains('test', na=False)]
    
    # 3. Traiter les dates
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Created At'])
    
    # Créer une colonne avec le mois et l'année (Format: AAAA-MM)
    df['Mois de Création'] = df['Created At'].dt.to_period('M').astype(str)
    
    # 4. Compter le nombre de créations par mois
    # On groupe par 'Mois de Création' et on compte le nombre de lignes (size)
    df_compte = df.groupby('Mois de Création').size().reset_index(name='Nombre de créations')
    
    # Trier du mois le plus récent au plus ancien
    df_compte = df_compte.sort_values(by='Mois de Création', ascending=False).reset_index(drop=True)
    
    return df_compte, df

# Zone d'upload du fichier
fichier_upload = st.file_uploader("Veuillez uploader votre fichier CSV", type=['csv'])

if fichier_upload is not None:
    try:
        # Appel de la fonction de traitement
        df_compte, df_complet = load_and_process_data(fichier_upload)
        
        st.success("Fichier traité avec succès ! (Les restaurants 'test' ont été ignorés)")
        
        st.subheader("Récapitulatif des créations mensuelles")
        
        # Affichage du tableau (st.dataframe ou st.table)
        st.dataframe(df_compte, use_container_width=True)
        
        # Optionnel : Afficher le total global
        total_restaurants = df_compte['Nombre de créations'].sum()
        st.info(f"**Total global des restaurants créés (hors tests) :** {total_restaurants}")
        
    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture du fichier : {e}")
else:
    st.info("En attente du fichier CSV...")
