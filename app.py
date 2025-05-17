# Imports
from urllib.request import urlopen
from dash import Dash, html, dash_table, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re
import plotly.graph_objects as go
import pandas as pd

# --- Read in data ---
data_folder = "data/"
transaction_data = pd.read_csv(data_folder + "reduced_transaction_data.csv", sep=",",  encoding="utf8")

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        html.Div('Finance Table Transaction Data', className="text-primary text-center fs-3")
    ]),
    dbc.Row([
        dash_table.DataTable(data=transaction_data.to_dict('records'), page_size=10, style_table={'overflowX': 'auto'}, id='tbl'),
    ]),
    dbc.Row([
        px.choropleth(transaction_data, geojson=counties, locations='amount', color='amount',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           scope="usa",
                           labels={'amount':'amount'}
                          ),

    ]),
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)