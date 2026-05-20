import pandas as pd
import os
import sys

def exporter_tous_les_mois(chemin_fichier):
    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier '{chemin_fichier}' n'existe pas.")
        return

    print(f"1. Lecture du fichier : {chemin_fichier}...")
    # Charger la data avec le bon séparateur
    df = pd.read_csv(chemin_fichier, sep=';')
    
    # Convertir les dates
    df['Created At'] = pd.to_datetime(df['Created At'], format='%d/%m/%Y', errors='coerce')
    
    # Supprimer les lignes où la date est invalide pour éviter les erreurs
    df = df.dropna(subset=['Created At'])
    
    # Créer la colonne Année-Mois (ex: 2019-06)
    df['Mois_Creation'] = df['Created At'].dt.to_period('M')
    
    # Créer un dossier pour stocker tous les fichiers Excel
    dossier_sortie = "exports_excel_mois"
    os.makedirs(dossier_sortie, exist_ok=True)
    
    print("2. Génération des fichiers Excel par mois...")
    # Grouper par mois et exporter chaque groupe
    for mois, groupe in df.groupby('Mois_Creation'):
        # On retire la colonne technique avant d'exporter
        groupe_propre = groupe.drop(columns=['Mois_Creation'])
        
        nom_fichier = f"{dossier_sortie}/restaurants_{mois}.xlsx"
        
        # Export en Excel
        groupe_propre.to_excel(nom_fichier, index=False, sheet_name=str(mois))
        print(f"   [OK] {nom_fichier} ({len(groupe_propre)} restaurants)")
        
    print(f"\nTerminé ! Tous les fichiers sont disponibles dans le dossier : '{dossier_sortie}/'")

if __name__ == "__main__":
    # Permet de passer le nom du fichier en paramètre ou utilise le fichier par défaut
    fichier_cible = sys.argv[1] if len(sys.argv) > 1 else 'restaurant-list-1778670885898.csv'
    exporter_tous_les_mois(fichier_cible)
