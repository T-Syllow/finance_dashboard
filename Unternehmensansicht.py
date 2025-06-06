import json
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Unternehmen-ID laden aus cards_data.csv für Dropdown
df_companies = pd.read_csv("cards_data.csv")
unternehmen_liste = df_companies['id'].dropna().unique().tolist()

# Unternehmen-ID laden aus transactions_data.csv für Dropdown
df_companies = pd.read_csv("transactions_data.csv")
unternehmen_liste = df_companies['id'].dropna().unique().tolist()

# --- Read in data ---
data_folder = "newData/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data_10k.csv", sep=",", encoding="utf8")
timed_transaction_data = transaction_data.copy()

# Darstellung Personas für Kreisdiagramme mit Zufallszahlen
labels = ['Persona 1', 'Persona 2', 'Persona 3', 'Persona 4']
values1 = [30, 20, 25, 25]
values2 = [40, 15, 25, 20]

# Dash - App starten
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# KPI Card-Funktion
def kpi_card(text):
    return dbc.Card(
        dbc.CardBody(html.Div(text, className="text-center fw-bold small")),
        style={"textOverflow": "ellipsis"},
        className="mb-2 shadow-sm",
    )

# Layout
app.layout = dbc.Container([
    html.H4("Unternehmensansicht", className="my-3"),

    dbc.Row([
        # Linke Spalte
        dbc.Col([
            html.Label("Unternehmen wählen:", className="mb-2"),
            dcc.DatePickerRange(
                id='date-range-start',
                min_date_allowed=transaction_data['date'].min(),
                max_date_allowed=transaction_data['date'].max(),
                start_date=transaction_data['date'].min(),
                end_date=transaction_data['date'].max(),
                className="mb-4"
            ),
            dbc.Row([], id="kpi_container", className="g-2 mb-2")
        ], width=3),

        # Rechte Spalte
        dbc.Col([
            dbc.Row([
                dcc.Tabs(id="umsatz-tabs", value='bar', className="mb-3", children=[
                    dcc.Tab(label='Balkendiagramm', value='bar'),
                    dcc.Tab(label='Liniendiagramm', value='line')
                ])
            ]),

            dcc.Graph(id="umsatz-barplot", config={"displayModeBar": False}, style={"height": "250px", "marginBottom": "40px"}),

            dbc.Row([
                dbc.Col(dcc.Graph(id="pie1", config={"displayModeBar": False}, style={"height": "180px"}), width=6),
                dbc.Col(dcc.Graph(id="pie2", config={"displayModeBar": False}, style={"height": "180px"}), width=6)
            ])
        ], width=9)
    ], align="start", className="g-3"),
], fluid=True, style={"maxWidth": "100vw", "overflow": "hidden", "paddingBottom": "20px"})

# Callback für Umsatz und Kreisdiagramme
@app.callback(
    Output("umsatz-barplot", "figure"),
    Output("pie1", "figure"),
    Output("pie2", "figure"),
    Input("umsatz-tabs", "value"),
    Input("date-range-start", "start_date"),
    Input("date-range-start", "end_date"),
)
def update_dashboard(value, start_date, end_date):
    transaction_data['date'] = pd.to_datetime(transaction_data['date'])
    transaction_data['Monat'] = transaction_data['date'].dt.to_period("M").dt.to_timestamp()

    umsatz_data = transaction_data[
        (transaction_data['merchant_id'] == 59935) &
        (transaction_data['date'] >= pd.to_datetime(start_date)) &
        (transaction_data['date'] <= pd.to_datetime(end_date))
    ].groupby('Monat')['amount'].sum().reset_index()

    umsatz_data.rename(columns={"amount": "Umsatz"}, inplace=True)

    if value == 'bar':
        fig = px.bar(umsatz_data[-12:], x='Monat', y='Umsatz', title=f"Umsatz 2024 - Unternehmens-ID: 59935")
    else:
        fig = px.line(umsatz_data[-12:], x='Monat', y='Umsatz', title=f"Umsatz 2024 - Unternehmens-ID: 59935")

    fig_pie1 = px.pie(names=labels, values=values1, title="Budgetverteilung").update_layout(margin=dict(t=30, b=10))
    fig_pie2 = px.pie(names=labels, values=values2, title="Kunden beim Konkurrenten").update_layout(margin=dict(t=30, b=10))

    return fig, fig_pie1, fig_pie2

# Callback für KPI Cards
@app.callback(
    Output('kpi_container', 'children'),
    Input("date-range-start", "start_date"),
    Input("date-range-start", "end_date"),
)
def renderKPIs(start_date, end_date):
    transaction_data['date'] = pd.to_datetime(transaction_data['date'])
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    timed_transaction_data = transaction_data[(transaction_data['date'] >= start_date) & (transaction_data['date'] <= end_date)]

    if timed_transaction_data.empty:
        return dbc.Col([
            dbc.Row([
                dbc.Alert('keine Daten in diesem Zeitraum verfügbar!', className="fs-5 text", color="danger"),
            ]),
        ], className="ranklist_container p-4")

    unternehmen_transaktionen = timed_transaction_data[timed_transaction_data['merchant_id'] == 59935]

    Marktkapitalisierung = unternehmen_transaktionen["amount"].sum()
    Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    DurchschnittTransaktionshöhe = unternehmen_transaktionen['amount'].mean()
    DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} € ".replace(",", "X").replace(".", ",").replace("X", ".")

    GesamtTransaktionen = unternehmen_transaktionen["merchant_id"].count()
    EinzigartigeKäufer = unternehmen_transaktionen["client_id"].nunique()
    DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer
    DurchschnittTransaktionenProKäufer = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

    GesamtAusgabenProClient = transaction_data.groupby("client_id")["amount"].sum()
    Durchschnitt_gesamt = GesamtAusgabenProClient.mean()
    UnternehmensAusgabenProClient = unternehmen_transaktionen.groupby("client_id")["amount"].sum()

    DurchschnittBranche = UnternehmensAusgabenProClient.mean()
    ConsumerMoneySpent = (DurchschnittBranche / Durchschnitt_gesamt) * 100
    ConsumerMoneySpent = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

    CustomerLifetimeValue = Durchschnitt_gesamt / EinzigartigeKäufer * 100
    CustomerLifetimeValue = f"{CustomerLifetimeValue:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    kpi_texts = [
        {'Markt- kapitalisierung': Marktkapitalisierung},
        {'durchschn. Transaktionshöhe': DurchschnittTransaktionshöhe},
        {'durchschn. Transaktionen pro Käufer': DurchschnittTransaktionenProKäufer},
        {'Umsatzwachstum (%)': 87.42},
        {'Consumer Money Spent (%)': ConsumerMoneySpent},
        {'Käufer': EinzigartigeKäufer},
        {'Customer Lifetime Value': CustomerLifetimeValue},
    ]

    cards = [
        dbc.Col(
            kpi_card(f"{list(kpi.keys())[0]} : {list(kpi.values())[0] if list(kpi.values())[0] is not None else 'n/a'}"),
            width=6
        )
        for kpi in kpi_texts
    ]

    return dbc.Row(cards, className="g-2 mb-2")

# Run App
if __name__ == "__main__":
    app.run(debug=True)
