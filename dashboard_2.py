import dash
from dash import dcc, html, dash_table, callback_context
import plotly.io as pio
import plotly.express as px
from dash.dependencies import Input, Output, State
import dash.exceptions
import pandas as pd
import copy

# Taille des figures et style de la page
FIGURE_WIDTH = "75vw"
FIGURE_HEIGHT = "30vh"
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
            title=None
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True
    )
    return fig

# --- Création de l'application Dash ---
app = dash.Dash(__name__)

# Initialisation des données dans le Store
init_store_data = {
    "xaxis": None,
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
        html.Div("Profondeur max. usure ondulatoire [mm]", style={'width': '10vw', 'textAlign': 'right', 'fontSize': '12px',
                                                                   'paddingRight': '10px', 'paddingTop': '5px'}),
        dcc.Graph(id="graph-2", config={'scrollZoom': True},
                  style={'height': FIGURE_HEIGHT, 'width': FIGURE_WIDTH})
    ], style={'display': 'flex', 'align-items': 'flex-start'}),

    html.Hr(),

    html.H4("Données supplémentaires"),
    dash_table.DataTable(
        id="data-table",
        style_table={"width": TABLE_WIDTH, "overflowX": "auto", "overflowY": "auto", "maxHeight": "400px"},
        sort_action="native",
        column_selectable="single",
        style_data_conditional=[
            {"if": {"filter_query": "{annee} <= 0"}, "backgroundColor": "red", "color": "white"},
            {"if": {"filter_query": "{annee} > 0 && {annee} < 1"}, "backgroundColor": "orange", "color": "black"},
            {"if": {"filter_query": "{annee} >= 1"}, "backgroundColor": "green", "color": "white"},
        ]
    ),

    html.Hr(),

    dcc.Graph(id="histogram", style={'height': "30vh", 'width': TABLE_WIDTH}),
], style=PAGE_STYLE)

# --- Callback pour charger les graphes à partir des fichiers JSON ---
@app.callback(
    Output("graph-1", "figure"),
    Output("graph-2", "figure"),
    Input("line-selector", "value"),
    Input("range-store", "data"),
)
def update_graphs(selected_line, store_data):
    file_map = {
        "Palézieux - Châtel-St-Denis": ("reserve_usure_Palezieux___Chatel_St_Denis.json",
                                        "data_25_cm_Palezieux___Chatel_St_Denis.json"),
        "Châtel-St-Denis - Montbovon": ("reserve_usure_Chatel_St_Denis___Montbovon.json",
                                        "data_25_cm_Chatel_St_Denis___Montbovon.json"),
    }

    if selected_line not in file_map:
        raise dash.exceptions.PreventUpdate

    file1, file2 = file_map[selected_line]

    try:
        fig1 = format_figure(pio.read_json(file1))
        fig2 = format_figure(pio.read_json(file2))
    except Exception as e:
        print(f"Erreur de chargement des fichiers JSON: {e}")
        raise dash.exceptions.PreventUpdate

    if store_data and store_data["xaxis"]:
        fig1.update_layout(xaxis_range=store_data["xaxis"])
        fig2.update_layout(xaxis_range=store_data["xaxis"])

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

    df = df.iloc[:, :-2]

    columns = [{"name": col, "id": col, "type": "numeric"} for col in df.columns]

    return columns, df.to_dict("records")

# --- Callback pour afficher l'histogramme ---
@app.callback(
    Output("histogram", "figure"),
    Input("data-table", "active_cell"),
    State("data-table", "data"),
)
def update_histogram(active_cell, table_data):
    if not active_cell:
        return px.histogram(title="Sélectionnez une colonne")

    col_selected = active_cell["column_id"]
    df = pd.DataFrame(table_data)

    fig = px.histogram(df, x=col_selected, y="longueur", histfunc="sum", title=f"Histogramme de {col_selected}")
    fig.update_layout(bargap=0.1)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
