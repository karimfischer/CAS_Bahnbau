import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
import numpy as np
from scipy.stats import skew, kurtosis
import math

file_path = "report2025-01-08_13-28.csv"

# Options avancées pour charger un fichier efficacement
df = pd.read_csv(file_path,
    na_values=["N/A", "NA", "-", " "],    # Gérer les valeurs manquantes
    chunksize=None,                       # Lire tout d'un coup, ou par morceaux si fichier volumineux
    low_memory=False,                     # Accélère les fichiers complexes,
    encoding = 'latin-1'
)

def fun_groupe(df,ligne,r_min, r_max):
    df_filtre = df[(df['Nom_Infrastructure_Horizontal geometry'] >= r_min) &
    (df['Nom_Infrastructure_Horizontal geometry']<=r_max) &
    (df['Linie']==ligne)]
    df_filtre['groupe'] = (df_filtre['Nom_Infrastructure_Horizontal geometry'] != df_filtre['Nom_Infrastructure_Horizontal geometry'].shift()).cumsum()
    df_filtre['CAL Riffel 10-100 l'] =df_filtre['ATM Riffel 10-30 l']+df_filtre['ATM Riffel 30-100 l']
    df_filtre['CAL Riffel 30-300 l'] =df_filtre['ATM Riffel 30-100 l']+df_filtre['ATM Riffel 100-300 l']
    df_filtre['CAL Riffel 10-100 r'] = df_filtre['ATM Riffel 10-30 r'] + df_filtre['ATM Riffel 30-100 r']
    df_filtre['CAL Riffel 30-300 r'] = df_filtre['ATM Riffel 30-100 r'] + df_filtre['ATM Riffel 100-300 r']
    df_filtre['km_debut'] = df_filtre['von'].groupby(df_filtre['groupe']).transform('min')
    df_filtre['km_fin'] = df_filtre['bis'].groupby(df_filtre['groupe']).transform('max')
    df_filtre['rayon_courbe'] = df_filtre['Nom_Infrastructure_Horizontal geometry'].groupby(df_filtre['groupe']).transform('mean')
    df_filtre["long"] = df_filtre["bis"]-df_filtre["von"]
    #df_filtre = df_filtre.sort_values(by='von')
    return df_filtre

def boxplot_wavelength(df):
    fig = plt.subplots(2, 3, figsize = (12,6))
    ax1 = plt.subplot(2,3,1)
    medianprops = dict(color='r',
                          linewidth=0.75)
    boxprops = dict(facecolor='w', linewidth=0.5)
    whiskerprops = dict(linewidth=0.5)
    sns.boxplot(x='groupe', y='CAL Riffel 10-100 l', data=df,
                showfliers=False, medianprops = medianprops, boxprops = boxprops,
                whiskerprops=whiskerprops, capprops=whiskerprops, ax=ax1)
    plt.ylim(0, 0.3)
    plt.subplot(2, 3, 2)
    sns.boxplot(x='groupe', y='CAL Riffel 30-300 l', data=df, showfliers=False)
    plt.ylim(0, 0.3)
    plt.subplot(2, 3, 3)
    sns.boxplot(x='groupe', y='ATM Riffel 300-1000 l', data=df, showfliers=False)
    plt.ylim(0, 0.3)
    plt.subplot(2, 3, 4)
    sns.boxplot(x='groupe', y='CAL Riffel 10-100 r', data=df, showfliers=False)
    plt.ylim(0, 0.3)
    plt.subplot(2, 3, 5)
    sns.boxplot(x='groupe', y='CAL Riffel 30-300 r', data=df, showfliers=False)
    plt.ylim(0, 0.3)
    plt.subplot(2, 3, 6)
    sns.boxplot(x='groupe', y='ATM Riffel 300-1000 r', data=df, showfliers=False)
    plt.ylim(0, 0.3)

pal_csd = fun_groupe(df,'Palezieux - Chatel-St-Denis',10,600)
csd_mbv = fun_groupe(df,'Chatel-St-Denis - Montbovon',10,600)
reseau = [pal_csd, csd_mbv]
reseau = pd.concat(reseau)


#- Skewness par courbe:
# Calcul du skewness par groupe en filtrant les cas problématiques
def safe_skew(values):
    if len(values) > 1 and values.std() > 0:  # Vérifie qu'il y a au moins 2 valeurs et une variance non nulle
        return skew(values)
    else:
        return 0  # Retourne 0 comme valeur par défaut si le calcul n'est pas possible

def output_riffel(df, gw):
    riffel_type = ['CAL Riffel 10-100 l', 'CAL Riffel 10-100 r',
                   'CAL Riffel 30-300 l', 'CAL Riffel 30-300 r',
                   'ATM Riffel 300-1000 l', 'ATM Riffel 300-1000 r']
    df1 = df.dropna(subset=riffel_type[0]).groupby('groupe')[riffel_type[0]]
    skewness_par_courbe_10_100_l = df1.apply(safe_skew)
    kurtosis_par_courbe_10_100_l  = df1.apply(kurtosis)
    median_10_100_l = df1.median()
    mean_10_100_l = df1.mean()

    df2 = df.dropna(subset=riffel_type[1]).groupby('groupe')[riffel_type[1]]
    skewness_par_courbe_10_100_r = df2.apply(safe_skew)
    kurtosis_par_courbe_10_100_r = df2.apply(kurtosis)
    median_10_100_r = df2.median()
    mean_10_100_r = df2.mean()

    df3 = df.dropna(subset=riffel_type[2]).groupby('groupe')[riffel_type[2]]
    skewness_par_courbe_30_300_l = df3.apply(safe_skew)
    kurtosis_par_courbe_30_300_l = df3.apply(kurtosis)
    median_30_300_l = df3.median()
    mean_30_300_l = df3.mean()

    df4 = df.dropna(subset=riffel_type[3]).groupby('groupe')[riffel_type[3]]
    skewness_par_courbe_30_300_r = df4.apply(safe_skew)
    kurtosis_par_courbe_30_300_r = df4.apply(kurtosis)
    median_30_300_r = df4.median()
    mean_30_300_r = df4.mean()

    df5 = df.dropna(subset=riffel_type[4]).groupby('groupe')[riffel_type[4]]
    skewness_par_courbe_300_1000_l = df5.apply(safe_skew)
    kurtosis_par_courbe_300_1000_l = df5.apply(kurtosis)
    median_300_1000_l = df5.median()
    mean_300_1000_l = df5.mean()

    df6 = df.dropna(subset=riffel_type[5]).groupby('groupe')[riffel_type[5]]
    skewness_par_courbe_300_1000_r = df6.apply(safe_skew)
    kurtosis_par_courbe_300_1000_r = df6.apply(kurtosis)
    median_300_1000_r = df6.median()
    mean_300_1000_r = df6.mean()

    km_debut = df.groupby('groupe')['km_debut'].max()
    groupe = df.groupby('groupe')['groupe'].max()
    km_fin = df.groupby('groupe')['km_fin'].max()
    rayon = df.groupby('groupe')['rayon_courbe'].max()
    stat_par_courbe = {'groupe': groupe,
                       'Median_10_100_l': median_10_100_l,
                       'Mean_10_100_l': mean_10_100_l,
                       'Skewness_10_100_l': skewness_par_courbe_10_100_l,
                       'Kurtosis_10_100_l': kurtosis_par_courbe_10_100_l,
                       'Median_10_100_r': median_10_100_r,
                       'Mean_10_100_r': mean_10_100_r,
                       'Skewness_10_100_r': skewness_par_courbe_10_100_r,
                       'Kurtosis_10_100_r': kurtosis_par_courbe_10_100_r,
                       'Median_30_300_l': median_30_300_l,
                       'Mean_30_300_l': mean_30_300_l,
                       'Skewness_30_300_l': skewness_par_courbe_30_300_l,
                       'Kurtosis_30_300_l': kurtosis_par_courbe_30_300_l,
                       'Median_30_300_r': median_30_300_r,
                       'Mean_30_300_r': mean_30_300_r,
                       'Skewness_30_300_r': skewness_par_courbe_30_300_r,
                       'Kurtosis_30_300_r': kurtosis_par_courbe_30_300_r,
                       'Median_300_1000_l': median_300_1000_l,
                       'Mean_300_1000_l': mean_300_1000_l,
                       'Skewness_300_1000_l': skewness_par_courbe_300_1000_l,
                       'Kurtosis_300_1000_l': kurtosis_par_courbe_300_1000_l,
                       'Median_300_1000_r': median_300_1000_r,
                       'Mean_300_1000_r': mean_300_1000_r,
                       'Skewness_300_1000_r': skewness_par_courbe_300_1000_r,
                       'Kurtosis_300_1000_r': kurtosis_par_courbe_300_1000_r,
                       'km_debut': km_debut,
                       'km_fin': km_fin,
                       'rayon': rayon}
    stat_curve = pd.DataFrame.from_dict(stat_par_courbe)
    stat_curve['length'] = [x - y for x,y in zip(stat_curve['km_fin'],stat_curve['km_debut'])]
    stat_curve['max_l'] = stat_curve[['Median_10_100_l', 'Median_30_300_l',
                                      'Median_300_1000_l']].max(axis=1)
    stat_curve['max_r'] = stat_curve[['Median_10_100_r', 'Median_30_300_r',
                                      'Median_300_1000_r']].max(axis=1)
    stat_curve['cause_max_r'] = stat_curve[['Median_10_100_r', 'Median_30_300_r',
                                      'Median_300_1000_r']].idxmax(axis=1)
    stat_curve['cause_max_l'] = stat_curve[['Median_10_100_l', 'Median_30_300_l',
                                            'Median_300_1000_l']].idxmax(axis=1)
    stat_curve['max'] = stat_curve[['max_r', 'max_l']].max(axis=1)
    stat_curve['reserve_usure_l'] = [gw - x for x in stat_curve['max_l']]
    stat_curve['reserve_usure_r'] = [gw - x for x in stat_curve['max_r']]
    stat_curve['reserve_usure_min'] = stat_curve[['reserve_usure_l', 'reserve_usure_r']].min(axis=1)
    return stat_curve

pal_csd_riffel = output_riffel(pal_csd, 0.08)

#pal_csd_riffel = pal_csd_riffel[pal_csd_riffel['reserve_usure_min'] <= 0]

fig, ax = plt.subplots(1, 1, figsize=(12, 6))
ax.scatter(x=pal_csd_riffel['Skewness_30_300_r'], y= pal_csd_riffel['Kurtosis_30_300_r'],
           alpha=0.3, edgecolors='none')
ax.scatter(x=pal_csd_riffel['Skewness_10_100_r'], y= pal_csd_riffel['Kurtosis_10_100_r'],
           alpha=0.3, edgecolors='none')
ax.scatter(x=pal_csd_riffel['Skewness_300_1000_r'], y= pal_csd_riffel['Kurtosis_300_1000_r'],
           alpha=0.3, edgecolors='none')
plt.axhline(y = 1, color = 'k', linestyle = '-', linewidth=0.5)
plt.axhline(y = -1, color = 'k', linestyle = '-', linewidth=0.5)
plt.axvline(x = 0.5, color = 'k', linestyle = '-', linewidth=0.5)
plt.axvline(x = -0.5, color = 'k', linestyle = '-', linewidth=0.5)


##Boxplots par courbe pour évaluer la dispersion des mesures + éléments stat. d'analyse:
boxplot_wavelength(pal_csd)

fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))
ax1.hlines(pal_csd_riffel["Median_10_100_l"], pal_csd_riffel['km_debut'], pal_csd_riffel['km_fin'], color='g')
ax1.hlines(pal_csd_riffel["Median_10_100_r"], pal_csd_riffel['km_debut'], pal_csd_riffel['km_fin'], colors='r')
ax1.vlines([(g + h) / 2 for g, h in zip(pal_csd_riffel['km_debut'], pal_csd_riffel['km_fin'])], pal_csd_riffel["Median_10_100_l"], pal_csd_riffel["Median_10_100_r"], linewidth=0.5, colors='k', linestyles='dashed')
ax1.scatter(pal_csd_riffel['km_debut'], pal_csd_riffel["Median_10_100_l"] - pal_csd_riffel["Median_10_100_r"])
plt.axhline(y = pal_csd_riffel["Median_10_100_l"].median(), color ='g', linestyle ='-')
plt.axhline(y = pal_csd_riffel["Median_10_100_r"].median(), color ='r', linestyle ='-')
plt.axhline(y = 0.08, color = 'k', linestyle = '-')
plt.axhline(y = 0.1, color = 'k', linestyle = '-')

pal_csd_riffel.to_csv('out2.csv')

# Réserve d'usure
fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))
ax1.hlines(pal_csd_riffel['reserve_usure_min'], pal_csd_riffel['km_debut'],
          pal_csd_riffel['km_fin'],color ='g')
plt.axhline(y = 0.00, color = 'r', linestyle = '-')

## Analyse des courbes sur le réseau entier (par ligne):
fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))
sns.kdeplot(x="rayon_courbe",weights = "long",data = reseau,hue = "Linie", bw_adjust=2, ax=ax1)
ax2 = ax1.twinx()
sns.histplot(x="rayon_courbe", weights = "long", hue="Linie", data = reseau, ax=ax2, binwidth = 20, binrange=[0, 600])

s1 = skew(pal_csd["rayon_courbe"])
k1 = kurtosis(pal_csd["rayon_courbe"])
s2 = skew(csd_mbv["rayon_courbe"])
k2 = kurtosis(csd_mbv["rayon_courbe"])
print("s1 =", s1)
print("k1 =", k1)
print("s2 = ", s2)
print("k2 = ", k2)

plt.show()




