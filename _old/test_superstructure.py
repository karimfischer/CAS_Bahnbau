import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

# 🔹 Chargement du fichier CSV
df = pd.read_csv("../segments_avec_km.csv")

# 🔹 Vérification et correction des inversions km_start/km_end
df[["km_start", "km_end"]] = df.apply(
    lambda row: (row["km_end"], row["km_start"]) if row["km_start"] > row["km_end"] else (row["km_start"], row["km_end"]),
    axis=1, result_type="expand"
)

# 🔹 Supprimer les tronçons > 20 km
df = df[(df["km_end"] - df["km_start"]) <= 20]

# 🔹 Remplacement des noms des rails pour la légende
df["typ_rail"] = df["typ_rail"].replace({
    "CFF I": "46 E1",
    "CFF IV": "54 E2",
    "Ri 60": "Ri 60",
    "UST 36": "UST 36"
})

# 🔹 Nouvelle palette de couleurs améliorée pour le contraste
category_settings = {
    "Traverse": {
        "offset": 0,
        "color_map": {
            "Béton": "#000000",  # Noir intense
            "Bois": "#A0522D",  # Marron clair
            "Acier (bêches courtes)": "#FF0000",  # Rouge vif
            "Acier (bêches longues)": "#C71585",  # Magenta foncé
        }
    },
    "Rail": {
        "offset": -0.5,
        "color_map": {
            "46 E1": "#007FFF",  # Bleu ciel intense
            "54 E2": "#228B22",  # Vert forêt
            "Ri 60": "#800080",  # Violet foncé
            "UST 36": "#D2691E",  # Orange brûlé
        }
    },
    "Acier": {
        "offset": -1,
        "color_map": {
            "R 260": "#00CED1",  # Cyan électrique
            "R 350 HT": "#8B0000",  # Rouge bordeaux
        }
    }
}

# 🔹 Création du graphique
fig = go.Figure()
legend_shown = set()
category_mapping = {"typ_trav": "Traverse", "typ_rail": "Rail", "qualite_acier": "Acier"}

# 🔹 Ajout des segments avec gestion des superpositions
for col, category in category_mapping.items():
    settings = category_settings[category]
    df_sorted = df.sort_values(by=["km_start"])

    active_segments = []  # Liste des segments placés

    for _, row in df_sorted.iterrows():
        km_start, km_end = row["km_start"], row["km_end"]
        category_value = row[col]

        if pd.isna(km_start) or pd.isna(km_end):
            continue

        y_base = settings["offset"]
        y_pos = y_base

        # 🔹 Gérer les superpositions en décalant légèrement les tronçons
        while any(km_start < end and km_end > start and pos == y_pos for start, end, pos in active_segments):
            y_pos -= 0.1  # Décalage pour afficher tous les tronçons

        active_segments.append((km_start, km_end, y_pos))

        # 🔹 Gérer la légende pour éviter les doublons
        show_legend = category_value not in legend_shown
        if show_legend:
            legend_shown.add(category_value)

        # 🔹 Ajout du segment au graphique
        fig.add_trace(go.Scatter(
            x=[km_start, km_end],
            y=[y_pos, y_pos],
            mode="lines",
            line=dict(color=settings["color_map"].get(category_value, "#808080"), width=3),
            name=category_value,
            showlegend=show_legend
        ))

# 🔹 Ajout des lignes pointillées pour séparer les catégories
separators = [-0.25, -0.75]
for sep in separators:
    fig.add_trace(go.Scatter(
        x=[df["km_start"].min(), df["km_end"].max()],
        y=[sep, sep],
        mode="lines",
        line=dict(color="gray", width=0.5, dash="dot"),
        showlegend=False
    ))

# 🔹 Ajout des titres des catégories (plus petits)
category_titles = {
    "Type de traverse": 0.15,
    "Profil du rail": -0.55,
    "Nuance d'acier": -1.05
}

for title, y_pos in category_titles.items():
    fig.add_annotation(
        x=0,
        y=y_pos,
        text=title,
        showarrow=False,
        xref="paper",
        yref="y",
        xanchor="left",
        font=dict(size=10, color="gray", family="Arial")
    )

# 🔹 Mise en page avec la légende sous le graphique
fig.update_layout(
    title=None,
    template="plotly_white",
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
        tickmode="auto",
        ticks="outside",
        ticklen=8
    ),
    yaxis=dict(
        showticklabels=False,
        zeroline=False,
        showgrid=False
    ),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.5,
        xanchor="center",
        x=0.5,
        title="Légende"
    ),
    margin=dict(l=10, r=50, t=20, b=120),  # Ajustement pour laisser la place à la légende
    plot_bgcolor="white",
    paper_bgcolor="white"
)

# 🔹 Initialisation de l'application Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id="graph-main", figure=fig, config={'scrollZoom': True},
              style={'height': '50vh', 'width': '100%', 'display': 'flex', 'justify-content': 'left'})
])

# 🔹 Lancement de l'application
if __name__ == '__main__':
    app.run_server(debug=True)