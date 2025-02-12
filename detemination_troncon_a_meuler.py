import pandas as pd

# Recharger les données initiales
file_path = "StdE_Chatel_St_Denis_Montbovon.csv"
df = pd.read_csv(file_path)

# Étape 1 : Filtrer les tronçons nécessitant un meulage (annee ≤ 1)
df_meulage = df[df["annee"] <= 1].copy()

# Ajouter une colonne de longueur du tronçon à meuler en km
df_meulage["Longueur"] = df_meulage["km_end"] - df_meulage["km_start"]

# Trier par priorité de meulage (annee la plus négative en premier)
df_meulage = df_meulage.sort_values(by="annee", ascending=True).reset_index(drop=True)

# Paramètres
budget_max = 50000  # CHF
cout_par_metre = 10  # CHF/m
metres_max_km = (budget_max // cout_par_metre) /1000  # Convertir en km
seuil_fusion = 0.2  # Distance max entre tronçons pour fusionner (en km)

# Étape 2 : Fusion des tronçons proches en maintenant la priorité sur "annee" min
troncons_fusionnes = []
troncon_actuel = df_meulage.iloc[0].copy()

for i in range(1, len(df_meulage)):
    km_start, km_end, annee, longueur = df_meulage.loc[i, ["km_start", "km_end", "annee", "Longueur"]]

    # Vérifier si le tronçon est proche du précédent
    if km_start - troncon_actuel["km_end"] <= seuil_fusion:
        troncon_actuel["km_end"] = max(troncon_actuel["km_end"], km_end)  # Étendre la fin du tronçon
        troncon_actuel["Longueur"] = troncon_actuel["km_end"] - troncon_actuel["km_start"]  # Recalculer la longueur
        troncon_actuel["annee"] = min(troncon_actuel["annee"], annee)  # Prendre la pire année (plus négative)
    else:
        # Ajouter le tronçon consolidé à la liste et commencer un nouveau
        troncons_fusionnes.append(troncon_actuel)
        troncon_actuel = df_meulage.iloc[i].copy()

# Ajouter le dernier tronçon
troncons_fusionnes.append(troncon_actuel)

# Transformer en DataFrame
df_fusionne = pd.DataFrame(troncons_fusionnes)

# Étape 3 : Sélectionner les tronçons jusqu'à 2000 mètres en priorisant l'année min
df_fusionne = df_fusionne.sort_values(by="annee").reset_index(drop=True)

metres_selectionnes_km = 0
selection_finale = []

for i in range(len(df_fusionne)):
    if metres_selectionnes_km + df_fusionne.loc[i, "Longueur"] <= metres_max_km:
        selection_finale.append(df_fusionne.loc[i])
        metres_selectionnes_km += df_fusionne.loc[i, "Longueur"]
    else:
        break  # Stopper la sélection si on atteint la limite

# Transformer en DataFrame final
df_selection_corrige = pd.DataFrame(selection_finale)

# Affichage des résultats
print(df_selection_corrige)
