import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json

# JSON-Daten laden
with open("mcc_codes.json", "r") as f:
    mcc_codes = json.load(f)

branchen_liste = list(mcc_codes.values())

# Beispiel-Daten erzeugen
months = pd.date_range(end=datetime.today(), periods=36, freq='ME')
data = pd.DataFrame({
    'Datum': months,
    'VW': np.cumsum(np.random.randn(36) * 10 + 50),
    'Porsche': np.cumsum(np.random.randn(36) * 10 + 45),
    'Daimler': np.cumsum(np.random.randn(36) * 10 + 40)
})
data.set_index('Datum', inplace=True)

kpis = ["+7%", "35 Mio €"] + ["KPI"] * 4

# App initialisieren
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

zeitraum_options = {
    "6 Monate": 6,
    "1 Jahr": 12,
    "2 Jahre": 24,
    "3 Jahre": 36
}


def create_kpi_cards(kpis):
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(html.H5(kpi, className="card-title text-center")),
                className="m-1 text-center shadow-sm"
            ),
            width=6
        ) for kpi in kpis
    ]


# Layout
app.layout = dbc.Container([
    html.H2("Branchenansicht", className="my-3"),

    dbc.Row([
        dbc.Col([
            html.Label("Branche wählen:"),
            dcc.Dropdown(
                id="branchen-dropdown",
                options=[{"label": b, "value": b} for b in branchen_liste],
                value=branchen_liste[0]
            ),
            html.Br(),
            dbc.Row(create_kpi_cards(kpis), className="g-1"),
        ], width=4),

        dbc.Col([
            html.Label("Zeitraum wählen:"),
            dcc.Dropdown(
                id="zeitraum-dropdown",
                options=[{"label": k, "value": k} for k in zeitraum_options],
                value="1 Jahr"
            ),
            html.Br(),
            dcc.Graph(id="umsatz-plot")
        ], width=8),
    ]),

    html.Hr(),

    html.H4("Persona"),

    dbc.Row([
        dbc.Col(html.Div("Einkommen Ø:", className="fw-bold")),
        dbc.Col(html.Div("Alter:", className="fw-bold")),
        dbc.Col(html.Div("Credit Score:", className="fw-bold")),
    ]),

    html.Div("Kaufverhalten: bezahlt mit…", className="mt-3 fw-bold")

], fluid=True)


# Callback mit Plotly
@app.callback(
    Output("umsatz-plot", "figure"),
    Input("zeitraum-dropdown", "value")
)
def update_plot(selected_period_label):
    selected_period = zeitraum_options[selected_period_label]
    filtered = data[-selected_period:]

    fig = go.Figure()
    for column in filtered.columns:
        fig.add_trace(go.Scatter(x=filtered.index, y=filtered[column], mode='lines', name=column))

    fig.update_layout(
        title="Umsatzentwicklung",
        xaxis_title="Monat",
        yaxis_title="Umsatz",
        template="plotly_white"
    )
    return fig


# App starten
if __name__ == "__main__":
    app.run(debug=True)
