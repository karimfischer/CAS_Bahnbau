import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import json
import pandas as pd


def enregistrer_troncons(df_sorted, category_settings, category_mapping, output_file="segments_superieurs.csv"):
    troncons_enregistres = []
    troncons_uniques = set()

    for col, category in category_mapping.items():
        settings = category_settings[category]
        active_segments = []

        for _, row in df_sorted.iterrows():
            km_start, km_end = row["km_start"], row["km_end"]
            category_value = row[col]

            if pd.isna(km_start) or pd.isna(km_end):
                continue

            y_base = settings["offset"]
            y_pos = y_base

            while any(km_start < end and km_end > start and pos == y_pos for start, end, pos in active_segments):
                y_pos -= 0.1

            active_segments.append((km_start, km_end, y_pos))

            if y_pos == y_base:  # Vérifier si le tronçon est en haut de la catégorie
                troncon_tuple = (km_start, km_end, row["typ_trav"], row["typ_rail"], row["qualite_acier"])
                if troncon_tuple not in troncons_uniques:
                    troncons_uniques.add(troncon_tuple)
                    troncons_enregistres.append({
                        "km_start": km_start,
                        "km_end": km_end,
                        "typ_trav": row["typ_trav"],
                        "typ_rail": row["typ_rail"],
                        "qualite_acier": row["qualite_acier"]
                    })

    df_troncons = pd.DataFrame(troncons_enregistres)
    df_troncons.to_csv(output_file, index=False)
    print(f"Tronçons enregistrés dans {output_file}")

# Chargement du fichier CSV
input_file = "segments_avec_km.csv"
df = pd.read_csv(input_file)

# Vérification et correction des inversions km_start/km_end
df[["km_start", "km_end"]] = df.apply(
    lambda row: (row["km_end"], row["km_start"]) if row["km_start"] > row["km_end"] else (row["km_start"], row["km_end"]),
    axis=1, result_type="expand"
)

# Supprimer les tronçons > 20 km
df = df[(df["km_end"] - df["km_start"] ) <= 20]

# Remplacement des noms des rails pour la légende
df["typ_rail"] = df["typ_rail"].replace({
    "CFF I": "46 E1",
    "CFF IV": "54 E2",
    "Ri 60": "Ri 60",
    "UST 36": "UST 36"
})

# Nouvelle palette de couleurs améliorée pour le contraste
category_settings = {
    "Traverse": {
        "offset": 0,
        "color_map": {
            "Béton": "#000000",
            "Bois": "#A0522D",
            "Acier (bêches courtes)": "#FF0000",
            "Acier (bêches longues)": "#C71585",
        }
    },
    "Rail": {
        "offset": -2,
        "color_map": {
            "46 E1": "#007FFF",
            "54 E2": "#228B22",
            "Ri 60": "#800080",
            "UST 36": "#D2691E",
        }
    },
    "Acier": {
        "offset": -4,
        "color_map": {
            "R 260": "#00CED1",
            "R 350 HT": "#8B0000",
        }
    }
}

# Trier les données par km_start
df_sorted = df.sort_values(by=["km_start", "km_end"])

# Création du graphique avec cadre noir, lignes pointillées et légende sous la figure
fig = go.Figure()
legend_shown = set()
category_mapping = {"typ_trav": "Traverse", "typ_rail": "Rail", "qualite_acier": "Acier"}

for col, category in category_mapping.items():
    settings = category_settings[category]
    df_sorted = df.sort_values(by=["km_start"])
    active_segments = []

    for _, row in df_sorted.iterrows():
        km_start, km_end = row["km_start"], row["km_end"]
        category_value = row[col]

        if pd.isna(km_start) or pd.isna(km_end):
            continue

        y_base = settings["offset"]
        y_pos = y_base

        while any(km_start < end and km_end > start and pos == y_pos for start, end, pos in active_segments):
            y_pos -= 0.1

        active_segments.append((km_start, km_end, y_pos))

        show_legend = category_value not in legend_shown
        if show_legend:
            legend_shown.add(category_value)

        fig.add_trace(go.Scatter(
            x=[km_start, km_end],
            y=[y_pos, y_pos],
            mode="lines",
            line=dict(color=settings["color_map"].get(category_value, "#808080"), width=3),
            name=category_value,
            showlegend=show_legend
        ))

# Ajout des lignes pointillées pour séparer les catégories et rendre les titres toujours visibles
separators = [-1, -3]
category_titles = {"Type de traverse": 0.5, "Type de rail": -1.5, "Nuance d'acier": -3.5}
for sep in separators:
    fig.add_trace(go.Scatter(
        x=[df["km_start"].min(), df["km_end"].max()],
        y=[sep, sep],
        mode="lines",
        line=dict(color="gray", width=0.5, dash="dot"),
        showlegend=False
    ))

for title, y_pos in category_titles.items():
    fig.add_annotation(
        x=0.5,
        y=y_pos,
        text=title,
        showarrow=False,
        xref="paper",
        yref="y",
        xanchor="center",
        font=dict(size=10, color="black", family="Arial"),
        bgcolor="white"
    )

# Mise en page du graphique restaurée avec cadre noir et légende plus proche
fig.update_layout(
    xaxis=dict(
        title="Kilométrage (km)",
        side="top",
        showgrid=True,
        zeroline=False,
        gridcolor="black",
        gridwidth=0.4,
        showline=True,
        linewidth=1,
        linecolor="black",
        ticks="outside",
        ticklen=8
    ),
    yaxis=dict(
        showticklabels=False,
        zeroline=False,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="black"
    ),
    height=360,
    margin=dict(l=50, r=50, t=20, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5
    )
)

# Enregistrement de la figure en JSON
output_json = "superstructure.json"
with open(output_json, "w") as f:
    json.dump(fig.to_plotly_json(), f)
print(f"Graphique enregistré en JSON : {output_json}")

enregistrer_troncons(df_sorted, category_settings, category_mapping)

# Initialisation de l'application Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Graph(id="graph-main", figure=fig, config={'scrollZoom': True})
])

# Lancement de l'application
if __name__ == '__main__':
    app.run_server(debug=True)
