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
#mcc_codes_data = pd.read_json(data_folder + "mcc_codes.json", encoding="utf8")

state_counts = transaction_data.groupby("merchant_state").size().reset_index(name="transaction_count")

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

map = px.choropleth(transaction_data, geojson=counties, locations='amount', color='amount',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           scope="usa",
                           labels={'amount':'amount'}
                          )
map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

app.layout = dbc.Container([
    dbc.Row([
        html.Div('Finance Table Transaction Data', className="text-primary text-center fs-3")
    ]),
    dbc.Row([
        #dash_table.DataTable(data=transaction_data.to_dict('records'), page_size=10, style_table={'overflowX': 'auto'}, id='tbl'),
    ]),
    dbc.Row([
        dcc.Graph(figure=map)
    ]),
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)