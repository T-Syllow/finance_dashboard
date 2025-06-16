# Imports
import json
import locale
from urllib.request import urlopen
from dash import Dash, State, html, dash_table, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re
import plotly.graph_objects as go
import pandas as pd
import numpy as np


with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

counties["features"][0]

country_config = {
    'scope': 'usa',
    'geo_column': 'merchant_state',
    'location_mode': 'USA-states'
}

plotly_layout_config = {
    "plot_bgcolor": "rgba(0, 0, 0, 0)",   # Zeichenfläche
    "paper_bgcolor": "rgba(0, 0, 0, 0)",   # Gesamter Graph
    "legend_bgcolor": "rgba(0, 0, 0, 0)",  # Hintergrund der Legende
}


###############
# Einkommensklassen Definition (für income_category_bar_component)
EINKOMMENSKLASSEN = [
    {"label": "Extreme Armut",           "min": 0,      "max": 14999,    "color": "#9e0142"},
    {"label": "Unterschicht",            "min": 15000,  "max": 29999,    "color": "#d53e4f"},
    {"label": "Niedrige Mittelschicht",  "min": 30000,  "max": 49999,    "color": "#f46d43"},
    {"label": "Mittlere Mittelschicht",  "min": 50000,  "max": 84999,    "color": "#fdae61"},
    {"label": "Obere Mittelschicht",     "min": 85000,  "max": 149999,   "color": "#abdda4"},
    {"label": "Oberschicht (reich)",     "min": 150000, "max": 499999,   "color": "#3288bd"},
    {"label": "Superreiche / Elite",     "min": 500000, "max": 99999999, "color": "#5e4fa2"},
]

blues_dark_to_light = [
    "#08519c",  # sehr dunkelblau
    "#3182bd",  # dunkelblau
    "#6baed6",  # mittelblau
    "#9ecae1",  # hellblau
    "#deebf7"   # sehr hellblau
]      

blues_dark_to_light_12 = [
            "#08306b",  # sehr dunkelblau
            "#08519c",
            "#0b318f",
            "#1664ad",
            "#2171b5",
            "#2383c1",
            "#2b8cbe",
            "#3182bd",
            "#4292c6",
            "#4fa3ca",
            "#6baed6",
            "#4292c6"   # nochmal ein mittlerer Ton, damit es 12 sind
        ]

def get_income_category_colors_and_labels(einkommensklassen):
    color_segments = [klass["color"] for klass in einkommensklassen]
    categories = []
    for klass in einkommensklassen:
        if klass["min"] == 0:
            label = f"{klass['label']}: < {klass['max']:,} $"
        elif klass["max"] >= 99999999:
            label = f"{klass['label']}: > {klass['min']:,} $"
        else:
            label = f"{klass['label']}: {klass['min']:,} $ – {klass['max']:,} $"
        categories.append(label)
    return color_segments, categories
##############
##############

# --- Read in data ---
data_folder = "./newData/"
parquet_folder = "./parquet_data/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data_50k.csv", sep=',', encoding='utf-8')
# transaction_data = pd.read_parquet(parquet_folder + "cleaned_transaction_data_50k.parquet", columns=["id","date","client_id","card_id","amount","merchant_id","merchant_city","merchant_state","mcc"])
cards_data = pd.read_csv(data_folder + "cleaned_cards_data.csv")
users_data = pd.read_csv(data_folder + "cleaned_users_data.csv")
with open(data_folder + 'mcc_codes.json', 'r', encoding='utf-8') as f:
    mcc_dict = json.load(f)
mcc_codes_data = pd.DataFrame(list(mcc_dict.items()), columns=['mcc_code', 'description'])

# alle Händler
merchants = transaction_data['merchant_id'].unique()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([ 
    dcc.Store(id='timed_transaction_data'),
    dcc.Store(id='timed_branchen_transaction_data'),
    dcc.Store(id='timed_unternehmen_transaction_data'),
    dbc.Row([
        dbc.Col([
            dbc.Col([
                dcc.DatePickerRange(
                    id='date-range-start',
                    min_date_allowed=transaction_data['date'].min(),
                    max_date_allowed=transaction_data['date'].max(),
                    start_date=transaction_data['date'].min(),
                    end_date=transaction_data['date'].max(),
                    className="datepicker"
                ),
            ], width=12, className="gap-5" ,id='zeitraum_container'),
            dbc.Col([
                dbc.Col([
                    dcc.Dropdown(['Unternehmen', 'Branchen'], 'Branchen', id='category_dropdown',  className="main-dropdown")
                ], width=3),
                dbc.Col([
                    dcc.Dropdown(['5411'],'5411', id='entity_dropdown', className="main-dropdown"),
                ], width=8),
            ], width=12, className="d-flex py-2 gap-2 justify-content-start"),
        ], width=6, className="px-5 filterbar"),
        dbc.Col([
            dbc.Button('KPIs anzeigen', className='toggle_button', id="toggle-button" , n_clicks=0),
            dbc.Button('Branche anzeigen', className='toggle_button', id="toggle-button2" , n_clicks=0),
            dbc.Button('Unternehmen anzeigen', className='toggle_button', id="toggle-button4" , n_clicks=0),
            dbc.Button('Persona anzeigen', className='toggle_button', id="toggle-button5" , n_clicks=0)
        ], width=6, className="px-5 d-flex justify-content-end align-items-center gap-2"),
    ], className="navbar"),
    dbc.Row([
        dbc.Col([
                
        ], width=6, className="d-flex justify-content-center align-items-start", id="map-container"),
        dbc.Col([
            dbc.Row([
            
            ], id="right_section"),
        ], width=5,),
    ], className="h-100"),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H2("", id="branche_title"),
                html.Img(src="./assets/x.png", className="icon1", id="toggle-button-close")
            ], width=12, className="px-5 py-2 d-flex justify-content-between"),
        ], className="popup-header"),
        dbc.Row([
            
        ], className="h-100 d-flex p-3", id="detail-view")
    ], width=12, className="h-100 position-absolute left-0", id="popup"),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H2("", id="branche_title2"),
                html.Img(src="./assets/x.png", className="icon1", id="toggle-button-close2")
            ], width=12, className="px-5 py-2 d-flex justify-content-between"),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(data=[], page_size=10, style_table={'overflowX': 'auto'}, id='tbl_detailansicht'),
            ], width=12, className="d-flex p-3", id="detail-view2")
        ], className="h-100 overflow-scroll")
    ], width=12, className="h-100 position-absolute left-0", id="popup2"),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H2("", id="branche_title4"),
                html.Img(src="./assets/x.png", className="icon1", id="toggle-button-close4")
            ], width=12, className="px-5 py-2 d-flex justify-content-between"),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(data=[], page_size=10, style_table={'overflowX': 'auto'}, id='tbl_detailansicht_Unternehmen'),
            ], width=12, className="d-flex p-3", id="detail-view4")
        ], className="h-100 overflow-scroll")
    ], width=12, className="h-100 position-absolute left-0", id="popup4"),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H2("", id="branche_title5"),
                html.Img(src="./assets/x.png", className="icon1", id="toggle-button-close5")
            ], width=12, className="px-5 py-2 d-flex justify-content-between"),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([
                
            ], width=12, className="d-flex p-3", id="detail-view5")
        ], className="h-100 overflow-scroll")
    ], width=12, className="h-100 position-absolute left-0", id="popup5")
], fluid=True, className="body position-relative")

@app.callback(
    Output('timed_transaction_data', 'data'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
)
def update_timed_transaction_data(start_date, end_date):
    df = transaction_data
    df['date'] = pd.to_datetime(df['date'])
    filtered = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    return filtered.to_dict('records')

@app.callback(
    Output('timed_branchen_transaction_data', 'data'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
    Input('category_dropdown', 'value'),  # Die ausgewählte Branche (MCC)
    Input('entity_dropdown', 'value')  # Die ausgewählte Branche (MCC)
)
def update_timed_branchen_transaction_data(start_date, end_date, category, entity):
    if category == 'Branchen':
        if entity is None:
            return []  # Keine Daten, wenn keine Branche ausgewählt ist

        df = transaction_data
        df['date'] = pd.to_datetime(df['date'])

        # Filtere die Daten basierend auf dem Zeitraum und der Branche (MCC)
        filtered = df[
            (df['date'] >= pd.to_datetime(start_date)) &
            (df['date'] <= pd.to_datetime(end_date)) &
            (df['mcc'] == int(entity))
        ]

        return filtered.to_dict('records')
    
@app.callback(
    Output('timed_unternehmen_transaction_data', 'data'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
    Input('category_dropdown', 'value'),  # Die ausgewählte Branche (MCC)
    Input('entity_dropdown', 'value')  # Die ausgewählte Branche (MCC)
)
def update_timed_unternehmen_transaction_data(start_date, end_date, category, entity):
    if category == 'Unternehmen':
        if entity is None:
            return []  # Keine Daten, wenn keine Branche ausgewählt ist

        df = transaction_data
        df['date'] = pd.to_datetime(df['date'])

        # Filtere die Daten basierend auf dem Zeitraum und der Branche (MCC)
        filtered = df[
            (df['date'] >= pd.to_datetime(start_date)) &
            (df['date'] <= pd.to_datetime(end_date)) &
            (df['merchant_id'] == int(entity))
        ]

        return filtered.to_dict('records')

@callback(
    Output('map-container', 'children'),
    Input('timed_transaction_data', 'data'),
    Input('entity_dropdown', 'value'),
    Input('category_dropdown', 'value'),
)
def renderMap(timed_transaction_data, entity_value, category_value):
    if timed_transaction_data is None or entity_value is None:
        return None

    # DataFrame aus Store-Daten rekonstruieren
    filtered_data = pd.DataFrame(timed_transaction_data)
    if filtered_data.empty:
        return dbc.Alert("Keine Daten im gewählten Zeitraum.", color="warning")

    geo_col = country_config['geo_column']
    scope = country_config['scope']
    location_mode = country_config.get('location_mode', None)

    if category_value == 'Branchen' and entity_value is not None:
        # Filtern nach MCC Code (Branche)
        df_filtered = filtered_data[filtered_data['mcc'] == int(entity_value)]
        # Berechnung der Marktkapitalisierung (Umsatz) pro Bundesstaat für die Branche
        marketcap = df_filtered.groupby(geo_col)['amount'].sum().reset_index(name="marketcap")
        title_text = f"Umsatz pro Bundesstaat:"
    elif category_value == 'Unternehmen' and entity_value is not None:
        # Filtern nach merchant_id (Unternehmen)
        df_filtered = filtered_data[filtered_data['merchant_id'] == int(entity_value)]
        # Berechnung des Umsatzes pro Bundesstaat für das Unternehmen
        marketcap = df_filtered.groupby(geo_col)['amount'].sum().reset_index(name="marketcap")
        title_text = f"Umsatz pro Bundesstaat:"

    if not marketcap.empty:
        fig = px.choropleth(
            marketcap,
            locations=geo_col,
            locationmode=location_mode,
            color='marketcap',
            color_continuous_scale="Blues",
            scope=scope,
            labels={geo_col: 'Bundesstaat', 'marketcap': 'Umsatz'},
            hover_data={geo_col: True, 'marketcap': True}
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, title_text=title_text, **plotly_layout_config)
        return dcc.Graph(figure=fig, className="w-100 overflowx-scroll")
    else:
        return dbc.Alert("Keine Daten für diese Auswahl.", color="warning")

@callback(
    Output('entity_dropdown', 'options'),
    Input('category_dropdown', 'value')
)
def update_entity_dropdown(category):
    if category == 'Branchen':
        categories = [
            {"label": cat, "value": str(mcc)}
            for mcc, cat in mcc_codes_data[["mcc_code", "description"]].drop_duplicates().values
        ]
        return categories
    return merchants.tolist()

def create_merchant_card(merchant_id, total_revenue, transaction_count, standorte, branchenbeschreibung, marktanteil_display, fig_bar_chart, online_umsatz_anteil_display):
    return [
        dbc.Card([
            dbc.CardHeader(f"Händler-ID: {merchant_id}", style={"backgroundColor": "#3182bd", "color": "white"}),
            dbc.CardBody([
                html.H5("Unternehmensprofil", className="card-title"),
                html.P(f"Branche: {branchenbeschreibung}", className="card-text"),
                html.P(f"Gesamtumsatz: {total_revenue:.2f} $", className="card-text"),
                html.P(f"Marktanteil: {marktanteil_display}", className="card-text"),
                html.P(f"Anzahl Transaktionen: {transaction_count}", className="card-text"),
                html.P(f"Umsatzanteil der Onlinetransaktionen:  {online_umsatz_anteil_display}", className="card-text"),
                html.P("Niederlassungen: " + str(len(standorte)), className="card-text"),
              
            ], style={"backgroundColor": "#deebf7"})
        ], color="light", outline=True, style={"margin": "10px 0"}),
        dbc.Col([
            dcc.Graph(figure=fig_bar_chart, className="w-100", style={"height": "400px"}),
        ], width=12, className=""),
    ]

def create_ranklist(title, content, list_id):
    if title == 'Top 5':
        return dbc.Row([
            dbc.Col([
                dbc.Col([
                    html.Img(src="./assets/top.png", className="icon2"),
                ], className="ranklist-title d-flex justify-content-start"),
                dbc.ListGroup(content, numbered=True, id=list_id, className="ranklist p-2")
            ], width=12, className="ranklist_wrapper d-flex")
        ])
    return dbc.Row([
            dbc.Col([
                dbc.Col([
                    html.Img(src="./assets/flop.png", className="icon2"),
                ], className="ranklist-title d-flex justify-content-start"),
                dbc.ListGroup(content, numbered=True, id=list_id, className="ranklist p-2")
            ], width=12, className="ranklist_wrapper d-flex")
        ])
   
def handle_unternehmen(df, entity_value, unternehmen_transaktionen):
    merchant_id = int(entity_value)
    df_merchant = df[df['merchant_id'] == merchant_id]

    if df_merchant.empty:
        return dbc.Alert("Keine Daten für dieses Unternehmen verfügbar.", color="warning")
    
    unternehmen_transaktionen = pd.DataFrame(unternehmen_transaktionen)

    total_revenue = df_merchant['amount'].sum()
    standorte = (
        df_merchant[['merchant_city', 'merchant_state']]
        .drop_duplicates()
        .sort_values(by=['merchant_state', 'merchant_city'])
    )

    branchenbeschreibung = "Unbekannte Branche"

    if 'mcc' in df_merchant.columns and not df_merchant['mcc'].isnull().all():
        mcc_code = str(int(df_merchant['mcc'].iloc[0]))
        branchenbeschreibung = mcc_codes_data.loc[
            mcc_codes_data["mcc_code"] == mcc_code, "description"
        ].values
        branchenbeschreibung = branchenbeschreibung[0] if len(branchenbeschreibung) > 0 else "Unbekannte Branche"
    else:
        branchenbeschreibung = "Unbekannte Branche"

    marktanteil_display = "n/a"

    # Marktanteil berechnen
    branche_umsatz = df[df['mcc'] == int(mcc_code)]['amount'].sum() if 'mcc' in df.columns else 0
    if branche_umsatz > 0:
        marktanteil = total_revenue / branche_umsatz * 100
        marktanteil_display = f"{marktanteil:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        marktanteil_display = "n/a"

    # Online Umsatzanteil berechnen
    online_transaktionen = df_merchant[df_merchant['merchant_city'].str.upper() == 'ONLINE']
    online_umsatz = online_transaktionen['amount'].sum()
    if total_revenue > 0:
        online_umsatz_anteil = (online_umsatz / total_revenue) * 100
        online_umsatz_anteil_display = f"{online_umsatz_anteil:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        online_umsatz_anteil_display = "n/a"


    top_10_bundesstaaten = (
        unternehmen_transaktionen.groupby('merchant_state')['amount']
        .sum()
        .reset_index(name='total_revenue')
        .sort_values(by='total_revenue', ascending=False)
        .head(10)
    )

    # Bar-Chart erstellen
    fig_bar_chart = px.bar(
        top_10_bundesstaaten,
        x='total_revenue',
        y='merchant_state',
        orientation='h',  # Horizontaler Bar-Chart
        title='Top 10 Bundesstaaten nach Umsatz',
        labels={'total_revenue': 'Umsatz ($)', 'merchant_state': 'Bundesstaat'},
        text_auto=True,
        color=None,
        color_discrete_sequence=['#1f77b4'],
        category_orders={
            "merchant_state": list(top_10_bundesstaaten.sort_values("total_revenue", ascending=False)["merchant_state"])
        }
    )

    # Layout des Bar-Charts anpassen
    fig_bar_chart.update_layout(
        xaxis_title="Umsatz ($)",
        yaxis_title="Bundesstaat",
        template="plotly_white",
    )

    return create_merchant_card(merchant_id, total_revenue, len(df_merchant), standorte, branchenbeschreibung, marktanteil_display, fig_bar_chart, online_umsatz_anteil_display)

def handle_branchen(df, entity_value):
    df_branche = df[df['mcc'] == int(entity_value)]

    if df_branche.empty:
        return dbc.Col([
            dbc.Row([
                dbc.Alert('keine Daten in diesem Zeitraum verfügbar!', className="fs-5 text", color="danger"),
            ]),
        ], className="ranklist_container p-2")

    umsatz_pro_merchant = (
        df_branche.groupby("merchant_id")['amount']
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_revenue"})
        .sort_values(by="total_revenue", ascending=False)
    )

    top_5 = umsatz_pro_merchant.nlargest(5, 'total_revenue')
    flop_5 = umsatz_pro_merchant.nsmallest(5, 'total_revenue')

    top_content = [
        dbc.ListGroupItem(
            f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} $",
            className="ranklist_item"
        )
        for _, row in top_5.iterrows()
    ]

    flop_content = [
        dbc.ListGroupItem(
            f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} $",
            className="ranklist_item"
        )
        for _, row in flop_5.iterrows()
    ]

    return dbc.Col([
        create_ranklist('Top 5', top_content, "top_list"),
        create_ranklist('Flop 5', flop_content, "flop_list")
    ], className="ranklist_container p-4")

@callback(
    Output('right_section', 'children'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value'),
    Input('timed_transaction_data', 'data'),
)
def update_right_section(category, entity_value, timed_unternehmen_transaction_data):
    if timed_unternehmen_transaction_data is None or entity_value is None:
        return None

    df = pd.DataFrame(timed_unternehmen_transaction_data)

    if category == 'Unternehmen':
        return handle_unternehmen(df, entity_value, timed_unternehmen_transaction_data)

    if category == 'Branchen':
        return handle_branchen(df, entity_value)

    return None

@app.callback(
    Output("toggle-button4", "className"),
    Output("toggle-button2", "className"),
    Output("toggle-button5", "className"),
    Input("category_dropdown", "value"),
)
def toggle_class(category):
    if category == "Branchen":
        return "d-none toggle_button", "d-block toggle_button", "d-block toggle_button"
    return "d-block toggle_button", "d-none toggle_button", "d-none toggle_button"
    
    

@app.callback(
    Output("popup", "className"),
    Input("toggle-button", "n_clicks"),
    Input("toggle-button-close", "n_clicks"),
    State("popup", "className")
)
def toggle_class(n1, n2, current_class):
    if "top-100-percent" in current_class:
        return "h-100 position-absolute left-0 col-12 top-0-pixel"
    else:
        return "h-100 position-absolute left-0 col-12 top-100-percent"
    
@app.callback(
    Output("popup2", "className"),
    Input("toggle-button2", "n_clicks"),
    Input("toggle-button-close2", "n_clicks"),
    State("popup2", "className")
)
def toggle_class2(n1, n2, current_class):
    if "top-100-percent" in current_class:
        return "h-100 position-absolute left-0 col-12 top-0-pixel"
    else:
        return "h-100 position-absolute left-0 col-12 top-100-percent"
    
@app.callback(
    Output("popup4", "className"),
    Input("toggle-button4", "n_clicks"),
    Input("toggle-button-close4", "n_clicks"),
    State("popup4", "className")
)
def toggle_class4(n1, n2, current_class):
    if "top-100-percent" in current_class:
        return "h-100 position-absolute left-0 col-12 top-0-pixel"
    else:
        return "h-100 position-absolute left-0 col-12 top-100-percent"    
    
@app.callback(
    Output("popup5", "className"),
    Input("toggle-button5", "n_clicks"),
    Input("toggle-button-close5", "n_clicks"),
    State("popup5", "className")
)
def toggle_class4(n1, n2, current_class):
    if "top-100-percent" in current_class:
        return "h-100 position-absolute left-0 col-12 top-0-pixel"
    else:
        return "h-100 position-absolute left-0 col-12 top-100-percent"    
    
def process_branchen_data(df, entity, start_date, end_date):
    time_transaction_data = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    branchen_transaktionen = time_transaction_data[time_transaction_data['mcc'] == int(entity)]
    branchen_transaktionen["year"] = pd.to_datetime(branchen_transaktionen["date"]).dt.year
    umsatz_Jahr_Merchant = branchen_transaktionen.groupby(["year", "merchant_id"])["amount"].sum().reset_index(name="Umsatz_im_Jahr")
    umsatz_pro_merchant = umsatz_Jahr_Merchant.groupby("merchant_id")["Umsatz_im_Jahr"].sum().reset_index(name="gesamtumsatz")
    return umsatz_Jahr_Merchant, umsatz_pro_merchant, branchen_transaktionen

def create_kpi_cards(kpis):
    blues_colors = [
        "#deebf7", "#9ecae1", "#6baed6"
    ]
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5(value),
                    html.P(key),
                ], className="kpi-card-body"),
            ], style={"backgroundColor": blues_colors[i % len(blues_colors)]})
        ], width=12, className="kpi-card")
        for i, kpi in enumerate(kpis)
        for key, value in kpi.items()
    ]

def create_branchen_charts(umsatz_Jahr_Merchant, top_5, flop_5):
    umsatz_Jahr_Merchant_top = umsatz_Jahr_Merchant[umsatz_Jahr_Merchant['merchant_id'].isin(top_5['merchant_id'])]
    umsatz_Jahr_Merchant_flop = umsatz_Jahr_Merchant[umsatz_Jahr_Merchant['merchant_id'].isin(flop_5['merchant_id'])]
    fig1 = px.line(umsatz_Jahr_Merchant_top, x='year', y='Umsatz_im_Jahr', color='merchant_id', markers=True, title="Jährlicher Gesamtumsatz aller Händler in der Branche")
    fig2 = px.line(umsatz_Jahr_Merchant_flop, x='year', y='Umsatz_im_Jahr', color='merchant_id', markers=True, title="Jährlicher Gesamtumsatz aller Händler in der Branche")
    return fig1, fig2

@app.callback(
    Output("detail-view", "children"),
    Input("category_dropdown", "value"),
    Input("entity_dropdown", "value"),
    Input("date-range-start", "start_date"),
    Input("date-range-start", "end_date"),
    Input('timed_transaction_data', 'data'),
    Input('timed_unternehmen_transaction_data', 'data'),
    Input('timed_branchen_transaction_data', 'data'),

)
def render_detailview(category, entity, start_date_first, end_date_first, timed_transaction_data, timed_unternehmen_data, timed_branchen_data):
    if timed_transaction_data is None:
        return dbc.Alert("Keine Transaktionsdaten verfügbar.", color="warning")

    df = pd.DataFrame(timed_transaction_data)
    timed_unternehmen_data = pd.DataFrame(timed_unternehmen_data)
    timed_branchen_data = pd.DataFrame(timed_branchen_data)
    df['date'] = pd.to_datetime(df['date'])

    if category == 'Branchen' and entity is not None:
        
        # =======================
        
        umsatz_Jahr_Merchant, umsatz_pro_merchant, branchen_transaktionen = process_branchen_data(df, entity, start_date_first, end_date_first)
        top_5 = umsatz_pro_merchant.nlargest(5, 'gesamtumsatz')
        flop_5 = umsatz_pro_merchant.nsmallest(5, 'gesamtumsatz')
        fig1, fig2 = create_branchen_charts(umsatz_Jahr_Merchant, top_5, flop_5)

        # ============================= Code Start ============================================

         #Marktkapitalisierung berechnet

        Marktkapitalisierung = umsatz_pro_merchant["gesamtumsatz"].sum()  
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        # =====================================================================================


    

        #branchen_transaktionen = transaction_data[transaction_data['mcc'] == int(entity)]
        #branchen_transaktionen = time_transaction_data[time_transaction_data['mcc'] == int(entity)]

        GesamtTransaktionen = branchen_transaktionen["merchant_id"].count()
        EinzigartigeKäufer = branchen_transaktionen["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer

        DurchschnittTransaktionenProKäufer = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

        # =====================================================================================

        #Durchschnittliche Transaktionshöhe einer Transaktion in dem ausgewählten Zeitraum

        #branchen_transaktionen = transaction_data[transaction_data['mcc'] == int(entity)]
        DurchschnittTransaktionshöhe = branchen_transaktionen['amount'].mean()
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} $ ".replace(",", "X").replace(".", ",").replace("X", ".")

        # =====================================================================================
        
        # Eine Serie, in der jeder Kunde (client_id) mit der Gesamtsumme seiner Ausgaben (amount) verknüpft ist.
        GesamtAusgabenProClient = transaction_data.groupby("client_id")["amount"].sum()
        # Ein einzelner Wert, der den durchschnittlichen Betrag angibt, den ein Kunde insgesamt ausgegeben hat.
        Durchschnitt_gesamt = GesamtAusgabenProClient.mean()
        
        
        BranchenAusgabenProClient = branchen_transaktionen.groupby("client_id")["amount"].sum()

        # Ein einzelner Wert, der den durchschnittlichen Betrag angibt, den ein Kunde in der Branche ausgegeben hat.
        DurchschnittBranche = BranchenAusgabenProClient.mean()

        # "ConsumerMoneySpent" = Ein Wert, der angibt, wie viel Prozent der Gesamtausgaben eines durchschnittlichen Kunden in der betrachteten Branche ausgegeben werden.
        ConsumerMoneySpent= (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpent = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

        # =================== Online Umsatzanteil =====================

        online_transaktionen = branchen_transaktionen[branchen_transaktionen['merchant_city'].str.upper() == 'ONLINE']
        online_umsatz = online_transaktionen['amount'].sum()
        gesamt_umsatz = branchen_transaktionen['amount'].sum()

        if gesamt_umsatz > 0:
            online_umsatz_anteil = (online_umsatz / gesamt_umsatz) * 100
            online_umsatz_anteil_display = f"{online_umsatz_anteil:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            online_umsatz_anteil_display = "n/a"

        # =====================================================================================

        #Unique Customers
        EinzigartigeKäufer = branchen_transaktionen["client_id"].nunique()

       

        #Marktkapitalisierung berechnet

        Marktkapitalisierung = umsatz_pro_merchant["gesamtumsatz"].sum()  
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")
        print("Marktkapitalisierung: ", Marktkapitalisierung)

        # =====================================================================================


        #Durchschnitt der Transaktionen Pro Käufer - noch nicht fertig 

        #branchen_transaktionen = transaction_data[transaction_data['mcc'] == int(entity)]
        #branchen_transaktionen = time_transaction_data[time_transaction_data['mcc'] == int(entity)]

        GesamtTransaktionen = branchen_transaktionen["merchant_id"].count()
        EinzigartigeKäufer = branchen_transaktionen["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer

        DurchschnittTransaktionenProKäufer = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

        print("Durchschnitt der Transaktionen pro Käufer: ", DurchschnittTransaktionenProKäufer)


        # =====================================================================================

        #Durchschnittliche Transaktionshöhe einer Transaktion in dem ausgewählten Zeitraum

        #branchen_transaktionen = transaction_data[transaction_data['mcc'] == int(entity)]
        DurchschnittTransaktionshöhe = branchen_transaktionen['amount'].mean()
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} $ ".replace(",", "X").replace(".", ",").replace("X", ".")

        print("Durchschnittliche Transaktionshöhe: ", DurchschnittTransaktionshöhe)

        # =====================================================================================
        
        #Consumer Money Spent (%)
        
        GesamtAusgabenProClient = transaction_data.groupby("client_id")["amount"].sum()
        Durchschnitt_gesamt = GesamtAusgabenProClient.mean()

        BranchenAusgabenProClient = branchen_transaktionen.groupby("client_id")["amount"].sum()
        DurchschnittBranche = BranchenAusgabenProClient.mean()

        ConsumerMoneySpent= (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpent = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

        print("Consumer Money Spent (%):", ConsumerMoneySpent)

        # =====================================================================================

        #Unique Customers
        EinzigartigeKäufer = branchen_transaktionen["client_id"].nunique()

        umsatzwachstum_display = "n/a"

        umsatz_pro_jahr = ""

        if not branchen_transaktionen.empty:
            branchen_transaktionen['date'] = pd.to_datetime(branchen_transaktionen['date'])
            branchen_transaktionen['year'] = branchen_transaktionen['date'].dt.year

            start_year = pd.to_datetime(start_date_first).year
            end_year = pd.to_datetime(end_date_first).year

            umsatz_pro_jahr = branchen_transaktionen.groupby('year')['amount'].sum()
            print("Umsatz pro Jahr:", umsatz_pro_jahr)

            if start_year in umsatz_pro_jahr.index and end_year in umsatz_pro_jahr.index:
                umsatz_anfang = umsatz_pro_jahr.loc[start_year]
                umsatz_ende = umsatz_pro_jahr.loc[end_year]
                print("Umsatz Startjahr:", umsatz_anfang)
                print("Umsatz Endjahr:", umsatz_ende)
                if umsatz_anfang != 0:
                    umsatzwachstum = ((umsatz_ende - umsatz_anfang) / umsatz_anfang) * 100
                    umsatzwachstum_display = f"{umsatzwachstum:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    umsatzwachstum_display = "n/a"
            else:
                umsatzwachstum_display = "n/a"
        else:
            umsatzwachstum_display = "n/a"

        

        umsatz_pro_jahr_chart = None
        if isinstance(umsatz_pro_jahr, pd.Series) and not umsatz_pro_jahr.empty:
            umsatz_pro_jahr_df = umsatz_pro_jahr.reset_index()
            umsatz_pro_jahr_df.columns = ['Jahr', 'Umsatz']
            # Anzahl der Jahre bestimmen
            umsatz_pro_jahr_df['Jahr'] = umsatz_pro_jahr_df['Jahr'].astype(str)
            n_years = umsatz_pro_jahr_df['Jahr'].nunique()
            # Passende Anzahl Blautöne aus der Skala ziehen
            blues = px.colors.sample_colorscale("Blues", [i/(n_years-1) if n_years > 1 else 0.5 for i in range(n_years)])
            umsatz_pro_jahr_chart = px.bar(
                umsatz_pro_jahr_df,
                x='Jahr',
                y='Umsatz',
                title='Umsatz pro Jahr',
                labels={'Jahr': 'Jahr', 'Umsatz': 'Umsatz ($)'},
                text_auto=True,
                color='Jahr',
                color_discrete_sequence=blues_dark_to_light_12
            )
            umsatz_pro_jahr_chart.update_layout(
                xaxis_title="Jahr",
                yaxis_title="Umsatz ($)",
                template="plotly_white",
                showlegend=False
            )

        kpis = [
                {'Marktkapitalisierung': Marktkapitalisierung},   # Berechnet die Marktkapitalisierung 
                {'durchschn. Transaktionshöhe': DurchschnittTransaktionshöhe},    # Berechnet die durchschn. Transaktionshöhe einer Transaktion in dem ausgewählten Zeitraum in Euro 
                {'durchschn. Transaktionen pro Käufer': DurchschnittTransaktionenProKäufer}, # Berechnet die Menge an Transaktionen, die ein Käufer im Durchschnitt im ausgewählten Zeitraum tätigt.
                {'Umsatzwachstum (Jahresvergleich)': umsatzwachstum_display},  # Umsatzwachstum dynamisch berechnet
                {'Consumer Money Spent (%)': ConsumerMoneySpent},  # Berechnet zunächst die durchschn. Menge an Geld, die ein User im Schnitt im ausgewählten Zeitraum ausgibt. Dann berechnet wie viel er für die Branche im durchschnitt ausgibt. und setzt es anschließend ins Verhältnis! ==> %
                {'Käufer':  EinzigartigeKäufer}, # Wie viele einzigartige User haben im ausgewählten Zeitrsaum bei der Branche eingekauft?
                {'Online Umsatzanteil (%)': online_umsatz_anteil_display}, #Anteil aller online Transaktionen am Gesamtumsatz der Branche
        ]

        return [
                dbc.Col(create_kpi_cards(kpis), md=3, sm=12, className="detail-view-left-section d-flex flex-wrap justify-content-start align-content-start gap-2 overflow-y-scroll"),
                dbc.Col([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(
                                dbc.Tabs([
                                    dbc.Tab(dcc.Graph(figure=fig1, id="card-content", className="card-text w-100", style={"height": "350px"}), label="Top 5", tab_id="tab-1"),
                                    dbc.Tab(dcc.Graph(figure=fig2, id="card-content", className="card-text w-100", style={"height": "350px"}), label="Flop 5", tab_id="tab-2"),
                                ], active_tab="tab-1"),
                            ),
                        ], style={"background-color": "#FFFFFF"}),
                    ], width=12, className="detail-view-right-section-1"),
                    dbc.Col([
                        dcc.Graph(figure=umsatz_pro_jahr_chart, className="w-100", style={"height": "300px"}) if umsatz_pro_jahr_chart else None,
                    ], width=12, className="detail-view-right-section-2"),
                ], md=9, sm=12, className="detail-view-right-section"),
        ]

    if category == 'Unternehmen' and entity is not None:

        # Konvertiere timed_transaction_data in ein DataFrame
        df = pd.DataFrame(timed_transaction_data)

        # Filtere die Transaktionen für das ausgewählte Unternehmen
        unternehmen_transaktionen = df[df['merchant_id'] == entity]

        # Umsatz pro Monat berechnen
        unternehmen_transaktionen['month'] = pd.to_datetime(unternehmen_transaktionen['date']).dt.to_period('M')
        umsatz_pro_monat = unternehmen_transaktionen.groupby('month')['amount'].sum().reset_index()
        umsatz_pro_monat['month'] = umsatz_pro_monat['month'].astype(str)  # Monat in String umwandeln für die Darstellung

        # Bar-Chart erstellen
        bar_umsatz_pro_monat = px.bar(
            umsatz_pro_monat,
            x='month',
            y='amount',
            title='Umsatz je Monat',
            labels={'month': 'Monat', 'amount': 'Umsatz ($)'},
            text_auto=True
        )

        # Formatierung des Bar-Charts
        bar_umsatz_pro_monat.update_layout(
            xaxis_title="Monat",
            yaxis_title="Umsatz ($)",
            template="plotly_white"
        )

        # Weitere Berechnungen und KPIs
        Marktkapitalisierung = unternehmen_transaktionen["amount"].sum()
        MarktkapitalisierungDisplay = f"{Marktkapitalisierung:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        DurchschnittTransaktionshöhe = unternehmen_transaktionen['amount'].mean()
        DurchschnittTransaktionshöheDisplay = f"{DurchschnittTransaktionshöhe:,.2f} $ ".replace(",", "X").replace(".", ",").replace("X", ".")

        GesamtTransaktionen = unternehmen_transaktionen["merchant_id"].count()
        EinzigartigeKäufer = unternehmen_transaktionen["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer
        DurchschnittTransaktionenProKäuferDisplay = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

        GesamtAusgabenProClient = df.groupby("client_id")["amount"].sum()
        Durchschnitt_gesamt = GesamtAusgabenProClient.mean()
        UnternehmensAusgabenProClient = unternehmen_transaktionen.groupby("client_id")["amount"].sum()

        DurchschnittBranche = UnternehmensAusgabenProClient.mean()
        ConsumerMoneySpent = (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpentDisplay = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

        CustomerLifetimeValue = Durchschnitt_gesamt / EinzigartigeKäufer * 100
        CustomerLifetimeValueDisplay = f"{CustomerLifetimeValue:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        bundesstaat_transaktionen = df.groupby('merchant_state')['merchant_id'].count().reset_index(name='transaction_count')


        # Sortiere die Bundesstaaten nach der Anzahl der Transaktionen und wähle die Top 3 aus
        top_3_bundesstaaten = bundesstaat_transaktionen.nlargest(3, 'transaction_count')

        top_3_bundesstaaten = top_3_bundesstaaten.sort_values(by='transaction_count', ascending=True)

        # Bar-Chart erstellen
        fig_bar_chart = px.bar(
            top_3_bundesstaaten,
            x='transaction_count',
            y='merchant_state',
            orientation='h',  # Horizontaler Bar-Chart
            title='Top 3 Bundesstaaten nach Anzahl der Transaktionen',
            labels={'transaction_count': 'Anzahl der Transaktionen', 'merchant_state': 'Bundesstaat'},
            text_auto=True,
            color='merchant_state',  # Damit jede Zeile eine andere Farbe bekommt
            color_discrete_sequence=blues_dark_to_light,
            category_orders={
                "merchant_state": list(top_3_bundesstaaten.sort_values("transaction_count", ascending=False)["merchant_state"])
            }
        )

        # Layout des Bar-Charts anpassen
        fig_bar_chart.update_layout(
            xaxis_title="Anzahl der Transaktionen",
            yaxis_title="Bundesstaat",
            template="plotly_white"
        )

        # =====================


    
        #MarktkapitalisierungUnternehmen = unternehmen_transaktionen["amount"].sum()
        unternehmen_mcc = timed_unternehmen_data['mcc'].iloc[0]  
        unternehmen_mcc = int(unternehmen_mcc)  # Sicherstellen, dass es ein Integer ist
        print("MCC des Unternehmens:", unternehmen_mcc)
        GesamtMarktkapitalisierungBranche = df[df['mcc'] == unternehmen_mcc]["amount"].sum()
        
        branchenbeschreibung = mcc_codes_data.loc[
            mcc_codes_data["mcc_code"] == str(unternehmen_mcc), "description"
        ].values
        branchenbeschreibung = branchenbeschreibung[0] if len(branchenbeschreibung) > 0 else "Unbekannte Branche"

        #Transaktionshöhe anzahl pro Bereich 
        ErsterPreisbereich = timed_unternehmen_data[timed_unternehmen_data['amount']<50]['amount'].count()
        #ZweiterPreisbereich = unternehmen_transaktionen[unternehmen_transaktionen['amount']>=50 & unternehmen_transaktionen['amount']<=200].count()
        ZweiterPreisbereich = timed_unternehmen_data[(timed_unternehmen_data['amount'] >= 50) & (timed_unternehmen_data['amount'] <= 200)]['amount'].count()
        DritterPreisbereich = timed_unternehmen_data[timed_unternehmen_data['amount']>200]['amount'].count()

        fig_pie = px.pie(
            names=["Marktkapitalisierung", "Gesamtkapitalisierung je Branche"],
            values=[Marktkapitalisierung, GesamtMarktkapitalisierungBranche],
            title="Marktanteil in " + branchenbeschreibung,
            color_discrete_sequence=blues_dark_to_light
        )
        
        
        #2. Kreisdiagramm 
        fig_pie_2 = px.pie(
            names=["bis 50$", "50$ - 200$", "über 200$"],
            values=[ErsterPreisbereich, ZweiterPreisbereich, DritterPreisbereich],
            title='Anteil der Transaktionshöhe nach Bereichen',
            labels = ['bis 50$', '50$ - 200$', 'über 200$'],
            color_discrete_sequence=blues_dark_to_light
        )


        # =====================

        kpis = [
            {'Marktkapitalisierung': MarktkapitalisierungDisplay},
            {'durchschn. Transaktionshöhe': DurchschnittTransaktionshöheDisplay},
            {'durchschn. Transaktionen pro Käufer': DurchschnittTransaktionenProKäuferDisplay},
            {'Umsatzwachstum (Jahresvergleich)': 87.42},
            {'Consumer Money Spent (%)': ConsumerMoneySpentDisplay},
            {'Käufer': EinzigartigeKäufer},
            {'Customer Lifetime Value': CustomerLifetimeValueDisplay},
        ]

        return [
            dbc.Col([
                dbc.Col(
                    create_kpi_cards(kpis)
                ,width=12, className="detail-view-kpis d-flex flex-wrap justify-content-start align-content-start gap-2 overflow-y-scroll"),
                dbc.Col([
                    
                ], width=12)
            ], md=3, sm=12, className="detail-view-left-section" ),
            dbc.Col([
                dbc.Col([
                    dcc.Graph(figure=bar_umsatz_pro_monat, className="w-100", style={"height": "400px"}),
                ], width=12, className="detail-view-right-section-3"),
                dbc.Col([
                    dbc.Col([    
                        dcc.Graph(figure=fig_bar_chart, className="w-100", style={"height": "300px"}),
                    ], width=6),
                    dbc.Col([
                       dbc.Col([
                            dbc.Col([
                                dcc.Graph(figure=fig_pie, className="w-100"),
                            ], width=6),
                            dbc.Col([
                                dcc.Graph(figure=fig_pie_2, className="w-100"),
                            ], width=6),
                        ], width=12, id="gesamtkapitalisierung_container", className="d-flex justify-content-between align-content-start p-3 overflow-y-scroll"),
                    ], width=6),
                ], width=12, className="detail-view-right-section-4 d-flex"),
            ], md=9, sm=12, className="detail-view-right-section")
        ]
    if category == 'Unternehmen':

        kpis = [
            {'Marktkapitalisierung': 100000000},
            {'durchschn. Transaktionshöhe': 380.20},
            {'durchschn. Transaktionen pro Käufer': 100000000},
            {'Umsatzwachstum (%)': 87.32},
            {'Consumer Money Spent (%)': 100000000},
            {'Unique Customers': 2102},
        ]

        return [
            dbc.Col([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(
                            [
                                html.H5(value),
                                html.P(
                                    key
                                ),
                            ], className="kpi-card-body"
                        ),         
                    ], color="success", outline=True)
                ],width=5, className="kpi-card p-2")
                for kpi in kpis
                for key, value in kpi.items()
            ], width=5, className="detail-view-left-section d-flex flex-wrap justify-content-start align-content-start p-3 overflow-y-scroll"),
            dbc.Col([
                dbc.Col([
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Tabs(
                                    [
                                        dbc.Tab("erster Tab Content",label="Top 5", tab_id="tab-3"),
                                        dbc.Tab("erster Tab Content",label="Flop 5", tab_id="tab-4"),
                                    ],
                                    active_tab="tab-3",
                                )
                            ),
                        ]
                    ),
                ], width=12, className="detail-view-right-section-1"),
                dbc.Col([
                    html.Div("Persona")
                ], width=12, className="detail-view-right-section-2"),
            ], width=7, className="detail-view-right-section")
        ]
    

@app.callback(
    Output("detail-view2", "children"),
    Input("category_dropdown", "value"),
    Input('timed_branchen_transaction_data', 'data'),
    Input('timed_unternehmen_transaction_data', 'data'),
)
def render_detailview2(category, timed_branchen_data, timed_unternehmen_data):
    if category == 'Unternehmen':
        return html.Div("Unternehmensdaten werden hier angezeigt.")

    if timed_branchen_data is None or len(timed_branchen_data) == 0:
        return html.Div("Keine Daten verfügbar.")

    df = pd.DataFrame(timed_branchen_data)
    kpi_df = df.groupby("merchant_id").agg(
        gesamtumsatz=("amount", "sum"),
        anzahl_transaktionen=("amount", "count"),
        durchschn_transaktionshoehe=("amount", "mean"),
        einzigartige_kaeufer=("client_id", "nunique")
    ).reset_index()
    kpi_df["durchschn_transaktionen_pro_kaeufer"] = kpi_df["anzahl_transaktionen"] / kpi_df["einzigartige_kaeufer"]


    #Sortiere nach Umsatz (absteigend)
    kpi_df = kpi_df.sort_values(by="gesamtumsatz", ascending=False)

    # Formatierungen
    kpi_df["gesamtumsatz"] = kpi_df["gesamtumsatz"].map(lambda x: f"{x:,.2f} $".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi_df["durchschn_transaktionshoehe"] = kpi_df["durchschn_transaktionshoehe"].map(lambda x: f"{x:,.2f} $".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi_df["durchschn_transaktionen_pro_kaeufer"] = kpi_df["durchschn_transaktionen_pro_kaeufer"].map(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    columns = [
        ("merchant_id", "Händler-ID"),
        ("gesamtumsatz", "Gesamtumsatz"),
        ("anzahl_transaktionen", "Anzahl Transaktionen"),
        ("durchschn_transaktionshoehe", "Ø Transaktionshöhe"),
        ("einzigartige_kaeufer", "Einzigartige Käufer"),
        ("durchschn_transaktionen_pro_kaeufer", "Ø Transaktionen/Käufer"),
    ]

    table = html.Table([
        html.Thead([
            html.Tr([html.Th(name, style={"textAlign":"right"}) for _, name in columns])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(row[col], style={"textAlign":"right"}) for col, _ in columns
            ]) for _, row in kpi_df.iterrows()
        ])
    ], className="table table-hover table-bordered w-100")

    return html.Div([
        html.Div("Unternehmens-KPIs je Händler", className="fw-bold mb-2"),
        table
    ], className="w-100 overflow-scroll")

@app.callback(
    Output("detail-view4", "children"),
    Input("category_dropdown", "value"),
    Input('timed_branchen_transaction_data', 'data'),
    Input('timed_unternehmen_transaction_data', 'data'),
)
def render_detailview4(category, timed_branchen_data, timed_unternehmen_data):
    if category == 'Unternehmen':
        if timed_unternehmen_data is None or len(timed_unternehmen_data) == 0:
            return html.Div("Keine Daten verfügbar.")

        df = pd.DataFrame(timed_unternehmen_data)
        # Gruppiere nach Bundesstaat
        kpi_df = df.groupby("merchant_state").agg(
            gesamtumsatz=("amount", "sum"),
            anzahl_transaktionen=("amount", "count"),
            durchschn_transaktionshoehe=("amount", "mean"),
            einzigartige_kaeufer=("client_id", "nunique")
        ).reset_index()
        kpi_df["durchschn_transaktionen_pro_kaeufer"] = kpi_df["anzahl_transaktionen"] / kpi_df["einzigartige_kaeufer"]
        #Sortiere nach Umsatz (absteigend)
        kpi_df = kpi_df.sort_values(by="gesamtumsatz", ascending=False)
        # Formatierungen
        kpi_df["gesamtumsatz"] = kpi_df["gesamtumsatz"].map(lambda x: f"{x:,.2f} $".replace(",", "X").replace(".", ",").replace("X", "."))
        kpi_df["durchschn_transaktionshoehe"] = kpi_df["durchschn_transaktionshoehe"].map(lambda x: f"{x:,.2f} $".replace(",", "X").replace(".", ",").replace("X", "."))
        kpi_df["durchschn_transaktionen_pro_kaeufer"] = kpi_df["durchschn_transaktionen_pro_kaeufer"].map(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        columns = [
            ("merchant_state", "Bundesstaat"),
            ("gesamtumsatz", "Gesamtumsatz"),
            ("anzahl_transaktionen", "Anzahl Transaktionen"),
            ("durchschn_transaktionshoehe", "Ø Transaktionshöhe"),
            ("einzigartige_kaeufer", "Einzigartige Käufer"),
            ("durchschn_transaktionen_pro_kaeufer", "Ø Transaktionen/Käufer"),
        ]

        table = html.Table([
                    html.Thead([
                        html.Tr([html.Th(name) for _, name in columns])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(row[col]) for col, _ in columns
                        ]) for _, row in kpi_df.iterrows()
                    ])
                ], className="table table-hover table-bordered w-100")

        return html.Div([
            html.Div("KPIs je Bundesstaat für das Unternehmen", className="fw-bold mb-2"),
            table
        ], className="w-100 overflow-scroll")


@app.callback(
    Output("detail-view5", "children"),
    Input("category_dropdown", "value"),
    Input('timed_transaction_data', 'data'),
    Input('timed_branchen_transaction_data', 'data'),
    Input('timed_unternehmen_transaction_data', 'data'),
    Input("entity_dropdown", "value"),
    Input("date-range-start", "start_date"),
    Input("date-range-start", "end_date"),
)
def render_detailview5(category, timed_transaction_data, timed_branchen_data, timed_unternehmen_data, entity, start_date_first, end_date_first):
    
    if timed_transaction_data is None:
        return dbc.Alert("Keine Transaktionsdaten verfügbar.", color="warning")

    df = pd.DataFrame(timed_transaction_data)
    timed_unternehmen_data = pd.DataFrame(timed_unternehmen_data)
    timed_branchen_data = pd.DataFrame(timed_branchen_data)
    df['date'] = pd.to_datetime(df['date'])
    
    if category == 'Branchen' and timed_branchen_data is not None:
        
        # =======================
        
        persona_cards = dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Durchschnittsalter der Kunden", className="card-title"),
                        
                        # Zahl
                        html.P(
                            f"{get_average_age_in_branche(start_date_first, end_date_first, entity)} Jahre",
                            className="fs-4 fw-bold"
                        ),
                        

                        # Histogramm darunter
                        dcc.Graph(
                            figure=create_age_histogram(start_date_first, end_date_first, entity),
                            config={"displayModeBar": False},
                            style={"height": "200px"},
                            className="w-100"
                        ),

                        html.P("Hinweis: Altersverteilung aller Kunden, die im Zeitraum in dieser Branche aktiv waren.", className="info")
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Durchschnittliches Einkommen ($)", className="card-title"),
                            html.P(
                                avg_income := calculate_avg_income_for_branche(entity, df),
                                className="card-text fw-bold"
                            ),
                                    income_category_bar_component(avg_income, start_date_first, end_date_first, entity)

                        ], className="persona-card")
                    ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Ø Monatsausgaben pro Kunde in dieser Branche (im ausgewählten Zeitraum)", className="card-title"),
                        html.P(
                            calculate_mean_monthly_spending_per_customer(entity, df),
                            className="card-text"
                        ),
                        dcc.Graph(
                            figure=get_customer_spending_distribution_pie_chart(start_date_first, end_date_first, entity, df),
                            config={"displayModeBar": False},
                            style={"height": "200px"},
                            className="w-100"
                        ),
                        html.P("Hinweis: Nur Kunden berücksichtigt, die im gewählten Zeitraum in dieser Branche aktiv waren. Im Kreisdiagramm: Verteilung ihrer Gesamtausgaben über alle Branchen.", className="info")
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Kartennutzung nach Typ & Marke", className="card-title"),
                        dcc.Graph(figure=plot_card_type_distribution_by_brand(entity, df), style={"height": "200px"}, className="w-100"),
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Geschlechterverteilung", className="card-title"),
                        dcc.Graph(figure=get_dominant_gender_in_branche(entity, df), config={"displayModeBar": False}, style={"height": "200px"}, className="w-100"),
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
                        
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Durchschnittlicher Credit Score", className="card-title"),
                        dcc.Graph(
                            figure=erstelle_kredit_score_anzeige(get_average_credit_score_in_branche(entity, df)),
                            config={"displayModeBar": False},
                            style={"height": "200px"},
                            className="w-100"
                        )
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
        ], className="g-2")
    
        return dbc.Col([
                    persona_cards,
                ], width=12, className="d-flex flex-column gap-3 p-3 pb-5")

@app.callback(
    Output("branche_title", "children"),
    Output("branche_title2", "children"),
    Output("branche_title4", "children"),
    Output("branche_title5", "children"),
    Input("category_dropdown", "value"),
    Input("entity_dropdown", "value"),
)
def update_detailView(category, entity):
    if category == 'Branchen' and entity is not None:
        beschreibung = mcc_codes_data.loc[
            mcc_codes_data["mcc_code"] == entity, "description"
        ].values

        if beschreibung.size > 0:
            value = f"{entity} – {beschreibung[0]}"
        else:
            value = f"{entity} – Beschreibung nicht gefunden"
        # Gib immer ein Tupel mit drei gleichen Strings zurück!
        return value, value, value, value
    if category == 'Unternehmen' and entity is not None:
        value = f"Unternehmensprofil: {entity}"
        return value, value, value, value
    return "", "", "", ""

def calculate_avg_income_for_branche(mcc_code, timed_transaction_data):
   

    users_data['id'] = users_data['id'].astype(str)

    # Nach Datum und Branche filtern
    filtered_tx = timed_transaction_data[
        (transaction_data['mcc'] == int(mcc_code))
    ]

    # Kunden-IDs
    unique_clients = filtered_tx['client_id'].dropna().astype(str).unique()

    matching_users = users_data[users_data['id'].astype(str).isin(unique_clients)]

    # Durchschnitt berechnen
    avg_income = matching_users['per_capita_income'].mean()

    # Errorhandling
    if pd.isna(avg_income):
        return "Keine Daten"

    # kürzen
    t_income = int(avg_income * 100) / 100

    # Ergebnis mit $ zurückgeben
    return f"{t_income:.2f} $"


def income_category_bar_component(avg_income_str):
    # Wenn keine Daten vorhanden sind
    if avg_income_str == "Keine Daten":
        return html.P("Keine Daten verfügbar.")

    # Zahl aus dem String holen (z. B. "12345.67 $")
    income_value = float(avg_income_str.replace(" $", "").replace(",", ""))

    # Skala von 0 bis 300.000$
    scale_min = 0
    scale_max = 300000

    # Position auf der Skala berechnen (in %)
    relative_pos = ((income_value - scale_min) / (scale_max - scale_min)) * 100
    relative_pos = max(0, min(relative_pos, 100))  # Begrenzen zwischen 0 und 100 %

    color_segments, categories = get_income_category_colors_and_labels(EINKOMMENSKLASSEN)



    return html.Div([
        # Farbige Skala und Pfeil anzeigen
        html.Div([
            html.Div(
                [html.Div(style={
                    "flex": "1",
                    "height": "10px",
                    "backgroundColor": color
                }) for color in color_segments],
                style={"display": "flex", "width": "100%"}
            ),
            html.Div("▲", style={
                "position": "absolute",
                "left": f"{relative_pos:.2f}%",
                "transform": "translateX(-50%)",
                "top": "-12px",
                "fontSize": "1.2rem"
            })
        ], style={"position": "relative", "height": "25px", "marginTop": "10px"}),

        # Legende mit den Einkommensgruppen
        html.Ul([
            html.Li(cat, style={"fontSize": "0.8rem"})
            for cat in categories
        ], style={"paddingLeft": "1rem", "marginTop": "10px"})
    ])
    
def calculate_avg_income_for_branche(mcc_code, timed_transaction_data):
   

    users_data['id'] = users_data['id'].astype(str)

    # Nach Datum und Branche filtern
    filtered_tx = timed_transaction_data[
        (transaction_data['mcc'] == int(mcc_code))
    ]

    # Kunden-IDs
    unique_clients = filtered_tx['client_id'].dropna().astype(str).unique()

    matching_users = users_data[users_data['id'].astype(str).isin(unique_clients)]

    # Durchschnitt berechnen
    avg_income = matching_users['per_capita_income'].mean()

    # Errorhandling
    if pd.isna(avg_income):
        return "Keine Daten"

    # kürzen
    t_income = int(avg_income * 100) / 100

    # Ergebnis mit $ zurückgeben
    return f"{t_income:.2f} $"
    
def income_category_bar_component(avg_income_str, start_date, end_date, mcc_code):
    if avg_income_str == "Keine Daten":
        return html.P("Keine Daten verfügbar.")

    income_value = float(avg_income_str.replace(" $", "").replace(",", ""))

    # hole alle Kunden in der Branche und Zeitraum
    transaction_data['date'] = pd.to_datetime(transaction_data['date'])
    df_tx = transaction_data[
        (transaction_data['date'] >= pd.to_datetime(start_date)) &
        (transaction_data['date'] <= pd.to_datetime(end_date)) &
        (transaction_data['mcc'] == int(mcc_code)) &
        (transaction_data['client_id'].notna())
    ]

    if df_tx.empty:
        return html.P("Keine Transaktionsdaten verfügbar.")

    # hole die passenden User-Daten
    unique_clients = df_tx['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].astype(str).isin(unique_clients)].copy()

    if matched_users.empty or 'per_capita_income' not in matched_users.columns:
        return html.P("Keine Nutzerinformationen verfügbar.")

    # klassifiziere pro Kunde → in welche Klasse fällt er
    def assign_class(income):
        for i, klass in enumerate(EINKOMMENSKLASSEN):
            if klass['min'] <= income <= klass['max']:
                return i
        return None

    matched_users['class_idx'] = matched_users['per_capita_income'].apply(assign_class)

    # Anzahl Kunden pro Klasse
    class_counts = matched_users['class_idx'].value_counts().sort_index()
    total_clients = class_counts.sum()

    # berechne % pro Klasse
    class_percents = class_counts / total_clients * 100

    #  berechne Dreieck-Position
    cumulative_percent = 0
    triangle_position_percent = 0

    for idx, klass in enumerate(EINKOMMENSKLASSEN):
        class_percent_span = class_percents.get(idx, 0)

        if klass['min'] <= income_value <= klass['max']:
            # innerhalb dieser Klasse
            within_class_percent = 0
            klass_span = klass['max'] - klass['min']
            if klass_span > 0:
                within_class_percent = ((income_value - klass['min']) / klass_span) * class_percent_span
            triangle_position_percent = cumulative_percent + within_class_percent
            break
        else:
            cumulative_percent += class_percent_span

    # Skalenanzeige
    color_bars = []
    hover_texts = []
    for idx, klass in enumerate(EINKOMMENSKLASSEN):
        percent = class_percents.get(idx, 0)
        count = class_counts.get(idx, 0)
        hover_text = f"{klass['label']}: {count} Kunden ({percent:.2f} %)"
        color_bars.append(
            html.Div(
                style={
                    "flex": f"{percent}",
                    "height": "10px",
                    "backgroundColor": klass['color'],
                    "position": "relative"
                },
                title=hover_text
            )
        )

    return html.Div([
        html.Div([
            html.Div(color_bars, style={"display": "flex", "width": "100%"}),
            html.Div("▲", style={
                "position": "absolute",
                "left": f"{triangle_position_percent:.2f}%",
                "transform": "translateX(-50%)",
                "top": "-12px",
                "fontSize": "1.2rem"
            })
        ], style={"position": "relative", "height": "25px", "marginTop": "10px"}),

        # Legende
        html.Ul([
            html.Li(f"{klass['label']}: {klass['min']:,} $ – {klass['max']:,} $", style={"fontSize": "0.8rem"})
            for klass in EINKOMMENSKLASSEN
        ], style={"paddingLeft": "1rem", "marginTop": "10px"})
    ])

def calculate_mean_monthly_spending_per_customer(mcc_code, timed_transaction_data):
    df = timed_transaction_data

    df['date'] = pd.to_datetime(df['date'])

    df = df[
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    if df.empty:
        return "Keine Daten"

    # Neue Spalte: Jahr + Monat
    df['year_month'] = df['date'].dt.to_period('M')

    # Summe pro Kunde
    total_by_client = df.groupby('client_id')['amount'].sum()

    # Anzahl Monate pro Kunde
    months_by_client = df.groupby('client_id')['year_month'].nunique()

    # Durchschnitt pro Monat
    monthly_avg = total_by_client / months_by_client

    if monthly_avg.empty:
        return "Keine Daten"

    # Durchschnitt aller Kunden
    mean_value = monthly_avg.mean()

    # Kürzen auf 2 Nachkommastellen
    truncated = int(mean_value * 100) / 100

    return f"{truncated:.2f} $"

def get_customer_spending_distribution_pie_chart(start_date, end_date, current_mcc_code, timed_transaction_data):
    df = timed_transaction_data
    df['date'] = pd.to_datetime(df['date'])

    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['client_id'].notna())
    ]

    if df.empty:
        return go.Figure()

    #  Kunden filtern → nur Kunden aktiv in aktueller Branche
    df_branche = df[df['mcc'] == int(current_mcc_code)]
    kunden_in_branche = df_branche['client_id'].unique()

    if len(kunden_in_branche) == 0:
        return go.Figure()

    # Transaktionen aller MCCs dieser Kunden
    df_clients = df[df['client_id'].isin(kunden_in_branche)].copy()
    df_clients['year_month'] = df_clients['date'].dt.to_period('M')

    # Anzahl Monate pro Kunde (egal wo aktiv)
    active_months_per_client = df_clients.groupby('client_id')['year_month'].nunique()

    # Gesamtausgaben pro Kunde und MCC
    total_spending_client_mcc = df_clients.groupby(['client_id', 'mcc'])['amount'].sum().reset_index()

    # Berechne Durchschnitt Monatsausgabe pro Kunde und MCC
    total_spending_client_mcc['active_months'] = total_spending_client_mcc['client_id'].map(active_months_per_client)
    total_spending_client_mcc['monthly_avg'] = total_spending_client_mcc['amount'] / total_spending_client_mcc['active_months']

    # Durchschnitt Monatsausgabe pro MCC → über alle Kunden
    avg_monthly_spending_mcc = total_spending_client_mcc.groupby('mcc')['monthly_avg'].mean().reset_index()

    total_avg_spending = avg_monthly_spending_mcc['monthly_avg'].sum()
    avg_monthly_spending_mcc['percent'] = avg_monthly_spending_mcc['monthly_avg'] / total_avg_spending * 100
    avg_monthly_spending_mcc['description'] = avg_monthly_spending_mcc['mcc'].astype(str).map(mcc_dict).fillna("Unbekannt")

    # Aktuelle Branche extrahieren
    current_row = avg_monthly_spending_mcc[avg_monthly_spending_mcc['mcc'] == int(current_mcc_code)]
    other_rows = avg_monthly_spending_mcc[avg_monthly_spending_mcc['mcc'] != int(current_mcc_code)]

    # Top 4 anderen Branchen
    top_4_others = other_rows.sort_values(by='monthly_avg', ascending=False).head(4)
    sonstige_rows = other_rows[~other_rows['mcc'].isin(top_4_others['mcc'])]

    # Pie-Chart Daten vorbereiten
    pie_data = pd.concat([current_row, top_4_others], ignore_index=True)
    sonstiges_amount = sonstige_rows['monthly_avg'].sum()
    sonstiges_percent = sonstiges_amount / total_avg_spending * 100

    labels = pie_data['description'].tolist()
    values = pie_data['monthly_avg'].tolist()
    hover_labels = [
        f"Branche: {row['description']}<br>MCC: {row['mcc']}<br>Ø Monatsausgabe: {row['monthly_avg']:,.2f} $<br>Prozent: {row['percent']:.2f} %"
        for _, row in pie_data.iterrows()
    ]
    ids = pie_data['mcc'].astype(str).tolist()

    # Sonstiges hinzufügen
    if sonstiges_amount > 0:
        labels.append("Sonstiges")
        values.append(sonstiges_amount)
        hover_labels.append(
            f"Sonstiges: Ø Monatsausgabe: {sonstiges_amount:,.2f} $ ({sonstiges_percent:.2f} %)"
        )
        ids.append("Sonstiges")

    num_segments = len(values)
    blues_colors = px.colors.sample_colorscale("Blues", [i/(num_segments-1) for i in range(num_segments)])

    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='none',
            hovertext=hover_labels,
            hoverinfo='text',
            hole=0.4,
            customdata=ids,
            sort=False,
            marker=dict(colors=blues_colors)
        )]
    )

    fig.update_layout(
        template='plotly_white',
        showlegend=False,
        dragmode='zoom',
        hovermode='closest',
        margin=dict(t=50, b=20, l=20, r=20),
    )

    print(f"DEBUG: Ø Monatsausgaben pro Kunde (nur aktiv in {current_mcc_code}): {total_avg_spending:.2f} $")
    return fig



def get_dominant_gender_in_branche(mcc_code, timed_transaction_data, show_full_distribution=False):
    # Daten kopieren
    df = timed_transaction_data
   
    users_data['id'] = users_data['id'].astype(str)

    # Transaktionen nach Datum und Branche filtern
    df = df[
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    # Wenn keine Transaktionen
    if df.empty:
        return "Keine Transaktionen im Zeitraum/MCC"

    # Kunden holen
    unique_clients = df['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)].copy()

  
    if matched_users.empty or 'gender' not in matched_users.columns:
        return "Keine Nutzerinformationen verfügbar"

    
    matched_users['gender'] = matched_users['gender'].str.lower()

    # Geschlecht zählen
    gender_counts = matched_users['gender'].value_counts()
    male = gender_counts.get('male', 0)
    female = gender_counts.get('female', 0)
    total = male + female 

    # Wenn keine Angaben, Hinweis zurückgeben
    if total == 0:
        fig = px.pie(
            names=["Keine Geschlechtsangaben"],
            values=[1]
        )
        fig.update_traces(textinfo="label")
        return fig

    percents = {
        "Männlich": male / total * 100,
        "Weiblich": female / total * 100
    }
    fig = px.pie(
        names=list(percents.keys()),
        values=list(percents.values()),
        color_discrete_sequence=blues_dark_to_light
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def get_average_age_in_branche(start_date, end_date, mcc_code):
    df = transaction_data
    df['date'] = pd.to_datetime(df['date'])
    users_data['id'] = users_data['id'].astype(str)

    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    if df.empty:
        return None

    unique_clients = df['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)].copy()

    if 'birth_year' not in matched_users.columns or 'birth_month' not in matched_users.columns:
        return None

    matched_users['birthdate'] = pd.to_datetime(
        matched_users['birth_year'].astype(str) + "-" +
        matched_users['birth_month'].astype(str).str.zfill(2) + "-01",
        errors='coerce'
    )
    matched_users = matched_users[matched_users['birthdate'].notna()]

    if matched_users.empty:
        return None

    reference_date = pd.to_datetime(end_date)
    matched_users['age'] = matched_users['birthdate'].apply(lambda b: (reference_date - b).days // 365)

    if matched_users['age'].empty:
        return None

    mean_age = matched_users['age'].mean()
    return int(mean_age * 100) / 100

def create_age_histogram(start_date, end_date, mcc_code):
    df = transaction_data
    df['date'] = pd.to_datetime(df['date'])
    users_data['id'] = users_data['id'].astype(str)

    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    if df.empty:
        return go.Figure()

    unique_clients = df['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)].copy()

    if 'birth_year' not in matched_users.columns or 'birth_month' not in matched_users.columns:
        return go.Figure()

    matched_users['birthdate'] = pd.to_datetime(
        matched_users['birth_year'].astype(str) + "-" +
        matched_users['birth_month'].astype(str).str.zfill(2) + "-01",
        errors='coerce'
    )
    matched_users = matched_users[matched_users['birthdate'].notna()]

    if matched_users.empty:
        return go.Figure()

    reference_date = pd.to_datetime(end_date)
    matched_users['age'] = matched_users['birthdate'].apply(lambda b: (reference_date - b).days // 365)

    fig = px.histogram(
        matched_users,
        x='age',
        nbins=20,
        labels={'age': 'Alter (Jahre)'}
    )

    fig.update_layout(
        template='plotly_white',
        height=250,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    return fig



def get_average_credit_score_in_branche(mcc_code, timed_transaction_data):
    # Daten kopieren
    df = timed_transaction_data

    users_data['id'] = users_data['id'].astype(str)

    # Nach Branche filtern
    df = df[
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    # Wenn keine Daten, dann nichts zurückgeben
    if df.empty:
        return None

    # Kunden-IDs sammeln
    unique_clients = df['client_id'].astype(str).unique()

    # Passende Nutzer finden
    matched_users = users_data[users_data['id'].isin(unique_clients)].copy()

    # Wenn keine Nutzer oder kein Score, dann nichts zurückgeben
    if matched_users.empty or 'credit_score' not in matched_users.columns:
        return None

    # Durchschnitt berechnen
    avg_credit = matched_users['credit_score'].mean()

    # Wenn kein Wert da, dann nichts zurückgeben
    if pd.isna(avg_credit):
        return None

    # Auf 2 Stellen kürzen
    return int(avg_credit * 100) / 100

#diagramm - tacho
def erstelle_kredit_score_anzeige(kredit_score_wert):
    if kredit_score_wert is None:
        kredit_score_wert = 0
        kredit_score_beschriftung = "Keine Daten"
    else:
        kredit_score_beschriftung = f"{kredit_score_wert} von 850"

    diagramm = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = kredit_score_wert,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [300, 850]},
            'bar': {'color': "darkblue"},
            'steps' : [
                {'range': [300, 580], 'color': "red"},
                {'range': [580, 670], 'color': "orange"},
                {'range': [670, 740], 'color': "yellow"},
                {'range': [740, 800], 'color': "lightgreen"},
                {'range': [800, 850], 'color': "green"}
            ],
        }
    ))

    diagramm.update_layout(
        margin=dict(t=30, b=20, l=20, r=20),
        height=250
    )

    return diagramm


def plot_card_type_distribution_by_brand(mcc_code, timed_transaction_data , show_percentage=False):
    # Kopiere die Transaktions- und Kartendaten
    df_tx = timed_transaction_data
    df_cards = cards_data

    # Filtere nach Datum, Branche (MCC) und gültigen IDs
    df_tx = df_tx[
        (df_tx['mcc'] == int(mcc_code)) &
        (df_tx['client_id'].notna()) &
        (df_tx['card_id'].notna())
    ]

    # Wenn keine Daten vorhanden sind, gib leere Grafik zurück
    if df_tx.empty:
        return go.Figure()

    # Verbinde Transaktionen mit Karteninformationen
    merged = df_tx.merge(df_cards, left_on='card_id', right_on='id', how='left')

    # Wenn keine relevanten Daten vorhanden sind, gib leere Grafik zurück
    if merged.empty or 'card_type' not in merged.columns or 'card_brand' not in merged.columns:
        return go.Figure()

    # Vereinheitliche Kartentyp-Bezeichnungen
    merged['card_type'] = merged['card_type'].str.lower().map({
        'debit': 'Debit',
        'credit': 'Kredit',
        'prepaid': 'Prepaid',
        'debit (prepaid)': 'Prepaid'
    }).fillna('Andere')

    # Vereinheitliche Markennamen
    merged['card_brand'] = merged['card_brand'].str.title()

    # Zähle Transaktionen pro Kartentyp und Marke
    grouped = merged.groupby(['card_brand', 'card_type']).size().reset_index(name='count')

   
    if show_percentage:
        # Berechne Prozent pro Marke
        total_per_brand = grouped.groupby('card_brand')['count'].transform('sum')
        grouped['percent'] = (grouped['count'] / total_per_brand) * 100
        # Kürze auf 2 Nachkommastellen
        grouped['percent'] = grouped['percent'].apply(lambda x: int(x * 100) / 100)
        y_val = 'percent'
        y_title = 'Anteil in %'
    else:
        y_val = 'count'
        y_title = 'Anzahl Transaktionen'

    # Erstelle Balkendiagramm mit Plotly
    fig = px.bar(
        grouped,
        x=y_val,                 # Wert auf X-Achse (Anzahl oder Prozent)
        y='card_brand',          # Marken auf Y-Achse
        color='card_type',       # Farbe nach Kartentyp
        orientation='h',         # Horizontal
        text_auto='.2s' if not show_percentage else None,  # Zeige Werte bei Anzahl
        labels={'card_type': 'Kartentyp', 'card_brand': 'Kartenmarke', y_val: y_title},
        color_discrete_sequence=blues_dark_to_light
    )

    # Layout-Einstellungen
    fig.update_layout(
        template='plotly_white',
        legend_title='Kartentyp',
        xaxis_title='Kartenmarke',
        yaxis_title=y_title,
        height=400
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)