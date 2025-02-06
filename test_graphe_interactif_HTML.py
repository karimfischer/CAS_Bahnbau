import dash
from dash import dcc, html, callback_context
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash.exceptions
import plotly.io as pio

# Charger le premier graphique depuis le fichier fig1.json
fig1 = pio.read_json("fig1.json")

# Charger le second graphique depuis le fichier fig2.json
fig2 = pio.read_json("data_25_cm_Palezieux - Chatel-St-Denis.json")

fig1.update_layout(title=None, margin=dict(l=10, r=20, t=20, b=20), xaxis=dict(matches='x'))
fig2.update_layout(title=None, margin=dict(l=10, r=20, t=20, b=20), xaxis=dict(matches='x'))

# --- Création de l'application Dash ---
app = dash.Dash(__name__)

init_store_data = {
    "xaxis": fig1.layout.xaxis.range if "range" in fig1.layout.xaxis else None,
    "selected_line": "Palézieux - Châtel-Saint-Denis"
}

# On utilise un dcc.Store pour conserver la plage courante de l'axe x et la ligne sélectionnée
app.layout = html.Div([
    dcc.Store(id="range-store", data=init_store_data),
    html.Div([
        html.Label("Sélectionner une ligne ferroviaire:"),
        dcc.Dropdown(
            id="line-selector",
            options=[
                {"label": "Palézieux - Châtel-Saint-Denis", "value": "Palézieux - Châtel-Saint-Denis"},
                {"label": "Châtel-Saint-Denis - Montbovon", "value": "Châtel-Saint-Denis - Montbovon"},
                {"label": "Réseau VM entier", "value": "Réseau VM entier"}
            ],
            value="Palézieux - Châtel-Saint-Denis",
            clearable=False
        )
    ], style={'margin-bottom': '20px'}),
    html.Div([
        dcc.Graph(id="graph-1", figure=fig1, config={'scrollZoom': True},
                  style={'height': '45vh', 'margin-bottom': '-10px'}),
        dcc.Graph(id="graph-2", figure=fig2, config={'scrollZoom': True},
                  style={'height': '45vh', 'margin-top': '-10px'})
    ], style={'display': 'flex', 'flex-direction': 'column', 'gap': '0px'}),
])


# --- Callback 1 : Mettre à jour le store quand on effectue un zoom ou un pan ---
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


# --- Callback 2 : Mettre à jour les deux graphiques en fonction du store ---
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

    # Mise à jour de la plage de l'axe x uniquement
    fig1_state["layout"]["xaxis"]["range"] = store_data["xaxis"]
    fig2_state["layout"]["xaxis"]["range"] = store_data["xaxis"]

    return fig1_state, fig2_state


if __name__ == '__main__':
    app.run_server(debug=True)
