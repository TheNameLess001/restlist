import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Filtre & Export Restaurants", layout="wide")
st.title("Filtre & Exportation Excel par Mois")

@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=';')
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df['Mois de Création'] = df['Created At'].dt.to_period('M')
    return df

fichier_upload = st.file_uploader("Choisissez votre fichier de restaurants (format CSV)", type=['csv'])

if fichier_upload is not None:
    try:
        df = load_data(fichier_upload)
        
        if df['Mois de Création'].notna().any():
            mois_disponibles = sorted(df['Mois de Création'].dropna().unique(), reverse=True)
            mois_str = [str(m) for m in mois_disponibles]
            
            st.divider()
            
            # Sélection du mois
            mois_selectionne_str = st.selectbox("Sélectionnez le mois de création :", ['Tous'] + mois_str)
            
            if mois_selectionne_str == 'Tous':
                df_filtre = df
                nom_fichier_export = "tous_les_restaurants.xlsx"
            else:
                df_filtre = df[df['Mois de Création'].astype(str) == mois_selectionne_str]
                nom_fichier_export = f"restaurants_{mois_selectionne_str}.xlsx"
            
            # --- BLOC EXPORT EXCEL ---
            # Préparation du fichier Excel en mémoire tampon (Buffer)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # On enlève la colonne technique avant d'exporter
                df_exportable = df_filtre.drop(columns=['Mois de Création'], errors='ignore')
                df_exportable.to_excel(writer, index=False, sheet_name="Restaurants")
            
            # Bouton de téléchargement Streamlit
            st.download_button(
                label=f"📥 Télécharger la sélection en Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=nom_fichier_export,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            # --------------------------
            
            st.success(f"{len(df_filtre)} résultats trouvés.")
            
            colonnes_a_afficher = ['Id', 'Restaurant Name', 'Main City', 'Sub City', 'Created At', 'Status']
            st.dataframe(df_filtre[colonnes_a_afficher], use_container_width=True)
            
        else:
            st.warning("Aucune date valide trouvée.")
    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("Veuillez uploader un fichier CSV pour commencer.")
