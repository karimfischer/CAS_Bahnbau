import pandas as pd
from Analysis_curve_tpf import * # Supposons que cette fonction retourne df1

# Charger df1
file_path = "report2025-01-08_13-28.csv"

# Options avancées pour charger un fichier efficacement
df = pd.read_csv(file_path,
    na_values=["N/A", "NA", "-", " "],    # Gérer les valeurs manquantes
    chunksize=None,                       # Lire tout d'un coup, ou par morceaux si fichier volumineux
    low_memory=False,                     # Accélère les fichiers complexes,
    encoding = 'latin-1'
)

df['Nom_Infrastructure_Horizontal geometry'] =\
    df['Nom_Infrastructure_Horizontal geometry'].apply(transformer_rationnels)

pal_csd = fun_groupe(df,'Palezieux - Chatel-St-Denis',10,600)

csd_mbv = fun_groupe(df,'Chatel-St-Denis - Montbovon',10,600)
pal_csd_riffel = output_riffel(pal_csd, 0.08)
csd_mbv_riffel = output_riffel(csd_mbv, 0.08)

df1 = pal_csd_riffel
# Convertir km_debut et km_fin en km
df1["km_debut"] = df1["km_debut"] / 1000
df1["km_fin"] = df1["km_fin"] / 1000

# Charger les segments supérieurs
segments_superieurs = pd.read_csv("segments_superieurs.csv")

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

        # Déterminer les nouveaux bornes du segment
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
result_df = pd.DataFrame(segments_resultants)

# Sauvegarder le résultat
result_df.to_csv("segments_superieurs_avec_rayon.csv", index=False)

print("Traitement terminé. Fichier enregistré sous segments_superieurs_avec_rayon.csv")

# Charger le fichier CSV
file_path = "segments_superieurs_avec_rayon.csv"
df = pd.read_csv(file_path)

#import pandas as pd

# Charger le fichier CSV
file_path = "segments_superieurs_avec_rayon.csv"
df = pd.read_csv(file_path)

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
df["element_standard"] = df.apply(attribuer_element_standard, axis=1)

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
df["frequence"] = df["element_standard"].map(frequence_mapping).fillna(0.15)

# Réserve usure:
#df["reserve_usure_min"] = df.merge(df1[['groupe','reserve_usure_min']],
                                 #  on="groupe", how='left')
#df1 = df1.reset_index()
df = df.merge(df1[['reserve_usure_min']], on='groupe', how='left')
df["annee"] = df['reserve_usure_min']/(0.08*df["frequence"])
df["annee"] = df["annee"].clip(lower=0)

# Enregistrer le fichier mis à jour
output_file = "segments_superieurs_avec_element_standard.csv"
df.to_csv(output_file, index=False)

print(f"Fichier enregistré : {output_file}")
