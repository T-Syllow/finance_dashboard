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

# alle Händler bei ihrer ID als Liste
merchants = transaction_data['merchant_id'].unique().tolist()

# Jede Transaktion hat eine Merchant_id und einen mcc_code --> Wertpaar als neuer Dataframe
merchant_mcc_relations = transaction_data[['merchant_id', 'mcc']].copy()

# Händler Kategorien (Klartext)
merchant_categories = mcc_codes_data['description'].unique().tolist()

# Händler Kategorie Codes (ID)
merchant_category_codes = mcc_codes_data['mcc_code'].unique()

state_counts = transaction_data.groupby("merchant_state").size().reset_index(name="transaction_count")

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

map = px.choropleth(transaction_data, geojson=counties, locations='mcc', color='mcc',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
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
                dcc.Dropdown(['Unternehmen', 'Branchen'], 'Branchen', id='category_dropdown')
            ], width=2),
            dbc.Col([
                dcc.Dropdown([], id='entity_dropdown'),
            ], width=4),
    ]),
    dbc.Row([
        #dash_table.DataTable(data=merchant_mcc_relations.to_dict('records'), page_size=10, style_table={'overflowX': 'auto'}, id='tbl'),
    ]),
    dbc.Row([
        dbc.Col([
                dcc.Graph(figure=map)
            ], width=6),
        dbc.Col([
            dbc.Row([
                dbc.ListGroup([],numbered=True, id="top_list")
            ]),
            dbc.Row([
                dbc.ListGroup([],numbered=True, id="flop_list")
            ])
            ], width=6),
    ]),
], fluid=True)

@callback(
    Output('entity_dropdown', 'options'),
    Input('category_dropdown', 'value')
)
def update_entity_dropdown(category):
    if category == 'Branchen':
        return merchant_categories
    return merchants
        
# @callback(
#     Output('top_list', 'children'),
#     Input('entity_dropdown', 'value')
# )
# def update_top_list(merchant):
#     if merchant 
    

if __name__ == '__main__':
    app.run(debug=True)