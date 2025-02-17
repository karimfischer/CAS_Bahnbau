from dash import dcc, html, callback_context, dash_table
import plotly.io as pio
import dash.exceptions
import copy
import dash
import plotly.express as px
from dash.dependencies import Input, Output, State
import pandas as pd


# Taille des figures et style de la page
FIGURE_WIDTH = "75vw"  # Largeur des graphiques
FIGURE_HEIGHT = "30vh"  # Hauteur des graphiques
Y_AXIS_DOMAIN = [0.1, 0.9]  # Alignement parfait des axes Y
TABLE_WIDTH = FIGURE_WIDTH

PAGE_STYLE = {
    "font-family": "Arial, sans-serif"
}

# Fonction pour formater les figures
def format_figure(fig, xlabel_format=True):
    fig.update_layout(
        title=None,
        margin=dict(l=50, r=30, t=10, b=30),
        xaxis=dict(
            matches='x',
            showgrid=True, gridcolor='black', gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            title=None,
            tickformat=",d" if xlabel_format else None,
        ),
        yaxis=dict(
            showgrid=True, gridcolor='black', gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            domain=Y_AXIS_DOMAIN,
            title=None
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

# --- Création de l'application Dash ---
app = dash.Dash(__name__)

# Initialisation des données dans le Store
init_store_data = {
    "xaxis": None,  # Plage de zoom initialement vide
    "selected_line": "Palézieux - Châtel-St-Denis"
}

app.layout = html.Div([

    dcc.Store(id="range-store", data=init_store_data),

    html.Div([
        html.Label("Sélectionner une ligne ferroviaire:", style={"font-size": "14px"}),
        dcc.Dropdown(
            id="line-selector",
            options=[
                {"label": "Palézieux - Châtel-St-Denis", "value": "Palézieux - Châtel-St-Denis"},
                {"label": "Châtel-St-Denis - Montbovon", "value": "Châtel-St-Denis - Montbovon"}
            ],
            value="Palézieux - Châtel-St-Denis",
            clearable=False
        )
    ], style={'margin-bottom': '15px'}),

    html.Div([
        html.Div("Réserve d'usure [mm]", style={'width': '10vw', 'textAlign': 'right', 'fontSize': '12px',
                                                'paddingRight': '10px', 'paddingTop': '5px'}),
        dcc.Graph(id="graph-1", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH})
    ], style={'display': 'flex', 'align-items': 'flex-start'}),

    html.Div([
        html.Div("Profondeur max. usure ondulatoire [mm]",
                 style={'width': '10vw', 'textAlign': 'right', 'fontSize': '12px',
                        'paddingRight': '10px', 'paddingTop': '5px'}),
        dcc.Graph(id="graph-2", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH})
    ], style={'display': 'flex', 'align-items': 'flex-start'}),

    html.Hr(),

    html.H4("Données tabulaires et histogramme de la colonne selectionnée"),

    # ✅ Conteneur flex pour afficher la table et l'histogramme sur une seule ligne
    html.Div([
        html.Div(
            dash_table.DataTable(
                id="data-table",
                fixed_rows={'headers': True},
                style_table={"width": "100%", "overflowX": "auto", "overflowY": "auto", "maxHeight": "400px"},
                style_cell={"minWidth": "150px", "textAlign": "left"},
                style_header={
                "backgroundColor": "white",
                },
                sort_action="native",
                column_selectable="single",
                style_data_conditional=[
                    {"if": {"filter_query": "{annee} <= 0"}, "backgroundColor": "#C0392B", "color": "white"},
                    {"if": {"filter_query": "{annee} > 0 && {annee} < 1"}, "backgroundColor": "#F39C12",
                     "color": "black"},
                    {"if": {"filter_query": "{annee} >= 1"}, "backgroundColor": "#2ECC71", "color": "black"},
                ]
            ),
            style={'width': '50%', 'padding': '10px'}
        ),

        html.Div(
            dcc.Graph(id="histogram", style={'height': "30vh", 'width': "100%"}),
            style={'width': '50%', 'padding': '10px'}
        )
    ], style={'display': 'flex', 'justify-content': 'space-between'}),
    # ✅ Flexbox pour aligner la table et l'histogramme sur une ligne

], style=PAGE_STYLE)

# --- Callback pour appliquer le zoom lors d'un clic sur `km_start` ---
@app.callback(
    Output("range-store", "data",allow_duplicate=True),
    Input("data-table", "active_cell"),
    State("data-table", "data"),
    State("range-store", "data"),
    prevent_initial_call=True
)
def update_zoom_on_click(active_cell, table_data, current_store):
    if not active_cell or "column_id" not in active_cell:
        raise dash.exceptions.PreventUpdate

    col_selected = active_cell["column_id"]

    # Vérifie que la colonne sélectionnée est bien `km_start`
    if col_selected != "km_start":
        raise dash.exceptions.PreventUpdate

    row_index = active_cell["row"]  # Récupère l'index de la ligne cliquée

    # Vérifie que les données existent et que `km_start` et `km_end` sont présents
    if not table_data or row_index >= len(table_data):
        raise dash.exceptions.PreventUpdate

    km_start = table_data[row_index].get("km_start")

    km_end = table_data[row_index].get("km_end")

    if km_start is None or km_end is None:
        raise dash.exceptions.PreventUpdate

    # Met à jour la plage de zoom avec `km_start` et `km_end`
    new_store = current_store.copy()
    new_store["xaxis"] = [km_start*1000, km_end*1000]

    return new_store

# --- Callback pour sauvegarder le zoom et la ligne sélectionnée ---
@app.callback(
    Output("range-store", "data"),
    Input("graph-1", "relayoutData"),
    Input("graph-2", "relayoutData"),
    Input("line-selector", "value"),
    State("range-store", "data"),
    prevent_initial_call=True
)
def update_range(relayout1, relayout2, selected_line, current_store):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_prop = ctx.triggered[0]['prop_id'].split('.')[0]
    relayout = relayout1 if triggered_prop == "graph-1" else relayout2

    new_store = current_store.copy()
    updated = False

    if relayout:
        if "xaxis.range" in relayout:
            new_range_x = relayout["xaxis.range"]
        elif "xaxis.range[0]" in relayout and "xaxis.range[1]" in relayout:
            new_range_x = [relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]]
        else:
            new_range_x = None

        if new_range_x and new_range_x != current_store.get("xaxis"):
            new_store["xaxis"] = new_range_x
            updated = True

    if selected_line != current_store.get("selected_line"):
        new_store["selected_line"] = selected_line
        updated = True

    if updated:
        return new_store

    else:
        raise dash.exceptions.PreventUpdate


@app.callback(
    Output("graph-1", "figure"),
    Output("graph-2", "figure"),
    Input("line-selector", "value"),
    Input("range-store", "data"),
)
def update_graphs(selected_line, store_data):
    """
    Met à jour les figures lorsque l'utilisateur change de ligne
    et applique le zoom sauvegardé.
    """
    # Dictionnaire pour mapper les noms de lignes aux fichiers JSON
    file_map = {
        "Palézieux - Châtel-St-Denis": ("reserve_usure_Palezieux___Chatel_St_Denis.json",
                                        "data_25_cm_Palezieux___Chatel_St_Denis.json"),
        "Châtel-St-Denis - Montbovon": ("reserve_usure_Chatel_St_Denis___Montbovon.json",
                                        "data_25_cm_Chatel_St_Denis___Montbovon.json"),
    }

    # Vérifier si la ligne est valide
    if selected_line not in file_map:
        raise dash.exceptions.PreventUpdate

    file1, file2 = file_map[selected_line]

    try:
        fig1 = pio.read_json(file1)
        fig2 = pio.read_json(file2)
    except Exception as e:
        print(f"Erreur de chargement des fichiers JSON: {e}")
        raise dash.exceptions.PreventUpdate

    # Copie profonde pour éviter tout problème de cache
    fig1 = copy.deepcopy(fig1)
    fig2 = copy.deepcopy(fig2)

    # Appliquer la mise en forme
    fig1 = format_figure(fig1)
    fig2 = format_figure(fig2)

    # Appliquer le zoom précédent si disponible
    if store_data and "xaxis" in store_data and store_data["xaxis"]:
        fig1.update_layout(xaxis_range=store_data["xaxis"])
        fig2.update_layout(xaxis_range=store_data["xaxis"])  # Ajout explicite

    return fig1, fig2

# --- Callback pour charger le tableau ---
@app.callback(
    Output("data-table", "columns"),
    Output("data-table", "data"),
    Input("line-selector", "value")
)
def update_table(selected_line):
    file_map = {
        "Palézieux - Châtel-St-Denis": "StdE_Palezieux_Chatel_St_Denis.csv",
        "Châtel-St-Denis - Montbovon": "StdE_Chatel_St_Denis_Montbovon.csv",
    }

    if selected_line not in file_map:
        raise dash.exceptions.PreventUpdate

    file_path = file_map[selected_line]

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Erreur de chargement du fichier CSV: {e}")
        raise dash.exceptions.PreventUpdate

    df = df.sort_values(by="annee", ascending=True)

    df["km_start"] = df["km_start"].round(3)
    df["km_end"] = df["km_end"].round(3)
    df["reserve_usure_min"] = df["reserve_usure_min"].round(5)
    df["km_a_meuler"] = df["km_a_meuler"].round(3)
    df["annee"] = df["annee"].round(1)
    df["longueur"] = (df["longueur"]*1000).round(3)

    df = df.iloc[:, :-1]

    columns = [{"name": col, "id": col, "type": "numeric"} for col in df.columns]

    return columns, df.to_dict("records")

# Histogramme


# --- Callback pour afficher l'histogramme ---
@app.callback(
    Output("histogram", "figure"),
    Input("data-table", "active_cell"),
    State("data-table", "data"),
)
def update_histogram(active_cell, table_data):
    # ✅ Vérifie si `table_data` est vide
    if not table_data or len(table_data) == 0:
        df_empty = pd.DataFrame({"x": [], "y": []})
        return px.histogram(df_empty, x="x", y="y", title="Aucune donnée disponible").update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="black"),
            yaxis=dict(showgrid=True, gridcolor="black")
        )

    # ✅ Vérifie si `active_cell` est bien défini
    if not active_cell or "column_id" not in active_cell or active_cell["column_id"] is None:
        df_empty = pd.DataFrame({"x": [], "y": []})
        return px.histogram(df_empty, x="x", y="y", title="Sélectionnez une colonne").update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="black"),
            yaxis=dict(showgrid=True, gridcolor="black")
        )

    col_selected = active_cell["column_id"]

    # ✅ Vérifie que `col_selected` existe bien dans les données
    if col_selected not in table_data[0]:
        df_empty = pd.DataFrame({"x": [], "y": []})
        return px.histogram(df_empty, x="x", y="y", title=f"Histogramme de {col_selected} (Colonne non trouvée)").update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="black"),
            yaxis=dict(showgrid=True, gridcolor="black")
        )

    df = pd.DataFrame(table_data)

    # ✅ Vérifie que la colonne "longueur" existe
    if "longueur" not in df.columns:
        df_empty = pd.DataFrame({"x": [], "y": []})
        return px.histogram(df_empty, x="x", y="y", title=f"Histogramme de {col_selected} (Longueur non disponible)").update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="black"),
            yaxis=dict(showgrid=True, gridcolor="black")
        )

    # ✅ Création de l'histogramme avec style blanc
    fig = px.histogram(df, x=col_selected, y="longueur", histfunc="sum")
    fig.update_layout(
        height=300,
        plot_bgcolor="white",  # Fond blanc
        paper_bgcolor="white",
        font=dict(family="Arial", size=10, color="#333"),
        xaxis=dict(showgrid=True, gridcolor="black"),
        yaxis=dict(showgrid=True, gridcolor="black"),
        bargap=0.1
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

