import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

#Unternehmen-ID laden aus cards_data.csv für Dropdown
df_companies = pd.read_csv("cards_data.csv")
unternehmen_liste = df_companies['id'].dropna().unique().tolist()

#Monatsdaten für Balkendiagramm - random, monatlich (Umsatzdaten integrieren!)  ####
months = pd.date_range(start="2023-01-01", end="2025-01-01", freq='M')
umsatz_data = pd.DataFrame({
    'Monat': months,
    'Umsatz': np.cumsum(np.random.randn(len(months)) * 1000 + 5000)
})

# Darstellung Personas für Kreisdiagramme mit Zufallszahlen
labels = ['Persona 1', 'Persona 2', 'Persona 3', 'Persona 4']
values1 = [30, 20, 25, 25]
values2 = [40, 15, 25, 20]

#KPI´s, (muss noch integriert werden!)
kpi_texts = [
    "+7% Umsatzentwicklung", "14% Marktanteil",
    "KPI 3", "KPI 2",
    "Customer Lifetime Value: 35 Mio €", "KPI 4",
    "KPI 5", "KPI 6"
]

# Dash - App starten
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


#einzelne KPI´s mit Text erzeugen (Cards erstellen)
def kpi_card(text):
    return dbc.Card(
        dbc.CardBody(html.Div(text, className="text-center fw-bold small")),
        className="mb-2 shadow-sm",
        style={"height": "80px"}
    )

#Layout
app.layout = dbc.Container([
    html.H4("Unternehmensansicht", className="my-3"),

#linke Spalte
    dbc.Row([
        dbc.Col([
            html.Label("Unternehmen wählen:", className="mb-2"),
            dcc.Dropdown(
                id="unternehmen-dropdown",
                options=[{"label": name, "value": name} for name in unternehmen_liste],
                value=unternehmen_liste[0],
                className="mb-3"
            ),
            dbc.Row([
                dbc.Col([kpi_card(kpi_texts[i]), kpi_card(kpi_texts[i + 4])])
                for i in range(4)
            ])
        ], width=3),

#rechte Spalte 
        dbc.Col([
            dcc.Graph(id="umsatz-barplot", config={"displayModeBar": False}, style={"height": "250px"}),
        

            dbc.Row([
                dbc.Col(dcc.Graph(id="pie1", config={"displayModeBar": False}, style={"height": "180px"}), width=6),
                dbc.Col(dcc.Graph(id="pie2", config={"displayModeBar": False}, style={"height": "180px"}), width=6)
            ])
        ], width=9)
    ], align="start", className="g-3")

], fluid=True, style={"maxWidth": "100vw", "overflow": "hidden", "paddingBottom": "20px"})

#Callbacks
@app.callback(
    Output("umsatz-barplot", "figure"),
    Output("pie1", "figure"),
    Output("pie2", "figure"),
    Input("unternehmen-dropdown", "value")
)

#Update der Daten 
def update_dashboard(selected_company):
    fig_bar = px.bar(
        data_frame=umsatz_data[-12:], 
        x='Monat', y='Umsatz',
        title=f"Umsatz 2024 - Unternehmens-ID: {selected_company}"
    ).update_layout(template='plotly_white', margin=dict(t=30, b=20))

    fig_pie1 = px.pie(names=labels, values=values1, title="Budgetverteilung").update_layout(margin=dict(t=30, b=10))
    fig_pie2 = px.pie(names=labels, values=values2, title="Kunden beim Konkurrenten").update_layout(margin=dict(t=30, b=10))

    return fig_bar, fig_pie1, fig_pie2

#run app
if __name__ == "__main__":
    app.run(debug=True)
