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
TABLE_WIDTH = FIGURE_WIDTH

PAGE_STYLE = {
    "margin-right": "2rem",
    "padding-left": "18rem",
    "display":"inline-block",

}

# Fonction pour formater les figures
def format_figure(fig, sel_line):
    if sel_line == "Palézieux - Châtel-St-Denis":
        range = [90000, 96700]
    elif sel_line == "Châtel-St-Denis - Montbovon":
        range = [0, 37000]

    fig.update_layout(
        title=None,
        margin=dict(l=70, r=20, t=5, b=5),
        font=dict(size=12),
        #yaxis_range=[-0.1, 0.5],
        xaxis=dict(
            matches='x',
            showgrid=True, gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            color="black",
            zeroline=False,
            range = range
        ),
        yaxis=dict(
            showgrid=True, gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            #fixedrange=False,
            color="black",
            zeroline=False,
            autorangeoptions_clipmax=0.5,
            automargin=True
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        #legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

# --- Création de l'application Dash ---
app = dash.Dash(__name__)

# Initialisation des données dans le Store
init_store_data = {
    "xaxis": None,  # Plage de zoom initialement vide
    "selected_line": "Palézieux - Châtel-St-Denis"
}


# Ajout des cartes en haut du layout
info_cards = html.Div([
    html.Div([
        html.Div("Valeur limite dépassée", style={"font-size": "12px", "color": "firebrick", "text-align": "center"}),
        html.Div([
            html.Span(id="km-this-year", style={"font-size": "28px", "font-weight": "bold", "color": "firebrick"}),
            html.Span("km", style={"font-size": "14px", "color": "firebrick", "margin-left": "3px", "font-weight": "bold"}),
            html.Span("❘", style={"font-size": "14px", "color": "firebrick", "margin-left": "3px"}),
            html.Span(id="percent1", style={"font-size": "14px", "color": "firebrick", "margin-left": "3px"})

        ])
    ], style={
        "background-color": "mistyrose",  # Fond foncé
        "color": "white",
        "padding": "15px",
        "border-radius": "8px",  # Coins légèrement arrondis
        "width": "25%",
        "text-align": "center",
        "box-shadow": "1px 1px 4px rgba(0, 0, 0, 0.2)",  # Ombre discrète
        "border-left": "10px solid firebrick",  # Trait coloré
        "margin": "5px"  # Espacement réduit
    }),

    html.Div([
        html.Div("Valeur limite bientôt dépassée (< 1 an)", style={"font-size": "12px", "color": "darkorange"}),
        html.Div([
            html.Span(id="km-next-year", style={"font-size": "28px", "font-weight": "bold", "color": "darkorange"}),
            html.Span("km",
                      style={"font-size": "14px", "color": "darkorange", "margin-left": "3px", "font-weight": "bold"}),
            html.Span("❘", style={"font-size": "14px", "color": "darkorange", "margin-left": "3px"}),
            html.Span(id="percent2", style={"font-size": "14px", "color": "darkorange", "margin-left": "3px"})
        ])
    ], style={
        "background-color": "papayawhip",
        "color": "white",
        "padding": "15px",
        "border-radius": "8px",
        "width": "25%",
        "text-align": "center",
        "box-shadow": "1px 1px 4px rgba(0, 0, 0, 0.2)",
        "border-left": "10px solid darkorange",
        "margin": "5px"
    }),

    html.Div([
        html.Div("Sans besoin de meulage", style={"font-size": "12px", "color": "darkolivegreen"}),
        html.Div([
            html.Span(id="km-no-grinding",
                      style={"font-size": "28px", "font-weight": "bold", "color": "darkolivegreen"}),
            html.Span("km",
                      style={"font-size": "14px", "color": "darkolivegreen", "margin-left": "3px", "font-weight": "bold"}),
            html.Span("❘", style={"font-size": "14px", "color": "darkolivegreen", "margin-left": "3px"}),
            html.Span(id="percent3", style={"font-size": "14px", "color": "darkolivegreen", "margin-left": "3px"})
        ])
    ], style={
        "background-color": "honeydew",
        "color": "white",
        "padding": "15px",
        "border-radius": "8px",
        "width": "25%",
        "text-align": "center",
        "box-shadow": "1px 1px 4px rgba(0, 0, 0, 0.2)",
        "border-left": "10px solid darkolivegreen",
        "margin": "5px"
    })
], style={"display": "flex", "justify-content": "center", "gap": "5px", "margin-bottom": "5px"})


main_layout = html.Div([



    dcc.Store(id="range-store", data=init_store_data),
    html.H3("Besoin en meulage sur la ligne",
            style={'background-color': "#DADADA", 'padding': '2px'}),

    info_cards,

    html.Div([
        html.Div(
            dash_table.DataTable(
                id="data-table",
                fixed_rows={'headers': True},
                style_table={"width": "96%", "overflowX": "auto", "overflowY": "auto", "maxHeight": "200px"},
                style_cell={'padding': '1px', 'textAlign': 'left', 'fontSize': 10,
                            'font-family': 'sans-serif', 'minWidth': '60px'},
                style_header={
                    "backgroundColor": "#DADADA", "color": "black", 'fontWeight': 'bold',
                    'padding': '2px', 'whiteSpace': 'normal', 'fontSize': 10,
                },

                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                selected_columns=["annee"],
                style_data_conditional=[
                    {"if": {"filter_query": "{annee} <= 0"}, "backgroundColor": "mistyrose", "color": "firebrick"},
                    {"if": {"filter_query": "{annee} > 0 && {annee} < 1"}, "backgroundColor": "papayawhip",
                     "color": "darkorange"},
                    {"if": {"filter_query": "{annee} >= 1"}, "backgroundColor": "honeydew", "color": "darkolivegreen"},
                ]
            ),

            style={'width': '100%', 'padding': '10px'}
        ),

        html.Div(
            dcc.Graph(id="histogram", style={'width': "100%"}),
            style={'width': '48%', 'padding-top': '20px'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'flex-direction': 'column'}),

    html.Div([
        html.H3("Graphiques d'analyse linéaire",style={'background-color':"#DADADA", 'padding': '2px'}),
        html.Div("Réserve d'usure [mm]", style={"color": "black", "font-weight": "bold", "padding-bottom": "10px"}),
        html.Div("Graphique d'analyse représentant la réserve d'usure médiane, pour chaque courbe considérée, pour le rail droite (gris clair) et le rail gauche (gris foncé). "
                 "La réserve d'usure médiane est calculée par rapport à la valeur limite définie à 0.08 mm de profondeur: une valeur négative signifie que la valeur limite est dépassée pour le tronçon concerné et que des travaux de meulage sont donc nécessaires. "
                 " Un tronçon est défini dès lors qu'un changement de rayon de courbure intervient sur la ligne."
                 "La valeur présentée est toujours la valeur maximale en considérant les deux plages de fréquences (10 à 100 mm et 30 à 300 mm).",
                 style={"padding-bottom": "15px", 'fontSize':12}),
        dcc.Graph(id="graph-1", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH})
    ]),

    html.Div([
        html.Div("Profondeur max. usure ondulatoire [mm]", style={"color": "black", "font-weight": "bold"}),
        dcc.Graph(id="graph-2", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH})
    ]),





    html.H3("Recommandation automatique des tronçons à meuler",
            style={'background-color': "#DADADA", 'padding': '2px'}),

    html.Div(
            dash_table.DataTable(
                id="table-meulage",
                fixed_rows={'headers': True},
                style_table={"width": "50%", "overflowX": "auto", "overflowY": "auto", "maxHeight": "190px"},
                style_cell={'padding': '5px', 'textAlign': 'left', 'fontSize':10, 'font-family':'sans-serif'},
                style_header={
                "backgroundColor": "#DADADA", "color": "black",
                    'fontWeight': 'bold', 'padding': '5px',
                },
                sort_action="native",
                column_selectable="single",

            ),
            style={'width': '90%', 'padding': '10px'}
    ),

], style=PAGE_STYLE)

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "15rem",
    "padding": "2rem 1rem",
    "background-color": "#DADADA",
    "display":"inline-block",
    "color": "black"
}

sidebar = html.Div(children = [
            html.H2("Meulage VM", className="display-4"),
            html.P(
                "Outil d'aide à la décision pour définir les tronçons à meuler sur le réseau TPF à voie métrique.", className="lead"
            ),
            html.Div("Sélectionner une ligne ferroviaire", style={'padding-top': '15px', 'padding-bottom': '5px', "font-weight": "bold", "font-size": "10pt"}),
            dcc.Dropdown(
                id="line-selector",
                options=[
                    {"label": "Palézieux - Châtel-St-Denis", "value": "Palézieux - Châtel-St-Denis"},
                    {"label": "Châtel-St-Denis - Montbovon", "value": "Châtel-St-Denis - Montbovon"}
                ],
                value="Palézieux - Châtel-St-Denis",
                style={'width': '100%', 'padding': '0px', 'font-family': 'sans-serif', 'font-size': '10pt', 'border': '0px', 'border-radius': '5px'},
                clearable=False
            ),
            html.Div("Budget pour la ligne [CHF/an]", style={'padding-top': '15px', 'padding-bottom': '5px', "font-weight": "bold", "font-size": "10pt"}),
            dcc.Input(
                id="budget-input",
                value=50000,
                type="number",
                min=0,
                max=1000000,
                step=1,
                style={'width': '92%', 'padding': '9px', 'font-family': 'sans-serif', 'font-size': '10pt','border': '0px', 'border-radius': '5px'},
                    ),


            html.H3("Model"
            ),
            html.P(
                "This project uses a Random Forest Classifier to predict heart failure based on 12 independent variables.", className="lead"
            ),

            html.H3("Code"
            ),
            html.P(
                "The complete code for this project is available on github.", className="lead"
            ),


        ], style=SIDEBAR_STYLE
    )


app.layout = html.Div(children = [
    sidebar,
    html.Div([
        main_layout
     ])
], style={'backgroundColor':'white', "font-family": "Arial, sans-serif",
    "top": 0,
    "left": 0,
    "bottom": 0})

# --- Callback pour appliquer le zoom lors d'un clic sur `km_start` ---
@app.callback(
    Output("range-store", "data",allow_duplicate=True),
    Input("data-table", "active_cell"),
    State("data-table", "derived_virtual_data"),
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
    fig1 = format_figure(fig1, selected_line)
    fig2 = format_figure(fig2, selected_line)

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

    df = df.iloc[:, [0,1,2,3,4,5,6,7,8,9,10,12]]

    columns = [{"name": col, "id": col,  "deletable": True, "selectable": True} for col in df.columns]
    columns[0]["name"] = "km début"
    columns[1]["name"] = "km fin"
    columns[2]["name"] = "Traverse"
    columns[3]["name"] = "Rail"
    columns[4]["name"] = "Acier"
    columns[5]["name"] = "Rayon [m]"
    columns[6]["name"] = "N° courbe"
    columns[7]["name"] = "Elément standard"
    columns[8]["name"] = "Fréquence [1/an]"
    columns[9]["name"] = "Réserve usure min [mm]"
    columns[10]["name"] = "Année [an]"
    columns[11]["name"] = "Longueur [m]"

    return columns, df.to_dict("records")


# Histogramme
# --- Callback pour afficher l'histogramme ---
@app.callback(
    Output("histogram", "figure"),
    Input("data-table", "selected_columns"),
    Input("data-table", "data"),
)
def update_histogram(col_selected, table_data):
    df = pd.DataFrame(table_data)

    # ✅ Création de l'histogramme avec style blanc
    base_labels = {
        "km_start": "Point km du début de tronçon",
        "km_end": "Point km de fin de tronçon",
        "typ_rail": "Profil de rail",
        "typ_trav": "Type de traverse",
        "qualite_acier": "Nuance d'acier",
        "rayon": "Rayon",
        "groupe": "ID de la courbe",
        "element_standard": "Elément standard",
        "frequence": "Fréquence théorique du meulage [1/an]",
        "reserve_usure_min": "Réserve min. d'usure [mm]",
        "annee": "Temps jusqu'au prochain meulage [an]",
        "longueur": "Longueur du tronçon [m]"
    }
    fig = px.histogram(df, x=col_selected, y="longueur", histfunc="sum",
                        text_auto='.2s',
                       labels={"value":base_labels.get(col_selected[0],col_selected[0])})
    fig.update_layout(
        height=200,
        plot_bgcolor="white",  # Fond blanc
        paper_bgcolor="white",
        font=dict(family="Arial", size=12, color="black"),
        xaxis=dict(showgrid=True, gridcolor="lightgray"),
        yaxis=dict(showgrid=True, gridcolor="lightgray"),
        bargap=0.1,
        barcornerradius=5,
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        yaxis_title="Longueur cumulée [m]",
        showlegend=False,



    )
    fig.update_traces(textfont_size=11, textangle=0, marker_color='#DADADA', marker_line_color='black',
                  marker_line_width=1.5, opacity=0.9, textfont_color="black")

    return fig

# Recommandation pour le meulage
@app.callback(
Output("table-meulage", "columns"),
    Output("table-meulage", "data"),
    Input("line-selector", "value"),
    Input("budget-input", "value")
)
def recomm_meulage(line_selector, budget_input):
    file_map = {
        "Palézieux - Châtel-St-Denis": "StdE_Palezieux_Chatel_St_Denis.csv",
        "Châtel-St-Denis - Montbovon": "StdE_Chatel_St_Denis_Montbovon.csv",
    }

    if line_selector not in file_map:
        raise dash.exceptions.PreventUpdate

    file_path = file_map[line_selector]

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Erreur de chargement du fichier CSV: {e}")
        raise dash.exceptions.PreventUpdate

    if budget_input is None:
        raise dash.exceptions.PreventUpdate
    km_start_lim = 0
    budget_max = budget_input # CHF

    # Étape 1 : Filtrer les tronçons nécessitant un meulage (annee ≤ 1)
    df_meulage = df[(df["annee"] <= 1) & (df["km_start"] >= km_start_lim)].copy()

    # Ajouter une colonne de longueur + profondeur du tronçon à meuler en km
    df_meulage["Longueur"] = df_meulage["km_end"] - df_meulage["km_start"]
    df_meulage["Prof. max. usure [mm]"] = 0.08-df_meulage["reserve_usure_min"]

    # Trier par priorité de meulage (annee la plus négative en premier)
    # df_meulage = df_meulage.sort_values(by="annee", ascending=True).reset_index(drop=True)
    df_meulage = df_meulage.sort_values(by="km_start", ascending=True).reset_index(drop=True)

    # Paramètres

    cout_par_metre = 10  # CHF/m
    metres_max_km = (budget_max / cout_par_metre) / 1000  # Convertir en km
    seuil_fusion = 0 #0.19  # Distance max entre tronçons pour fusionner (en km)

    # Étape 2 : Fusion des tronçons proches en maintenant la priorité sur "annee" min
    troncons_fusionnes = []
    troncon_actuel = df_meulage.iloc[0].copy()
    id_troncons_selectionnes = []

    for i in range(1, len(df_meulage)):
        km_start, km_end, annee, longueur = df_meulage.loc[i, ["km_start", "km_end", "annee", "Longueur"]]

        # Vérifier si le tronçon est proche du précédent
        if km_start - troncon_actuel["km_end"] <= seuil_fusion and troncon_actuel["Longueur"] <= 0.85:
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
        non_select_reste_km = non_select[non_select["Longueur"] <= (metres_max_km - metres_selectionnes_km)]
        dernier_troncon_indx = non_select_reste_km["Longueur"].idxmax()
        selection_finale.append(non_select.loc[dernier_troncon_indx])
        metres_selectionnes_km += non_select.loc[dernier_troncon_indx, "Longueur"]
        #print("Il vous reste une réserve de:",
            #  ((metres_max_km - metres_selectionnes_km) * 1000).round(0), "m.")

    # Transformer en DataFrame final
    df_selection_corrige = pd.DataFrame(selection_finale)
    df_selection_corrige["Longueur"] = (df_selection_corrige["Longueur"] * 1000).round(0)


    # Affichage des résultats
    #print("km totaux selon budget:", metres_max_km)
    #print("km totaux du programme:", df_selection_corrige["Longueur"].sum().round(3) / 1000, "km")
    df_selection_corrige["km_start"] = df_selection_corrige["km_start"].round(3)
    df_selection_corrige["km_end"] = df_selection_corrige["km_end"].round(3)
    df_selection_corrige["annee"] = df_selection_corrige["annee"].round(1)
    df_selection_corrige["Prof. max. usure [mm]"] = df_selection_corrige["Prof. max. usure [mm]"].round(2)

    df_selection_corrige = df_selection_corrige.iloc[:, [0, 1, 10, 14, 15]]
    columns = [{"name": col, "id": col, "type": "numeric"} for col in df_selection_corrige.columns]

    return columns, df_selection_corrige.sort_values("km_start").to_dict("records")

@app.callback(
    [Output("km-this-year", "children"),
     Output("km-next-year", "children"),
     Output("km-no-grinding", "children"),
     Output("percent1", "children"),
     Output("percent2", "children"),
     Output("percent3", "children")],
    [Input("data-table", "data")]
)
def update_info_cards(table_data):
    df = pd.DataFrame(table_data)

    km_this_year = df[df["annee"] <= 0]["longueur"].sum() / 1000  # en km
    km_next_year = df[(df["annee"] > 0) & (df["annee"] < 1)]["longueur"].sum() / 1000
    km_no_grinding = df[df["annee"] >= 1]["longueur"].sum() / 1000
    percent1 = (km_this_year/(km_this_year+km_next_year+km_no_grinding)*100)
    percent2 = (km_next_year / (km_this_year + km_next_year + km_no_grinding) * 100)
    percent3 = (km_no_grinding / (km_this_year + km_next_year + km_no_grinding) * 100)

    return f"{km_this_year:.2f}", f"{km_next_year:.2f}", f"{km_no_grinding:.2f}", f"{percent1:.0f}%", f"{percent2:.0f}%", f"{percent3:.0f}%"




if __name__ == '__main__':
    app.run_server(debug=True)

