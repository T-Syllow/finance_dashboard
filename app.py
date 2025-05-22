# Imports
import json
from urllib.request import urlopen
from dash import Dash, html, dash_table, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re
import plotly.graph_objects as go
import pandas as pd

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

counties["features"][0]

# --- Read in data ---
data_folder = "newData/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data_10k.csv", sep=",",  encoding="utf8")
cards_data = pd.read_csv(data_folder + "cleaned_cards_data.csv", sep=",",  encoding="utf8")
users_data = pd.read_csv(data_folder + "cleaned_users_data.csv", sep=",",  encoding="utf8")
with open(data_folder + 'mcc_codes.json', 'r', encoding='utf-8') as f:
    mcc_dict = json.load(f)
mcc_codes_data = pd.DataFrame(list(mcc_dict.items()), columns=['mcc_code', 'description'])


# alle Händler
merchants = transaction_data['merchant_id'].unique()

# Jede Transaktion hat eine Merchant_id und einen mcc_code --> Wertpaar als neuer Dataframe
merchant_mcc_relations = transaction_data[['merchant_id', 'mcc']].copy()

# Händler Kategorien (Klartext)
merchant_categories = mcc_codes_data['description'].unique().tolist()

# Händler Kategorie Codes (ID)
merchant_branche_codes = mcc_codes_data['mcc_code'].unique()

state_counts = transaction_data.groupby("merchant_state").size().reset_index(name="transaction_count")

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

map = px.choropleth(transaction_data, geojson=counties, locations='mcc', color='mcc',
                           color_continuous_scale="Viridis",
                           scope="usa",
                           labels={'state_counts':'state_counts'}
                          )
map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

app.layout = dbc.Container([
    dbc.Row([
        html.Div('Finance Table Transaction Data', className="text-primary text-center fs-3")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Col([
                dcc.Dropdown(['1 Monat', '3 Monate', '6 Monate', '1 Jahr', '2 Jahre', '3 Jahre'], 'Quartal', id='zeitraum_dropdown', className="")
            ], width=12, className="gap-2"),
            dbc.Col([
                dbc.Col([
                    dcc.Dropdown(['Unternehmen', 'Branchen'], 'Branchen', id='category_dropdown')
                ], width=3),
                dbc.Col([
                    dcc.Dropdown(['5411'],'5411', id='entity_dropdown'),
                ], width=8),
            ], width=12, className="d-flex py-2 gap-2 justify-content-start"),
        ], width=6, className="py-3 filterbar"),
    ], className="navbar"),
    dbc.Row([
        dbc.Col([
                dcc.Graph(figure=map)
            ], width=6, className="d-flex justify-content-center align-items-center"),
        dbc.Col([
            # html.Div(
            #     html.Ul(
            #         id="unternehmen_liste"
            #     ),
            #     id="unternehmen_liste_container",
            #     style={"position": "absolute", "top": 0, "right": 0, "height": "100%", "zIndex": "1", "overflowY": "scroll"},
            # ),
            # dbc.Row([
            #     dbc.Button("Alle anzeigen", color="primary", className="me-1 col-4", id="show_unternehmen_btn"),
            # ], className="d-flex justify-content-center"),
            dbc.Row([
            ], id="right_section")
        ], width=6),
    ]),
], fluid=True, className="body")

@callback(
    Output('entity_dropdown', 'options'),
    Input('category_dropdown', 'value')
)
def update_entity_dropdown(branche):
    if branche == 'Branchen':
        categories = [
            {"label": cat, "value": str(mcc)}
            for mcc, cat in mcc_codes_data[["mcc_code", "description"]].drop_duplicates().values
        ]
        return categories
    return merchants.tolist()
        
@callback(
    Output('right_section', 'children'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value')
)
def update_right_section(category, entity_value):
    if category == 'Unternehmen' and entity_value:
        merchant_id = int(entity_value)
        df_merchant = transaction_data[transaction_data['merchant_id'] == merchant_id]

        if df_merchant.empty:
            return dbc.Alert("Keine Daten für dieses Unternehmen verfügbar.", color="warning")

        # Umsatz berechnen
        total_revenue = df_merchant['amount'].sum()

        # Niederlassungen: Stadt + Bundesstaat
        standorte = (
            df_merchant[['merchant_city', 'merchant_state']]
            .drop_duplicates()
            .sort_values(by=['merchant_state', 'merchant_city'])
        )

        # Formatierung der Standorte als Bullet-List
        standort_liste = html.Ul([
            html.Li(f"{row['merchant_city']}, {row['merchant_state']}")
            for _, row in standorte.iterrows()
        ])

        return dbc.Card([
            dbc.CardHeader(f"Händler-ID: {merchant_id}"),
            dbc.CardBody([
                html.H5("Unternehmensprofil", className="card-title"),
                html.P(f"Gesamtumsatz: {total_revenue:.2f} €", className="card-text"),
                html.P(f"Anzahl Transaktionen: {len(df_merchant)}", className="card-text"),
                html.H6("Niederlassungen:"),
                standorte.__len__(),
                #standort_liste
            ])
        ], color="light", outline=True)

    branche = transaction_data.query(f"mcc == {entity_value}")
    # Gruppiere nach merchant_id und summiere den Umsatz (amount)
    umsatz_pro_merchant = (
        branche.groupby("merchant_id")['amount']
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_revenue"})
        .sort_values(by="total_revenue", ascending=False)
    )
    top_5 = umsatz_pro_merchant.nlargest(5, 'total_revenue')
    flop_5 = umsatz_pro_merchant.nsmallest(5, 'total_revenue')

    top_content = [
        dbc.ListGroupItem(
            f" Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €"
        , className="ranklist_item")
        for i, row in top_5.iterrows()
    ]

    flop_content = [
        dbc.ListGroupItem(
            f" Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €"
        , className="ranklist_item")
        for i, row in flop_5.iterrows()
    ]

    # Wenn "Branchen" gewählt ist -> Top/Flop-Liste
    return dbc.Col([
        dbc.Row([
            dbc.Label('Top 5', className="fs-2 text"),
            dbc.ListGroup(top_content, numbered=True, id="top_list", className="ranklist p-4")
        ]),
        dbc.Row([
            dbc.Label('Flop 5', className="fs-2 text"),
            dbc.ListGroup(flop_content, numbered=True, id="flop_list", className="ranklist p-4")
        ])
    ], className="ranklist_container p-4")
            
    
# @callback(
#     Output("unternehmen_liste", "children"),       
#     Input("show_unternehmen_btn", "n_clicks"),  
#     Input('category_dropdown', 'value'), 
#     Input('entity_dropdown', 'value'), 
#     prevent_initial_call=True
# )
# def on_click_update(n_clicks, category, entity):
#     if category != 'Branchen' or not entity:
#         return []

#     # Filtere alle Transaktionen für die gewählte Branche (MCC-Code)
#     df_branche = transaction_data[transaction_data['mcc'] == int(entity)]

#     # Umsatz + Transaktionsanzahl je Händler berechnen
#     metrics = (
#         df_branche.groupby("merchant_id")["amount"]
#         .agg(total_revenue="sum", transaction_count="count")
#         .reset_index()
#     )

#     # Standorte je Händler extrahieren
#     locations_map = (
#         df_branche.groupby("merchant_id")[["merchant_city", "merchant_state"]]
#         .apply(lambda x: list(set(zip(x["merchant_city"], x["merchant_state"]))))
#         .to_dict()
#     )

#     # Locations ins DataFrame einfügen
#     metrics["locations"] = metrics["merchant_id"].map(locations_map)

#     # Karten erzeugen
#     cards = []
#     for _, row in metrics.iterrows():
#         standort_liste = html.Ul([
#             html.Li(f"{city}, {state}") for city, state in row["locations"]
#         ])

#         card = html.Li(
#             dbc.Card(
#                 dbc.CardBody([
#                     html.H5(f"Händler-ID: {row['merchant_id']}", className="card-title"),
#                     html.P(f"Gesamtumsatz: {row['total_revenue']:.2f} €", className="card-text"),
#                     html.P(f"Anzahl Transaktionen: {row['transaction_count']}", className="card-text"),
#                     html.H6("Niederlassungen:"),
#                     standort_liste.__len__()
#                 ]),
#                 color="success", inverse=True
#             )
#         )
#         cards.append(card)

#     return cards

if __name__ == '__main__':
    app.run(debug=True)