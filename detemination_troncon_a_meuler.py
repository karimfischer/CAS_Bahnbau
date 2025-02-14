import pandas as pd

# Recharger les données initiales
file_path = "StdE_Chatel_St_Denis_Montbovon.csv"
#file_path = "StdE_Palezieux_Chatel_St_Denis.csv"
df = pd.read_csv(file_path)

km_start_lim = 23
budget_max = 38700 # CHF

# Étape 1 : Filtrer les tronçons nécessitant un meulage (annee ≤ 1)
df_meulage = df[df["annee"] <= 1].copy()
#Uniquement Intyamon:
df_meulage = df[df["km_start"] >= km_start_lim].copy()

# Ajouter une colonne de longueur du tronçon à meuler en km
df_meulage["Longueur"] = df_meulage["km_end"] - df_meulage["km_start"]

# Trier par priorité de meulage (annee la plus négative en premier)
#df_meulage = df_meulage.sort_values(by="annee", ascending=True).reset_index(drop=True)
df_meulage = df_meulage.sort_values(by="km_start", ascending=True).reset_index(drop=True)

# Paramètres

cout_par_metre = 10  # CHF/m
metres_max_km = (budget_max / cout_par_metre) /1000  # Convertir en km
seuil_fusion = 0.19  # Distance max entre tronçons pour fusionner (en km)

# Étape 2 : Fusion des tronçons proches en maintenant la priorité sur "annee" min
troncons_fusionnes = []
troncon_actuel = df_meulage.iloc[0].copy()
id_troncons_selectionnes = []

for i in range(1, len(df_meulage)):
    km_start, km_end, annee, longueur = df_meulage.loc[i, ["km_start", "km_end", "annee", "Longueur"]]

    # Vérifier si le tronçon est proche du précédent
    if  km_start - troncon_actuel["km_end"] <= seuil_fusion and troncon_actuel["Longueur"] <= 0.85:
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

# Étape 3 : Sélectionner les tronçons en priorisant l'année min
df_fusionne = df_fusionne.sort_values(by="annee", ascending=True).reset_index(drop=True)
metres_selectionnes_km = 0
selection_finale = []

for i in range(len(df_fusionne)):
    if metres_selectionnes_km + df_fusionne.loc[i, "Longueur"] <= metres_max_km:
        selection_finale.append(df_fusionne.loc[i])
        metres_selectionnes_km += df_fusionne.loc[i, "Longueur"]
        id_troncons_selectionnes.append(i)

    else:
        break  # Stopper la sélection si on atteint la limite

if metres_selectionnes_km < metres_max_km:
    troncons_non_select = ~df_meulage.index.isin(id_troncons_selectionnes)
    index_non_selec = [i for i, val in enumerate(troncons_non_select) if val]
    non_select = df_meulage.iloc[index_non_selec]
    non_select_reste_km = non_select[non_select["Longueur"]<=(metres_max_km-metres_selectionnes_km)]
    dernier_troncon_indx = non_select_reste_km["Longueur"].idxmax()
    selection_finale.append(non_select.loc[dernier_troncon_indx])
    metres_selectionnes_km += non_select.loc[dernier_troncon_indx, "Longueur"]
    print("Il vous reste une réserve de:",
          ((metres_max_km - metres_selectionnes_km)*1000).round(0), "m.")

# Transformer en DataFrame final
df_selection_corrige = pd.DataFrame(selection_finale)
df_selection_corrige["Longueur"] = (df_selection_corrige["Longueur"]*1000).round(0)

# Affichage des résultats
print("km totaux selon budget:", metres_max_km)
print("km totaux du programme:", df_selection_corrige["Longueur"].sum().round(3)/1000, "km")
df_selection_corrige["km_start"] = df_selection_corrige["km_start"].round(3)
df_selection_corrige["km_end"] = df_selection_corrige["km_end"].round(3)
print(df_selection_corrige.sort_values("km_start"))

