import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
import numpy as np
from scipy.stats import skew, kurtosis
import math
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import plotly.tools as tls  # Outil pour conversion Matplotlib -> Plotly
import plotly.io as pio
import plotly.graph_objects as go
import json
import unicodedata
import re

file_path = "report2025-01-08_13-28.csv"

# Options avancées pour charger un fichier efficacement
df = pd.read_csv(file_path,
    na_values=["N/A", "NA", "-", " "],    # Gérer les valeurs manquantes
    chunksize=None,                       # Lire tout d'un coup, ou par morceaux si fichier volumineux
    low_memory=False,                     # Accélère les fichiers complexes,
    encoding = 'latin-1'
)

# Fonction pour transformer les nombres rationnels des rayons
def transformer_rationnels(x):
    if isinstance(x, (int, float)) and x != 0:
        # Vérifie si le nombre est rationnel sous forme décimale périodique
        if -1 < x < 1 and not np.isinf(1/x):
            return round(abs(1 / x))
    return x  # Garde les autres nombres inchangés

df['Nom_Infrastructure_Horizontal geometry'] =\
    df['Nom_Infrastructure_Horizontal geometry'].apply(transformer_rationnels)

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

def data_25_max(df_line):
    data_25cm_max_l = df_line[['CAL Riffel 10-100 l',
                             'CAL Riffel 30-300 l',
                             'ATM Riffel 300-1000 l'
                             ]].max(axis=1)

    data_25cm_max_r = df_line[['CAL Riffel 10-100 r',
                             'CAL Riffel 30-300 r',
                             'ATM Riffel 300-1000 r'
                             ]].max(axis=1)

    # Création des listes pour x et y avec gestion des trous
    x_values = []
    y_values_l = []
    y_values_r = []

    for i in range(len(df_line['von'])):
        x_values.append(df_line['von'].iloc[i])
        y_values_l.append(data_25cm_max_l.iloc[i])
        y_values_r.append(data_25cm_max_r.iloc[i])

        # Ajouter un trou si les données ne sont pas contiguës
        if i < len(df_line['von']) - 1 and df_line['von'].iloc[i + 1] != df_line['von'].iloc[i] + 0.25:
            x_values.append(None)
            y_values_l.append(None)
            y_values_r.append(None)

    # Création du graphe avec un seul scatter
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values_l,
        mode='lines',
        line=dict(width=0.75, color='palevioletred'),  # Réduction de l'épaisseur de la ligne
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values_r,
        mode='lines',
        line=dict(width=0.75, color='teal'),  # Réduction de l'épaisseur de la ligne
        showlegend=False
    ))

    # Ajout de la ligne rouge horizontale à y = 0.08
    fig.add_trace(go.Scatter(
        x=[df_line['von'].min(), df_line['von'].max()],
        y=[0.08, 0.08],
        mode='lines',
        line=dict(color='black', width=2),  # Ligne rouge continue
        name='Limite 0.08 mm'
    ))

    # Mise en page du graphique
    fig.update_layout(
        title="Valeur max. d'usure ondulatoire par pas de 25 cm",
        xaxis=dict(
            title="Point kilométrique",
            range=[df_line['von'].min(), df_line['von'].max()]
        ),
        yaxis=dict(
            title="Profondeur de l'usure ondulatoire max. [mm]",
            range=[min(min(data_25cm_max_l),min(data_25cm_max_r)),
                   max(max(data_25cm_max_l),max(data_25cm_max_r))]
        ),
        template="plotly_white"
    )
    # Sauvegarde du graphique en JSON
    line = df_line['Linie'].iloc[0]
    line = line = line.replace(" ", "_").replace("é", "e").replace("-", "_").replace("â","a")
    json_filename = f"data_25_cm_{line}.json"
    pio.write_json(fig, json_filename)
    return

def reserve_usure_par_courbe_plot(line_riffel):
    # Conversion en Plotly pour le graphe des réserves d'usure:
    # 🔹 Normalisation des couleurs
    # 🔹 Création du graphique avec Plotly
    fig = go.Figure()

    # Ajout des lignes verticales (vlines)
    for i, row in line_riffel.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['km_debut'], row['km_fin']],
            y=[row['reserve_usure_l'], row['reserve_usure_l']],
            mode="lines",
            line=dict(color='palevioletred', width=3),
            name=f"Ligne L {row['groupe']}",
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=[row['km_debut'], row['km_fin']],
            y=[row['reserve_usure_r'], row['reserve_usure_r']],
            mode="lines",
            line=dict(color='teal', width=3),
            name=f"Ligne R {row['groupe']}",
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=[(row['km_debut'] + row['km_fin']) / 2, (row['km_debut'] + row['km_fin']) / 2],
            y=[row['reserve_usure_l'], row['reserve_usure_r']],
            mode="lines",
            line=dict(color="black", width=1),
            name=f"VLine {row['groupe']}",
            showlegend=False
        ))

        # Ajout des annotations (text)
        fig.add_annotation(
            x=(row['km_debut'] + row["km_fin"]) / 2,  # Position X normale
            y=1.05,  # 1.05 pour être légèrement au-dessus du graphe
            xref="x",  # Référence par rapport à l'axe X (valeurs normales)
            yref="paper",  # Référence de l'axe Y par rapport au graph (0 = bas, 1 = haut)
            text=row['groupe'],  # Texte affiché
            showarrow=False,  # Pas de flèche
            font=dict(size=9),  # Taille de la police
            align="center",
            textangle=-45
        )

    # Ajout d'une ligne horizontale à y=0 (équivalent de `plt.axhline(y=0, ...)`)
    fig.add_trace(go.Scatter(
        x=[line_riffel['km_debut'].min(), line_riffel['km_fin'].max()],
        y=[0, 0],
        mode="lines",
        line=dict(color='black', width=2),
        name="Base Line",
        showlegend=False
    ))

    # Configuration du layout
    fig.update_layout(
        title="Réserve d'usure",
        xaxis_title="Kilométrage linéaire (km)",
        yaxis_title="Réserve d'usure",
        xaxis=dict(showgrid=True, range=[line_riffel['km_debut'].min(), line_riffel['km_fin'].max()]),
        yaxis=dict(showgrid=True, range=[-0.1, 0.1]),
        template="plotly_white",
    )

    # Sauvegarde du graphique en JSON
    line = line_riffel['Linie'].iloc[0]
    line = line.replace(" ", "_").replace("é", "e").replace("-", "_").replace("â","a")
    json_filename = f"reserve_usure_{line}.json"
    pio.write_json(fig, json_filename)
    return


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
    linie = df.groupby('groupe')['Linie'].first()
    stat_par_courbe = {'Linie': linie, 'groupe': groupe,
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

    stat_curve = stat_curve.replace('',np.nan)

    stat_curve.dropna(subset=['Median_10_100_l'], inplace=True)

    # Exemple de variable Linie
    Linie_retenue = stat_curve["Linie"].iloc[0]
    # Normaliser en ASCII et supprimer les accents
    Linie_cleaned = (unicodedata.normalize("NFKD", Linie_retenue).
                     encode("ascii", "ignore").decode("ascii"))
    # Remplacer espaces et tirets par des underscores
    Linie_cleaned = re.sub(r"[\s\-]+", "_", Linie_cleaned)
    # Construire le nom du fichier
    filename = f"ANALYSIS_RIFFEL_{Linie_cleaned}.csv"
    # Sauvegarde du DataFrame
    stat_curve.to_csv(filename, index=False)

    return stat_curve

data_25_max(pal_csd)
data_25_max(csd_mbv)
pal_csd_riffel = output_riffel(pal_csd, 0.08)
csd_mbv_riffel = output_riffel(csd_mbv, 0.08)
reserve_usure_par_courbe_plot(pal_csd_riffel)
reserve_usure_par_courbe_plot(csd_mbv_riffel)

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

fig1, ax1 = plt.subplots(1, 1, figsize=(12, 6))
norm = mcolors.Normalize(vmin=pal_csd_riffel['reserve_usure_min'].min(),
                         vmax=pal_csd_riffel['reserve_usure_min'].max())
cmap = plt.colormaps.get_cmap('RdYlGn')  # 'RdYlGn' donne un dégradé de rouge -> jaune -> vert
colors = [cmap(norm(v)) for v in pal_csd_riffel['reserve_usure_min']]
pos_courbe_moyenne = [(g + h) / 2 for g, h in zip(pal_csd_riffel['km_debut'],
                                        pal_csd_riffel['km_fin'])]
ax1.vlines(pos_courbe_moyenne, pal_csd_riffel["reserve_usure_l"],
           pal_csd_riffel["reserve_usure_r"], linewidth=0.7, colors='k', linestyles='-')
ax1.hlines(pal_csd_riffel["reserve_usure_l"],
           pal_csd_riffel['km_debut'], pal_csd_riffel['km_fin'], color='palevioletred', linewidth=3)
ax1.hlines(pal_csd_riffel["reserve_usure_r"], pal_csd_riffel['km_debut'],
           pal_csd_riffel['km_fin'], colors='teal', linewidth=3)
pal_csd_riffel.apply(lambda row: ax1.text(row['km_debut'],
                                          row['reserve_usure_r'], row['groupe']), axis=1)
plt.grid(axis='y', linestyle='-', alpha=0.7, linewidth=0.5)
plt.axhline(y = 0.0, color = 'k', linestyle = '-')

pal_csd_riffel.to_csv('out2.csv')

# Réserve d'usure plt
colors = [cmap(norm(v)) for v in pal_csd_riffel['reserve_usure_min']]
pal_csd_riffel['un']=1
fig2, ax1 = plt.subplots(1, 1, figsize=(30, 3))
plt.ylim(0.9, 1.1)
plt.grid(visible=1,axis='x')
ax1.hlines(pal_csd_riffel['un']+pal_csd_riffel['reserve_usure_l'], pal_csd_riffel['km_debut'],
          pal_csd_riffel['km_fin'],color =colors, linewidth=4.5)
#ax1.vlines(pal_csd_riffel['km_debut'],pal_csd_riffel['un']-0.01,pal_csd_riffel['un']+0.01,
 #          linewidth=0.5, color='k')
#ax1.vlines(pal_csd_riffel['km_fin'],pal_csd_riffel['un']-0.01,pal_csd_riffel['un']+0.01,
 #          linewidth=0.5, color='k')

fig3, ax3 = plt.subplots(1, 1, figsize=(30, 3))
plt.axhline(y = 1.00, color = 'k', linestyle = '-', linewidth=0.5)
sm = cm.ScalarMappable(norm=norm, cmap=cmap)
cbar = fig3.colorbar(sm, ax=ax3, label='Réserve d''usure')

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

## Barplots horizontaux:
# Paramètres pour le plot
bar_width = 0.2  # Largeur des barres

# Trier les courbes en fonction de la valeur minimale
pal_csd_riffel = pal_csd_riffel.sort_values(by='reserve_usure_min')
indices = np.arange(len(pal_csd_riffel))  # Positions des courbes après tri

# Couleurs pour chaque paramètre
param_a = pal_csd_riffel['reserve_usure_l'].values
param_b = pal_csd_riffel['reserve_usure_r'].values
courbes = pal_csd_riffel['groupe'].astype(str)

fig, ax = plt.subplots(figsize=(10, 12))

# Création des barres
ax.barh(indices - bar_width/2, param_a, bar_width, label='Réserve usure rail G', color='g')
ax.barh(indices + bar_width/2, param_b, bar_width, label='Réserve usure rail D', color='r')

# Ajouter les labels des courbes à l'axe Y
ax.set_yticks(indices)
ax.set_yticklabels(courbes)  # Numéros des courbes depuis le DataFrame

# Ajout des labels et légende
ax.set_xlabel('Réserve d''usure')
ax.set_title('Comparaison de paramètres pour courbes ferroviaires')
ax.legend()

# Améliorations visuelles
plt.gca().invert_yaxis()  # Pour afficher la première courbe en haut
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()

#plt.show()




