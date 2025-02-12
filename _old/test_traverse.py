import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

# 🔹 Chargement du fichier CSV
df = pd.read_csv("../segments_avec_km.csv")  # Remplace avec ton fichier

# 🔹 Assurer que les types de traverses sont bien catégorisés
df["typ_trav"] = df["typ_trav"].astype(str).fillna("Inconnu")  # Remplit les valeurs manquantes

# 🔹 Inverser km_start et km_end si nécessaire
df[["km_start", "km_end"]] = df.apply(
    lambda row: (row["km_end"], row["km_start"]) if row["km_start"] > row["km_end"] else (row["km_start"], row["km_end"]),
    axis=1, result_type="expand"
)

# 🔹 Définition des couleurs et épaisseurs par type de traverse
color_map = {
    "Béton": "darkgray",
    "Bois": "brown",
    "Acier (bêches courtes)": "red",
    "Acier (bêches longues)": "pink",
    "Inconnu": "lightgray"  # 🔥 Couleur pour les tronçons sans info
}

width_map = {
    "Béton": 10,  # 🔥 Épaisseur épaisse
    "Bois": 8,
    "Acier (bêches courtes)": 6,
    "Acier (bêches longues)": 4,
    "Inconnu": 2  # 🔥 Tronçons sans info en plus fin
}

# 🔹 Trier les segments par km_start pour mieux gérer les superpositions
df = df.sort_values(by=["km_start"])

# 🔹 Liste des segments actifs pour éviter la superposition inutile
position_step = -0.5  # Espacement entre les niveaux
active_segments = []  # Garde une trace des segments actifs à chaque instant

# 🔹 Création du graphique
fig = go.Figure()

# 🔹 Itération sur chaque segment
for _, row in df.iterrows():
    km_start, km_end = row["km_start"], row["km_end"]
    traverse_type = row["typ_trav"] if row["typ_trav"] in color_map else "Inconnu"

    # 🔹 Déterminer la première position Y disponible sans chevauchement avec un type différent
    y_pos = 0
    while any(km_start < end and km_end > start and pos == y_pos and traverse_type != typ for start, end, pos, typ in active_segments):
        y_pos += position_step  # Décale vers le bas si un chevauchement est détecté avec un type différent

    # 🔹 Ajouter le segment aux actifs
    active_segments.append((km_start, km_end, y_pos, traverse_type))

    # 🔹 Déterminer si on doit afficher la légende (une seule fois par type)
    show_legend = bool(row["km_start"] == df["km_start"].min())

    # 🔹 Ajout du tronçon au graphique avec épaisseur et hauteur dynamique
    fig.add_trace(go.Scatter(
        x=[km_start, km_end],
        y=[y_pos, y_pos],  # 🔥 Position dynamique pour éviter la superposition inutile
        mode="lines",
        line=dict(color=color_map[traverse_type], width=width_map[traverse_type]),  # 🔥 Couleur + épaisseur spécifique
        name=traverse_type,
        legendgroup=traverse_type,  # Évite la duplication des légendes
        showlegend=show_legend  # ✅ Corrigé ici avec un bool explicite
    ))

# 🔹 Personnalisation du graphique
fig.update_layout(
    title="Répartition des types de traverses",
    xaxis_title="Kilométrage (km)",
    yaxis=dict(showticklabels=False, zeroline=False),  # Cache l'axe Y
    xaxis=dict(showgrid=True),  # Active la grille verticale
    showlegend=True
)

# 🔹 Création de l'application Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id="graph", figure=fig)
])

# 🔹 Exécuter l'application Dash
if __name__ == "__main__":
    app.run_server(debug=True)
