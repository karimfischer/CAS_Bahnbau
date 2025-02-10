import pandas as pd
import unicodedata
import re
import numpy as np
import matplotlib.pyplot as plt

df_pal_csd = pd.read_csv("ANALYSIS_RIFFEL_Palezieux_Chatel_St_Denis.csv")
df_csd_mbv = pd.read_csv("ANALYSIS_RIFFEL_Chatel_St_Denis_Montbovon.csv")
# Charger les segments supérieurs (valable pour les deux lignes)
segments_superieurs = pd.read_csv("segments_superieurs.csv")

def attribution_StdE_troncon(df1, segments_superieurs, gw):
    # Convertir km_debut et km_fin en km
    df1["km_debut"] = df1["km_debut"] / 1000
    df1["km_fin"] = df1["km_fin"] / 1000

    # Initialisation du dataframe résultant
    segments_resultants = []

    # Itérer sur chaque segment supérieur pour le croiser avec df1
    for _, segment in segments_superieurs.iterrows():
        km_start, km_end = segment["km_start"], segment["km_end"]
        segment_copy = segment.copy()

        # Trouver les tronçons de df1 qui intersectent ce segment
        intersecting_troncons = df1[(df1["km_fin"] > km_start) & (df1["km_debut"] < km_end)]

        for _, troncon in intersecting_troncons.iterrows():
            km_debut, km_fin, rayon, groupe = troncon["km_debut"], troncon["km_fin"], troncon["rayon"],troncon["groupe"]

            # Déterminer les nouvelles bornes du segment
            new_km_debut = max(km_debut, km_start)
            new_km_fin = min(km_fin, km_end)

            # Créer une copie du segment avec le rayon attribué
            new_segment = segment_copy.copy()
            new_segment["km_start"] = new_km_debut
            new_segment["km_end"] = new_km_fin
            new_segment["rayon"] = rayon
            new_segment["groupe"] = groupe

            segments_resultants.append(new_segment)

    # Transformer la liste en DataFrame
    df_rayon = pd.DataFrame(segments_resultants)


    # Fonction pour attribuer l'élément standard chiffré
    def attribuer_element_standard(row):
        A = 3  # Toujours 1
        B = 1  # Toujours 1

        # Déterminer C en fonction du rayon (colonne "rayon")
        if pd.isna(row["rayon"]):
            C = "F"  # Si valeur manquante, mettre F
        elif row["rayon"] > 600:
            C = 1
        elif 300 < row["rayon"] <= 600:
            C = 2
        elif 120 < row["rayon"] <= 300:
            C = 3
        elif 80 < row["rayon"] <= 120:
            C = 4
        else:
            C = 5

        # Déterminer D en fonction du type de traverse (colonne "typ_trav")
        if row["typ_trav"] == "Béton":
            D = 1
        elif row["typ_trav"] == "Bois":
            D = 3
        elif "Acier" in str(row["typ_trav"]):
            D = 4
        else:
            D = "F"  # Si valeur inconnue

        # Déterminer E en fonction du type de rail (colonne "typ_rail")
        if "46 E1" in str(row["typ_rail"]):
            E = 2
        elif "54 E2" in str(row["typ_rail"]):
            E = 1
        else:
            E = "E"

        # Déterminer F en fonction de la qualité d'acier (colonne "qualite_acier")
        if pd.isna(row["qualite_acier"]):
            F = "F"
        else:
            F = 1 if row["qualite_acier"] == "R 260" else 2 if row["qualite_acier"] == "R 350 HT" else 3

        # G et H sont toujours 1
        G = 1
        H = 1

        # Construire la chaîne ABCDEFGH
        return f"{A}{B}{C}{D}{E}{F}{G}{H}"

    # Appliquer la fonction à chaque ligne
    df_rayon["element_standard"] = df_rayon.apply(attribuer_element_standard, axis=1)

    # Dictionnaire des fréquences associées aux éléments standards
    frequence_mapping = {
        "31112211": 0.000, "31212211": 0.000, "31312211": 0.067, "31412211": 0.100, "31512211": 0.120,
        "31132211": 0.000, "31232211": 0.000, "31332211": 0.100, "31432211": 0.120, "31532211": 0.120,
        "31142211": 0.000, "31242211": 0.000, "31342211": 0.075, "31442211": 0.100, "31542211": 0.133,
        "31112111": 0.000, "31212111": 0.000, "31312111": 0.133, "31412111": 0.200, "31512111": 0.240,
        "31132111": 0.000, "31232111": 0.000, "31332111": 0.133, "31432111": 0.200, "31532111": 0.240,
        "31142111": 0.000, "31242111": 0.000, "31342111": 0.100, "31442111": 0.200, "31542111": 0.250,
    }

    # Ajouter la colonne de fréquence en fonction de l'élément standard
    df_rayon["frequence"] = df_rayon["element_standard"].map(frequence_mapping).fillna(0.14)
    # Réserve usure:
    #df["reserve_usure_min"] = df.merge(df1[['groupe','reserve_usure_min']],
                                 #  on="groupe", how='left')

    df_rayon = df_rayon.merge(df1[['groupe','reserve_usure_min']], on='groupe', how='left')
    df_rayon["annee"] = df_rayon['reserve_usure_min']/(gw*df_rayon["frequence"])
    #df_rayon["annee"] = df_rayon["annee"].clip(lower=0)
    df_rayon["km_a_meuler"] = np.where(df_rayon["annee"] < 1, abs(df_rayon["km_end"] - df_rayon["km_start"]), 0)
    sum_km_meuler = df_rayon['km_a_meuler'].sum()

    # HISTOGRAMME ETAT DU RESEAU:
    # Calculer la longueur de chaque segment
    df_rayon["longueur"] = df_rayon["km_end"] - df_rayon["km_start"]
    df_rayon = df_rayon[np.isfinite(df_rayon["annee"])]
    # Définir le nombre de bins (peut être ajusté selon les données)
    bins = [-np.inf, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, np.inf]
    labels = ["<-5", "-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", ">5"]
    df_rayon["bin"] = pd.cut(df_rayon["annee"], bins=bins, labels=labels, right=True)
    df_grouped = df_rayon.groupby("bin")["longueur"].sum()
    # Tracer l'histogramme pondéré
    plt.figure(figsize=(8, 5))
    plt.bar(df_grouped.index, df_grouped, color="blue", edgecolor="black", alpha=0.7)
    # Ajouter labels et titre
    plt.xlabel("Année")
    plt.ylabel("Longueur pondérée (km)")
    plt.title("Histogramme pondéré des années en fonction de la longueur des segments")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # FIGURE LINEAIRE OU MEULER?
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    df_rayon_filtered = df_rayon[df_rayon["annee"] < 1]
    df_rayon_filtered["zero"] = 0

    # Trier par km_start
    df_rayon_filtered = df_rayon_filtered.sort_values(by="km_start").reset_index(drop=True)
    # Liste pour stocker les nouvelles lignes
    new_rows = []
    # Vérifier la distance entre km_end d'une ligne et km_start de la suivante
    for i in range(len(df_rayon_filtered) - 1):
        row_current = df_rayon_filtered.iloc[i]
        row_next = df_rayon_filtered.iloc[i + 1]

        gap = row_next["km_start"] - row_current["km_end"]

        if gap < 0.15:  # Si l'écart est inférieur à 0.15 km (150m)
            new_row = {
                "km_start": row_current["km_end"],
                "km_end": row_next["km_start"],
                "zero": 0  # Même position Y
            }
            new_rows.append(new_row)

    # Ajouter les nouvelles lignes fictives au DataFrame
    df_fictive = pd.DataFrame(new_rows)
    df_rayon_extended = pd.concat([df_rayon_filtered, df_fictive]).sort_values(by="km_start").reset_index(drop=True)


    ax.hlines(df_rayon_extended['zero'],
              df_rayon_extended['km_start'],
              df_rayon_extended['km_end'],
              linewidth=2, color='black')

    ax.set_xlabel("km")
    ax.set_title("Tronçons à meuler")

    # Enregistrer le fichier mis à jour
    Linie_retenue = df1["Linie"].iloc[0]
    # Normaliser en ASCII et supprimer les accents
    Linie_cleaned = (unicodedata.normalize("NFKD", Linie_retenue).
                     encode("ascii", "ignore").decode("ascii"))
    # Remplacer espaces et tirets par des underscores
    Linie_cleaned = re.sub(r"[\s\-]+", "_", Linie_cleaned)
    # Construire le nom du fichier
    filename = f"StdE_{Linie_cleaned}.csv"
    df_rayon.to_csv(filename, index=False)
    print(f"Fichier enregistré : {filename}")
    return print(sum_km_meuler)

attribution_StdE_troncon(df_pal_csd, segments_superieurs, 0.08)
attribution_StdE_troncon(df_csd_mbv, segments_superieurs, 0.08)



plt.show()




