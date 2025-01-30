import pandas as pd
import numpy as np

def read_csv(file_path):
    df = pd.read_csv(file_path,
    na_values=["N/A", "NA", "-", " "],    # Gérer les valeurs manquantes
    chunksize=None,                       # Lire tout d'un coup, ou par morceaux si fichier volumineux
    low_memory=False,                     # Accélère les fichiers complexes,
    encoding = 'UTF8'
    )
    return df

df1 = read_csv('out2.csv')
df2 = read_csv('segments_avec_km.csv')

df1[['km_debut', 'km_fin']] = df1[['km_debut', 'km_fin']] / 1000
df2['pk_debut_corr'] = df2[['km_start', 'km_end']].min(axis=1)
df2['pk_fin_corr'] = df2[['km_start', 'km_end']].max(axis=1)
df2['typ_rail'] = df2['typ_rail'].replace({'CFF I': '46 E1', 'CFF IV': '54 E2'})

df2['length'] = df2['pk_fin_corr'] - df2['pk_debut_corr']

df2['interval'] = pd.IntervalIndex.from_arrays(df2['pk_debut_corr'],df2['pk_fin_corr'], closed='both')

# Fonction pour trouver les correspondances
def attribuer_parametres(row, df2):
    row_interval = pd.Interval(row['km_debut'], row['km_fin'], closed='both')
    mask = df2['interval'].apply(lambda x: x.overlaps(row_interval))
    matches = df2[mask]

    if not matches.empty:
        dominant_traverse = matches.loc[matches['length'].idxmax(), 'typ_trav']
        dominant_steel = matches.loc[matches['length'].idxmax(), 'qualite_acier']
        dominant_rail_profil = matches.loc[matches['length'].idxmax(), 'typ_rail']
        row['traverse'] = dominant_traverse
        row['acier'] = dominant_steel
        row['profil_rail'] = dominant_rail_profil
        row['param1'] = list(matches['typ_trav'])  # Liste des paramètres si plusieurs
        row['param2'] =list(matches['qualite_acier'])
        row['interval_left'] = list(matches['interval'].apply(lambda x: x.left))
        row['interval_right'] = list(matches['interval'].apply(lambda x: x.right))
        row['coord1'] = list(matches['interval'])
    else:
        row['param'] = None  # Aucun recouvrement

    return row

# Appliquer la fonction sur DF1
df1 = df1.apply(attribuer_parametres, axis=1, args=(df2,))
df1.to_csv('out3.csv')