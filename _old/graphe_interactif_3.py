import dash
from dash import dcc, html, callback_context
import plotly.io as pio
from dash.dependencies import Input, Output, State
import dash.exceptions

# Taille ajustée
FIGURE_WIDTH = "75vw"
FIGURE_HEIGHT = "30vh"
Y_AXIS_DOMAIN = [0.1, 0.9]

# Uniformisation de la police
PAGE_STYLE = {"font-family": "Arial, sans-serif"}

# Fonction pour charger les figures
def load_figures(line):
    if line == "Palézieux - Châtel-St-Denis":
        fig1 = pio.read_json("../reserve_usure_Palezieux___Chatel_St_Denis.json")
        fig2 = pio.read_json("../data_25_cm_Palezieux___Chatel_St_Denis.json")
    else:
        fig1 = pio.read_json("../reserve_usure_Chatel_St_Denis___Montbovon.json")
        fig2 = pio.read_json("../data_25_cm_Chatel_St_Denis___Montbovon.json")
    return fig1, fig2

# Fonction pour formater les figures
def format_figure(fig, xaxis_range=None):
    fig.update_layout(
        title=None,
        margin=dict(l=50, r=30, t=10, b=30),
        xaxis=dict(
            matches='x',
            showgrid=True, gridcolor='black', gridwidth=0.5,
            showline=True, linewidth=1, linecolor="black", mirror=True,
            title=None,
            tickformat=",d",
            range=xaxis_range if xaxis_range else None,
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

# Création de l'application Dash
app = dash.Dash(__name__)

# Layout principal
app.layout = html.Div([
    dcc.Store(id="range-store", data={"xaxis": None}),
    dcc.Store(id="line-store", data={"selected_line": "Palézieux - Châtel-St-Denis"}),

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
        dcc.Graph(id="graph-1", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH, 'padding': '0px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'flex-start'}),

    html.Div([
        dcc.Graph(id="graph-2", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH, 'padding': '0px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'flex-start'}),
])

# Callback pour changer la ligne
@app.callback(
    Output("graph-1", "figure", allow_duplicate=True),
    Output("graph-2", "figure", allow_duplicate=True),
    Output("line-store", "data", allow_duplicate=True),
    Input("line-selector", "value"),
    prevent_initial_call=True
)
def update_line(selected_line):
    fig1, fig2 = load_figures(selected_line)
    fig1 = format_figure(fig1)
    fig2 = format_figure(fig2)
    return fig1, fig2, {"selected_line": selected_line}

# Callback pour gérer le zoom
@app.callback(
    Output("range-store", "data"),
    Input("graph-1", "relayoutData"),
    Input("graph-2", "relayoutData"),
    State("range-store", "data"),
    prevent_initial_call=True
)
def update_zoom(relayout1, relayout2, store_data):
    relayout = relayout1 or relayout2
    if relayout and "xaxis.range" in relayout:
        store_data["xaxis"] = relayout["xaxis.range"]
    return store_data

if __name__ == '__main__':
    app.run_server(debug=True)
