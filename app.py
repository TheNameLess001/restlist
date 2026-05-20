import streamlit as st
import pandas as pd
import io
import zipfile

# Configuration de la page
st.set_page_config(page_title="Dashboard Restaurants", layout="wide")

# Agrandir l'affichage du tableau
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

st.title("📊 Tableau de bord : Restaurants onboardés")

@st.cache_data
def process_data(file):
    df = pd.read_csv(file, sep=';')
    
    # 1. Élimination des restaurants "test"
    df = df.dropna(subset=['Restaurant Name'])
    df = df[~df['Restaurant Name'].str.lower().str.contains('test', na=False)]
    
    # 2. Formatage des dates
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Created At'])
    
    # Création de la colonne Mois pour le groupement
    df['Mois'] = df['Created At'].dt.to_period('M').astype(str)
    
    # 3. Calcul des chiffres par mois (pour le tableau d'affichage)
    df_chiffres = df.groupby('Mois').size().reset_index(name='Nombre de créations')
    df_chiffres = df_chiffres.sort_values(by='Mois', ascending=False).reset_index(drop=True)
    
    # Remettre la date au format lisible pour l'export Excel
    df['Created At'] = df['Created At'].dt.strftime('%d/%m/%Y')
    
    return df, df_chiffres

# Zone d'upload
fichier_upload = st.file_uploader("Chargez votre fichier CSV ici", type=['csv'])

if fichier_upload is not None:
    try:
        df_complet, df_chiffres = process_data(fichier_upload)
        
        st.success("✅ Fichier traité avec succès (les restaurants 'test' ont été exclus).")
        
        # --- PARTIE 1 : AFFICHAGE DES CHIFFRES PAR MOIS ---
        st.markdown('<p class="grand-titre">📈 Nombre de restaurants par mois :</p>', unsafe_allow_html=True)
        # Affichage du grand tableau des comptes
        st.dataframe(df_chiffres, use_container_width=True, height=400)
        
        st.divider()
        
        # --- PARTIE 2 : GÉNÉRATION DU FICHIER ZIP ---
        st.markdown('<p class="grand-titre">📥 Exporter le détail complet (Fichier ZIP) :</p>', unsafe_allow_html=True)
        st.write("Cliquez sur le bouton ci-dessous pour télécharger une archive ZIP contenant un fichier Excel par mois avec le détail de chaque restaurant signé.")
        
        # Création de l'archive ZIP en mémoire
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # On boucle sur chaque mois
            for mois, groupe in df_complet.groupby('Mois'):
                # On retire la colonne technique 'Mois' avant l'export
                groupe_export = groupe.drop(columns=['Mois'], errors='ignore')
                
                # Création du fichier Excel du mois en mémoire
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    groupe_export.to_excel(writer, index=False, sheet_name=str(mois))
                
                # Ajout de ce fichier Excel dans le dossier ZIP
                nom_fichier_excel = f"details_restaurants_{mois}.xlsx"
                zip_file.writestr(nom_fichier_excel, excel_buffer.getvalue())
        
        # Bouton pour télécharger le ZIP
        st.download_button(
            label="🚀 Télécharger le ZIP par mois",
            data=zip_buffer.getvalue(),
            file_name="details_restaurants_mensuels.zip",
            mime="application/zip",
            type="primary"
        )

    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture du fichier : {e}")
else:
    st.info("Veuillez charger le fichier CSV pour commencer.")
