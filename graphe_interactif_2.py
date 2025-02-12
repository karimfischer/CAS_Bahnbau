import dash
from dash import dcc, html, callback_context
import plotly.io as pio
from dash.dependencies import Input, Output, State
import dash.exceptions

# Charger les graphiques

fig1 = pio.read_json("reserve_usure_Palezieux___Chatel_St_Denis.json")
fig2 = pio.read_json("data_25_cm_Palezieux___Chatel_St_Denis.json")

# Charger le premier graphique depuis le fichier fig1.json
#fig1 = pio.read_json("fig1.json")

# Charger le second graphique depuis le fichier fig2.json
#fig2 = pio.read_json("data_25_cm_Palezieux - Chatel-St-Denis.json")

# Taille ajustée
FIGURE_WIDTH = "75vw"  # Environ 75% de la largeur de la page
FIGURE_HEIGHT = "30vh"  # Hauteur réduite pour des figures plus fines
Y_AXIS_DOMAIN = [0.1, 0.9]  # Alignement parfait des axes Y

# Uniformisation de la police pour toute la page
PAGE_STYLE = {
    "font-family": "Arial, sans-serif"
}

# Fonction pour formater les axes et aligner les figures
def format_figure(fig, xlabel_format=True):
    fig.update_layout(
        title=None,
        margin=dict(l=50, r=30, t=10, b=30),  # Moins de marge pour rapprocher les figures
        xaxis=dict(
            matches='x',
            showgrid=True, gridcolor='black', gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            title=None,
            tickformat=",d" if xlabel_format else None,  # Affiche le kilométrage en "km"
        ),
        yaxis=dict(
            showgrid=True, gridcolor='black', gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            domain=Y_AXIS_DOMAIN,
            title=None  # On supprime le label de l'axe Y, car il est affiché en HTML
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

fig1 = format_figure(fig1)
fig2 = format_figure(fig2)

# --- Création de l'application Dash ---
app = dash.Dash(__name__)

init_store_data = {
    "xaxis": fig1.layout.xaxis.range if "range" in fig1.layout.xaxis else None,
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
                                           'paddingRight': '10px', 'paddingTop': '5px', 'lineHeight': 'normal'}),
        dcc.Graph(id="graph-1", figure=fig1, config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH, 'padding': '0px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'flex-start'}),

    html.Div([
        html.Div("Profondeur max. usure ondulatoire [mm]", style={'width': '10vw', 'textAlign': 'right', 'fontSize': '12px',
                                                                   'paddingRight': '10px', 'paddingTop': '5px', 'lineHeight': 'normal'}),
        dcc.Graph(id="graph-2", figure=fig2, config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH, 'padding': '0px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'flex-start'}),
], style=PAGE_STYLE)

# --- Callbacks pour mise à jour ---
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
    Input("range-store", "data"),
    State("graph-1", "figure"),
    State("graph-2", "figure")
)



def update_graphs(store_data, fig1_state, fig2_state):
    if not store_data:
        raise dash.exceptions.PreventUpdate

    fig1_state["layout"]["xaxis"]["range"] = store_data["xaxis"]
    fig2_state["layout"]["xaxis"]["range"] = store_data["xaxis"]

    return fig1_state, fig2_state


if __name__ == '__main__':
    app.run_server(debug=True)