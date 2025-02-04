import dash
from dash import dcc, html, callback_context
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash.exceptions
import plotly.io as pio

# Charger le premier graphique depuis le fichier fig1.json
fig1 = pio.read_json("fig1.json")

# Charger le second graphique depuis le fichier fig2.json
fig2 = pio.read_json("fig1.json")


# --- Création de l'application Dash ---
app = dash.Dash(__name__)

init_store_data = {
    "xaxis": fig1.layout.xaxis.range if "range" in fig1.layout.xaxis else None,
    "yaxis": fig1.layout.yaxis.range if "range" in fig1.layout.yaxis else None
}

# On utilise un dcc.Store pour conserver la plage courante des axes.
# On initialise avec les plages des figures.
app.layout = html.Div([
    dcc.Store(id="range-store", data=init_store_data),
    dcc.Graph(id="graph-1", figure=fig1, config={'scrollZoom': True}),
    dcc.Graph(id="graph-2", figure=fig2, config={'scrollZoom': True})
])

# --- Callback 1 : Mettre à jour le store quand on effectue un zoom ou un pan ---
@app.callback(
    Output("range-store", "data"),
    Input("graph-1", "relayoutData"),
    Input("graph-2", "relayoutData"),
    State("range-store", "data"),
    prevent_initial_call=True
)
def update_range(relayout1, relayout2, current_store):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # On détermine quel graphique a déclenché le callback
    triggered_prop = ctx.triggered[0]['prop_id'].split('.')[0]
    relayout = relayout1 if triggered_prop == "graph-1" else relayout2

    new_store = current_store.copy()
    updated = False

    if relayout:
        # Pour l'axe x
        if "xaxis.range" in relayout:
            new_range_x = relayout["xaxis.range"]
        elif "xaxis.range[0]" in relayout and "xaxis.range[1]" in relayout:
            new_range_x = [relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]]
        else:
            new_range_x = None

        if new_range_x and new_range_x != current_store.get("xaxis"):
            new_store["xaxis"] = new_range_x
            updated = True

        # Pour l'axe y
        if "yaxis.range" in relayout:
            new_range_y = relayout["yaxis.range"]
        elif "yaxis.range[0]" in relayout and "yaxis.range[1]" in relayout:
            new_range_y = [relayout["yaxis.range[0]"], relayout["yaxis.range[1]"]]
        else:
            new_range_y = None

        if new_range_y and new_range_y != current_store.get("yaxis"):
            new_store["yaxis"] = new_range_y
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

    # Mise à jour de la plage de l'axe x et y dans le Graphique 1
    fig1_state["layout"]["xaxis"]["range"] = store_data["xaxis"]
    fig1_state["layout"]["yaxis"]["range"] = store_data["yaxis"]

    # Mise à jour de la plage de l'axe x et y dans le Graphique 2
    fig2_state["layout"]["xaxis"]["range"] = store_data["xaxis"]
    fig2_state["layout"]["yaxis"]["range"] = store_data["yaxis"]

    return fig1_state, fig2_state

if __name__ == '__main__':
    app.run_server(debug=True)
