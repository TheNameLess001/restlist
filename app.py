import streamlit as st
import pandas as pd
import io
import zipfile

st.set_page_config(page_title="Export Excel par Mois", layout="wide")
st.title("Générateur de fichiers Excel par Mois")

@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=';')
    # Conversion de la date au format Jour/Mois/Année
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Created At'])
    # Création d'une colonne simplifiée 'AAAA-MM' pour le regroupement
    df['Mois_Creation'] = df['Created At'].dt.to_period('M').astype(str)
    return df

# Zone d'upload du fichier
fichier_upload = st.file_uploader("1. Glissez-déposez votre fichier CSV ici", type=['csv'])

if fichier_upload is not None:
    try:
        df = load_data(fichier_upload)
        st.success(f"Fichier chargé avec succès ! {len(df)} restaurants trouvés.")
        
        st.subheader("2. Générer les exports")
        st.write("Cliquez sur le bouton ci-dessous pour générer un fichier ZIP contenant un fichier Excel (.xlsx) pour chaque mois.")

        # --- LOGIQUE DU BOUTON DE GÉNÉRATION COMPLET ---
        # On prépare le fichier ZIP en mémoire (sans écrire sur le disque)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # On groupe les restaurants par mois
            for mois, groupe in df.groupby('Mois_Creation'):
                # On nettoie la colonne technique avant l'export
                groupe_propre = groupe.drop(columns=['Mois_Creation'], errors='ignore')
                
                # Création du fichier Excel pour ce mois spécifique
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    groupe_propre.to_excel(writer, index=False, sheet_name=str(mois))
                
                # Ajout du fichier Excel dans le ZIP
                nom_fichier_excel = f"restaurants_{mois}.xlsx"
                zip_file.writestr(nom_fichier_excel, excel_buffer.getvalue())
        
        # Le bouton magique Streamlit
        st.download_button(
            label="⚙️ Générer et Télécharger le ZIP de tous les mois",
            data=zip_buffer.getvalue(),
            file_name="exports_restaurants_par_mois.zip",
            mime="application/zip",
            type="primary" # Met le bouton en couleur (bleu/rouge selon votre thème)
        )
        
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Veuillez d'abord uploader votre fichier CSV pour faire apparaître le bouton de génération.")
