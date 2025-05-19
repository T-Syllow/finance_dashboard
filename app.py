import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# =============================
# Daten vorbereiten
# =============================
df = pd.read_csv("reduced_transaction_data.csv")


df['merchant_state'] = df['merchant_state'].fillna('Unknown')

# Konfigurierbarer Bereich für spätere Erweiterungen
country_config = {
    'scope': 'usa',
    'geo_column': 'merchant_state',
    'location_mode': 'USA-states'
}


# =============================
# Dash App initialisieren
# =============================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Transaktionsübersicht USA", className="my-4"),
    dcc.Tabs(id="tabs", value='by_state', children=[
        dcc.Tab(label='Nach Bundesstaat', value='by_state'),
        dcc.Tab(label='Nach Branche (MCC)', value='by_mcc'),
        dcc.Tab(label='Nach Unternehmen (Merchant ID)', value='by_merchant'),
    ]),
    html.Div(id='tabs-content')
], fluid=True)


# =============================
# Callback Logik für Tabs
# =============================
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    geo_col = country_config['geo_column']
    scope = country_config['scope']
    location_mode = country_config.get('location_mode', None)

    if tab == 'by_state':
        counts = df.groupby(geo_col).size().reset_index(name='transaction_count')
        fig = px.choropleth(
            counts,
            locations=geo_col,
            locationmode=location_mode,
            color='transaction_count',
            color_continuous_scale="Blues",
            scope=scope,
            labels={geo_col: 'Bundesstaat', 'transaction_count': 'Transaktionen'},
            hover_data={geo_col: True, 'transaction_count': True}
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return dcc.Graph(figure=fig)

    elif tab == 'by_mcc':
        mcc_counts = df.groupby('mcc').size().reset_index(name='transaction_count')
        fig = px.bar(mcc_counts, x='mcc', y='transaction_count', labels={'mcc': 'Branche (MCC)', 'transaction_count': 'Transaktionen'})
        return dcc.Graph(figure=fig)

    elif tab == 'by_merchant':
        merchant_counts = df.groupby('merchant_id').size().reset_index(name='transaction_count')
        fig = px.bar(merchant_counts, x='merchant_id', y='transaction_count', labels={'merchant_id': 'Unternehmen (Merchant ID)', 'transaction_count': 'Transaktionen'})
        return dcc.Graph(figure=fig)


# =============================
# App starten
# =============================
if __name__ == "__main__":
    app.run(debug=True)
