# Imports
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

fig = go.Figure(data=[go.Table(
    header=dict(values=list(transaction_data.columns),
                fill_color='paleturquoise',
                align='left'))
])

fig.show()

if __name__ == '__main__':
    app.run(debug=True)