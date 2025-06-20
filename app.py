# Imports
import json
import locale
import os
from urllib.request import urlopen
from dash import Dash, State, html, dash_table, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re
import plotly.graph_objects as go
import pandas as pd
import glob
import re
import duckdb



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
transaction_file = parquet_folder + "cleaned_transaction_data_500k.parquet"
#transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data_50k.csv", sep=',', encoding='utf-8')
# transaction_data = pd.read_parquet(parquet_folder + "cleaned_transaction_data_50k.parquet", columns=["id","date","client_id","card_id","amount","merchant_id","merchant_city","merchant_state","mcc"])
cards_data = pd.read_csv(data_folder + "cleaned_cards_data.csv")
users_data = pd.read_csv(data_folder + "cleaned_users_data.csv")
with open(data_folder + 'mcc_codes.json', 'r', encoding='utf-8') as f:
    mcc_dict = json.load(f)
mcc_codes_data = pd.DataFrame(list(mcc_dict.items()), columns=['mcc_code', 'description'])

# Annahme: Dateien heißen transactions_YYYY_MM.parquet
parquet_files = glob.glob(os.path.join(parquet_folder, "transactions_*.parquet"))

year_months = set()
for f in parquet_files:
    match = re.search(r'transactions_(\d{4})_(\d{2})\.parquet', f)
    if match:
        year_months.add((match.group(1), match.group(2)))
years = sorted({y for y, m in year_months})
months = sorted({m for y, m in year_months})

date_col = pd.read_parquet(transaction_file, columns=['date'])
min_date = pd.to_datetime(date_col['date']).min().strftime("%Y-%m-%d")
max_date = pd.to_datetime(date_col['date']).max().strftime("%Y-%m-%d")

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([ 
    dcc.Store(id='timed_transaction_data'),
    dcc.Store(id='timed_branchen_transaction_data'),
    dcc.Store(id='timed_unternehmen_transaction_data'),
    dbc.Row([
        dbc.Col([
            dbc.Col([
                html.Div([
                    dbc.Col([
                        dcc.Dropdown(
                            id='year_dropdown',
                            options=[{"label": y, "value": y} for y in years],
                            value=years[0],
                            className="time-dropdown",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Dropdown(
                            id='month_dropdown',
                            options=[{"label": m, "value": m} for m in months],
                            value=months[0],
                            className="time-dropdown",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Dropdown(
                            id='compare_period_dropdown',
                            options=[
                                {"label": "Letzter Monat", "value": "last_month"},
                                {"label": "Letzte 3 Monate", "value": "last_3_months"},
                                {"label": "Letzte 6 Monate", "value": "last_6_months"},
                                {"label": "Letztes Jahr", "value": "last_year"},
                            ],
                            value="last_month",
                            className="time-dropdown",
                            clearable=False,
                        ),
                    ], width=4),
                ], className="d-flex gap-2 w-100 flex-wrap justify-content-start"),

            ], width=12, id='zeitraum_container'),
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

def load_all_period_duckdb(year, month, compare_period, parquet_folder="./parquet_data/"):
    # Gleiches Perioden-Building wie oben
    periods = []
    year = int(year)
    month = int(month)
    if compare_period == "last_month":
        periods = [(year, month)]
    elif compare_period == "last_3_months":
        for i in range(3):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_6_months":
        for i in range(6):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_year":
        periods = [(year - 1, m) for m in range(1, 13)]
    else:
        periods = [(year, month)]

    parquet_files = [
        f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet"
        for y, m in periods
        if os.path.exists(f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet")
    ]
    if not parquet_files:
        return pd.DataFrame()

    con = duckdb.connect()
    query = f"""
        SELECT date, amount, merchant_id, mcc, client_id, merchant_city, merchant_state, card_id
        FROM read_parquet({parquet_files})
    """
    df = con.execute(query).df()
    con.close()
    return df

def load_unternehmen_period_duckdb(year, month, compare_period, entity, parquet_folder="./parquet_data/"):
    # Erzeuge Liste aller relevanten Parquet-Dateien
    periods = []
    year = int(year)
    month = int(month)
    if compare_period == "last_month":
        periods = [(year, month)]
    elif compare_period == "last_3_months":
        for i in range(3):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_6_months":
        for i in range(6):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_year":
        periods = [(year - 1, m) for m in range(1, 13)]
    else:
        periods = [(year, month)]

    parquet_files = [
        f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet"
        for y, m in periods
        if os.path.exists(f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet")
    ]
    if not parquet_files:
        return pd.DataFrame()

    con = duckdb.connect()
    query = f"""
        SELECT date, amount, merchant_id, mcc, client_id, merchant_city, merchant_state, card_id
        FROM read_parquet({parquet_files})
        WHERE merchant_id = {int(entity)}
    """
    df = con.execute(query).df()
    con.close()
    return df

def load_branchen_period_duckdb(year, month, compare_period, entity, parquet_folder="./parquet_data/"):
    # Erzeuge Liste aller relevanten Parquet-Dateien
    periods = []
    year = int(year)
    month = int(month)
    if compare_period == "last_month":
        periods = [(year, month)]
    elif compare_period == "last_3_months":
        for i in range(3):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_6_months":
        for i in range(6):
            y, m = divmod(month - i - 1, 12)
            periods.append((year + y, (m % 12) + 1))
    elif compare_period == "last_year":
        periods = [(year - 1, m) for m in range(1, 13)]
    else:
        periods = [(year, month)]

    parquet_files = [
        f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet"
        for y, m in periods
        if os.path.exists(f"{parquet_folder}/transactions_{y}_{str(m).zfill(2)}.parquet")
    ]
    if not parquet_files:
        return pd.DataFrame()

    con = duckdb.connect()
    query = f"""
        SELECT date, amount, merchant_id, mcc, client_id, merchant_city, merchant_state, card_id
        FROM read_parquet({parquet_files})
        WHERE mcc = {int(entity)}
    """
    df = con.execute(query).df()
    con.close()
    return df

@app.callback(
    Output('timed_branchen_transaction_data', 'data'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('compare_period_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value')
)
def update_timed_branchen_transaction_data(selected_year, selected_month, compare_period, category, entity):
    if category == 'Branchen' and entity is not None and selected_year and selected_month and compare_period:
        df = load_branchen_period_duckdb(selected_year, selected_month, compare_period, entity)
        return df.to_dict('records')
    elif category == 'Unternehmen' and entity is not None and selected_year and selected_month and compare_period:
        # Lade die Transaktionen des Unternehmens
        df_unternehmen = load_unternehmen_period_duckdb(selected_year, selected_month, compare_period, entity)
        # Ermittle die Branche (mcc) des Händlers
        if not df_unternehmen.empty and 'mcc' in df_unternehmen.columns:
            mcc = int(df_unternehmen['mcc'].iloc[0])
            # Lade alle Transaktionen dieser Branche im Zeitraum
            df_branche = load_branchen_period_duckdb(selected_year, selected_month, compare_period, mcc)
            return df_branche.to_dict('records')
    return []

@app.callback(
    Output('timed_unternehmen_transaction_data', 'data'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('compare_period_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value')
)
def update_timed_unternehmen_transaction_data(selected_year, selected_month, compare_period, category, entity):
    if category == 'Unternehmen' and entity and selected_year and selected_month and compare_period:
        df = load_unternehmen_period_duckdb(selected_year, selected_month, compare_period, entity)
        return df.to_dict('records')
    return []

@app.callback(
    Output('timed_transaction_data', 'data'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('compare_period_dropdown', 'value'),
)
def update_timed_transaction_data(selected_year, selected_month, compare_period):
    if not selected_year or not selected_month or not compare_period:
        return []
    df = load_all_period_duckdb(selected_year, selected_month, compare_period)
    return df.to_dict('records')

@callback(
    Output('map-container', 'children'),
    Input('timed_unternehmen_transaction_data', 'data'),
    Input('timed_branchen_transaction_data', 'data'),
    Input('entity_dropdown', 'value'),
    Input('category_dropdown', 'value'),
)
def renderMap(timed_unternehmen_transaction_data, timed_branchen_transaction_data, entity_value, category_value):
    # Wähle das passende, bereits gefilterte DataFrame
    if category_value == 'Branchen':
        data = timed_branchen_transaction_data
    elif category_value == 'Unternehmen':
        data = timed_unternehmen_transaction_data
    else:
        data = None

    if data is None or entity_value is None or len(data) == 0:
        return dbc.Alert("Keine Daten im gewählten Zeitraum.", color="warning")

    df_filtered = pd.DataFrame(data)
    if df_filtered.empty:
        return dbc.Alert("Keine Daten im gewählten Zeitraum.", color="warning")

    geo_col = country_config['geo_column']
    scope = country_config['scope']
    location_mode = country_config.get('location_mode', None)

    # Gruppiere nach Bundesstaat und berechne Umsatz
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
    merchant_ids = pd.read_parquet(transaction_file, columns=['merchant_id'])['merchant_id'].drop_duplicates()
    return [{"label": str(m), "value": str(m)} for m in sorted(merchant_ids)]

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
   
def handle_unternehmen(df_merchant, df_branche_of_merchant, entity_value):

    merchant_id = int(entity_value)

    if df_merchant.empty:
        return dbc.Alert("Keine Daten für dieses Unternehmen verfügbar.", color="warning")

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
    branche_umsatz = df_branche_of_merchant['amount'].sum() if 'mcc' in df_merchant.columns else 0
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
        df_merchant.groupby('merchant_state')['amount']
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

def handle_branchen(df_branche):

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
    Input('timed_unternehmen_transaction_data', 'data'),
    Input('timed_branchen_transaction_data', 'data'),
)
def update_right_section(category, entity_value, timed_unternehmen_transaction_data, timed_branchen_transaction_data):
    if timed_unternehmen_transaction_data is None or entity_value is None:
        return None


    if category == 'Unternehmen':
        df_merchant = pd.DataFrame(timed_unternehmen_transaction_data)
        df_branche = pd.DataFrame(timed_branchen_transaction_data)
        return handle_unternehmen(df_merchant, df_branche, entity_value)

    if category == 'Branchen':
        df = pd.DataFrame(timed_branchen_transaction_data)
        return handle_branchen(df)

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

def process_branchen_data(timed_branchen_data):
    timed_branchen_data["year"] = pd.to_datetime(timed_branchen_data["date"]).dt.year
    umsatz_Jahr_Merchant = timed_branchen_data.groupby(["year", "merchant_id"])["amount"].sum().reset_index(name="Umsatz_im_Jahr")
    umsatz_pro_merchant = umsatz_Jahr_Merchant.groupby("merchant_id")["Umsatz_im_Jahr"].sum().reset_index(name="gesamtumsatz")
    return umsatz_Jahr_Merchant, umsatz_pro_merchant

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
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('timed_transaction_data', 'data'),
    Input('timed_unternehmen_transaction_data', 'data'),
    Input('timed_branchen_transaction_data', 'data'),

)
def render_detailview(category, entity, selected_year, selected_month, timed_transaction_data, timed_unternehmen_data, timed_branchen_data):
    if timed_transaction_data is None:
        return dbc.Alert("Keine Transaktionsdaten verfügbar.", color="warning")

    df = pd.DataFrame(timed_transaction_data)
    timed_unternehmen_data = pd.DataFrame(timed_unternehmen_data)
    timed_branchen_data = pd.DataFrame(timed_branchen_data)
    df['date'] = pd.to_datetime(df['date'])

    if category == 'Branchen' and entity is not None:
        
        
        # =======================

        umsatz_Jahr_Merchant, umsatz_pro_merchant = process_branchen_data(timed_branchen_data)
        top_5 = umsatz_pro_merchant.nlargest(5, 'gesamtumsatz')
        flop_5 = umsatz_pro_merchant.nsmallest(5, 'gesamtumsatz')
        fig1, fig2 = create_branchen_charts(umsatz_Jahr_Merchant, top_5, flop_5)

        # =================== Online Umsatzanteil =====================

        online_transaktionen = timed_branchen_data[timed_branchen_data['merchant_city'].str.upper() == 'ONLINE']
        online_umsatz = online_transaktionen['amount'].sum()
        gesamt_umsatz = timed_branchen_data['amount'].sum()

        if gesamt_umsatz > 0:
            online_umsatz_anteil = (online_umsatz / gesamt_umsatz) * 100
            online_umsatz_anteil_display = f"{online_umsatz_anteil:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            online_umsatz_anteil_display = "n/a"

        # =====================================================================================

        #Unique Customers
        EinzigartigeKäufer = timed_branchen_data["client_id"].nunique()

        #Marktkapitalisierung berechnet

        Marktkapitalisierung = umsatz_pro_merchant["gesamtumsatz"].sum()
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        # =====================================================================================


        #Durchschnitt der Transaktionen Pro Käufer - noch nicht fertig

        GesamtTransaktionen = timed_branchen_data["merchant_id"].count()
        EinzigartigeKäufer = timed_branchen_data["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer

        DurchschnittTransaktionenProKäufer = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")


        # =====================================================================================

        #Durchschnittliche Transaktionshöhe einer Transaktion in dem ausgewählten Zeitraum

        DurchschnittTransaktionshöhe = timed_branchen_data['amount'].mean()
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} $ ".replace(",", "X").replace(".", ",").replace("X", ".")


        # =====================================================================================
        
        #Consumer Money Spent (%)

        gesamt_ausgaben_pro_client = pd.read_parquet("./parquet_data/gesamt_ausgaben_pro_client.parquet")
        # Ein einzelner Wert, der den durchschnittlichen Betrag angibt, den ein Kunde insgesamt ausgegeben hat.
        Durchschnitt_gesamt = gesamt_ausgaben_pro_client['gesamt_ausgaben'].mean()
        BranchenAusgabenProClient = timed_branchen_data.groupby("client_id")["amount"].sum()
        DurchschnittBranche = BranchenAusgabenProClient.mean()

        ConsumerMoneySpent= (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpent = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")


        # =====================================================================================

        # Umsatzwachstum: Nur Startmonat vs. Endmonat vergleichen
        umsatzwachstum_display = "n/a"
        if not timed_branchen_data.empty and 'date' in timed_branchen_data.columns:
            timed_branchen_data['date'] = pd.to_datetime(timed_branchen_data['date'])
            timed_branchen_data['year_month'] = timed_branchen_data['date'].dt.to_period('M')

            # Finde Start- und Endmonat im aktuellen Zeitraum
            min_month = timed_branchen_data['year_month'].min()
            max_month = timed_branchen_data['year_month'].max()

            # Umsatz im Start- und Endmonat berechnen
            umsatz_start = timed_branchen_data[timed_branchen_data['year_month'] == min_month]['amount'].sum()
            umsatz_end = timed_branchen_data[timed_branchen_data['year_month'] == max_month]['amount'].sum()

            if umsatz_start > 0:
                umsatzwachstum = ((umsatz_end - umsatz_start) / umsatz_start) * 100
                umsatzwachstum_display = f"{umsatzwachstum:,.2f} %".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                umsatzwachstum_display = "n/a"

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
                ], md=9, sm=12, className="detail-view-right-section"),
        ]

    if category == 'Unternehmen' and entity is not None:

        gesamt_ausgaben_pro_client = pd.read_parquet("./parquet_data/gesamt_ausgaben_pro_client.parquet")

        # Umsatz pro Monat berechnen
        if timed_unternehmen_data.empty or 'date' not in timed_unternehmen_data.columns:
            return dbc.Alert("Keine Transaktionsdaten oder kein Datum für das Unternehmen verfügbar.", color="warning")
        timed_unternehmen_data['month'] = pd.to_datetime(timed_unternehmen_data['date']).dt.to_period('M')
        umsatz_pro_monat = timed_unternehmen_data.groupby('month')['amount'].sum().reset_index()
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
        Marktkapitalisierung = timed_unternehmen_data["amount"].sum()
        MarktkapitalisierungDisplay = f"{Marktkapitalisierung:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        DurchschnittTransaktionshöhe = timed_unternehmen_data['amount'].mean()
        DurchschnittTransaktionshöheDisplay = f"{DurchschnittTransaktionshöhe:,.2f} $ ".replace(",", "X").replace(".", ",").replace("X", ".")

        GesamtTransaktionen = timed_unternehmen_data["merchant_id"].count()
        EinzigartigeKäufer = timed_unternehmen_data["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer
        DurchschnittTransaktionenProKäuferDisplay = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

        Durchschnitt_gesamt = gesamt_ausgaben_pro_client['gesamt_ausgaben'].mean()
        UnternehmensAusgabenProClient = timed_unternehmen_data.groupby("client_id")["amount"].sum()

        DurchschnittBranche = UnternehmensAusgabenProClient.mean()
        ConsumerMoneySpent = (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpentDisplay = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

        CustomerLifetimeValue = Durchschnitt_gesamt / EinzigartigeKäufer * 100
        CustomerLifetimeValueDisplay = f"{CustomerLifetimeValue:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

        bundesstaat_transaktionen = timed_unternehmen_data.groupby('merchant_state')['merchant_id'].count().reset_index(name='transaction_count')


        

        # =====================


    
        #MarktkapitalisierungUnternehmen = unternehmen_transaktionen["amount"].sum()
        if not timed_unternehmen_data.empty and 'mcc' in timed_unternehmen_data.columns:
            unternehmen_mcc = timed_unternehmen_data['mcc'].iloc[0]
            unternehmen_mcc = int(unternehmen_mcc)
        else:
            unternehmen_mcc = None
        GesamtMarktkapitalisierungBranche = df[df['mcc'] == unternehmen_mcc]["amount"].sum()
        
        branchenbeschreibung = mcc_codes_data.loc[
            mcc_codes_data["mcc_code"] == str(unternehmen_mcc), "description"
        ].values
        branchenbeschreibung = branchenbeschreibung[0] if len(branchenbeschreibung) > 0 else "Unbekannte Branche"

        #Transaktionshöhe anzahl pro Bereich 
        if not timed_unternehmen_data.empty and 'amount' in timed_unternehmen_data.columns:
            ErsterPreisbereich = timed_unternehmen_data[timed_unternehmen_data['amount'] < 50]['amount'].count()
            ZweiterPreisbereich = timed_unternehmen_data[(timed_unternehmen_data['amount'] >= 50) & (timed_unternehmen_data['amount'] <= 200)]['amount'].count()
            DritterPreisbereich = timed_unternehmen_data[timed_unternehmen_data['amount'] > 200]['amount'].count()
        else:
            ErsterPreisbereich = ZweiterPreisbereich = DritterPreisbereich = 0

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
                       dbc.Col([
                            dbc.Col([
                                dcc.Graph(figure=fig_pie, className="w-100"),
                            ], width=6),
                            dbc.Col([
                                dcc.Graph(figure=fig_pie_2, className="w-100"),
                            ], width=6),
                        ], width=12, id="gesamtkapitalisierung_container", className="d-flex justify-content-between align-content-start p-3 overflow-y-scroll"),
                    ], width=12),
                ], width=12, className="detail-view-right-section-4 d-flex"),
            ], md=9, sm=12, className="detail-view-right-section")
        ]

@app.callback(
    Output("detail-view2", "children"),
    Input("category_dropdown", "value"),
    Input('timed_branchen_transaction_data', 'data'),
)
def render_detailview2(category, timed_branchen_data):  # Tabelle für Branchen mit KPIs
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
    Input('timed_unternehmen_transaction_data', 'data'),
)
def render_detailview4(category, timed_unternehmen_data): # Tabelle für Unternehmen mit KPIs
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


# Personas für Branchen 
@app.callback(
    Output("detail-view5", "children"),
    Input("category_dropdown", "value"),
    Input('timed_branchen_transaction_data', 'data'),
    Input("entity_dropdown", "value"),
    Input("year_dropdown", "value"),
    Input("month_dropdown", "value"),
)
def render_detailview5(category, timed_branchen_data, entity, selected_year, selected_month):
    if timed_branchen_data is None:
        return dbc.Alert("Keine Transaktionsdaten verfügbar.", color="warning")

    timed_branchen_data = pd.DataFrame(timed_branchen_data)
    if 'date' in timed_branchen_data.columns:
        timed_branchen_data['date'] = pd.to_datetime(timed_branchen_data['date'])
    else:
        return dbc.Alert("Keine Datumsinformationen verfügbar.", color="warning")

    if category == 'Branchen' and timed_branchen_data is not None:
        persona_cards = dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Durchschnittsalter der Kunden", className="card-title"),
                        html.P(
                            f"{get_average_age_in_branche(selected_year, selected_month, entity, timed_branchen_data)} Jahre",
                            className="fs-4 fw-bold"
                        ),
                        dcc.Graph(
                            figure=create_age_histogram(selected_year, selected_month, entity, timed_branchen_data),
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
                            avg_income := calculate_avg_income_for_branche(timed_branchen_data),
                            className="card-text fw-bold"
                        ),
                        income_category_bar_component(avg_income, timed_branchen_data)
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Ø Monatsausgaben pro Kunde in dieser Branche (im ausgewählten Zeitraum)", className="card-title"),
                        html.P(
                            calculate_mean_monthly_spending_per_customer(timed_branchen_data),
                            className="card-text"
                        ),
                        dcc.Graph(
                            figure=get_customer_spending_distribution_pie_chart(entity, timed_branchen_data),
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
                        dcc.Graph(figure=plot_card_type_distribution_by_brand(timed_branchen_data), style={"height": "200px"}, className="w-100"),
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Geschlechterverteilung", className="card-title"),
                        dcc.Graph(figure=get_dominant_gender_in_branche(timed_branchen_data), config={"displayModeBar": False}, style={"height": "200px"}, className="w-100"),
                    ], className="persona-card")
                ], className="h-100")
            ], md=4, sm=12, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Durchschnittlicher Credit Score", className="card-title"),
                        dcc.Graph(
                            figure=erstelle_kredit_score_anzeige(get_average_credit_score_in_branche(timed_branchen_data)),
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


def calculate_avg_income_for_branche(timed_branchen_data):

    users_data['id'] = users_data['id'].astype(str)

    unique_clients = timed_branchen_data['client_id'].dropna().astype(str).unique()

    matching_users = users_data[users_data['id'].astype(str).isin(unique_clients)]

    avg_income = matching_users['per_capita_income'].mean()

    if pd.isna(avg_income):
        return "Keine Daten"

    t_income = int(avg_income * 100) / 100

    # Ergebnis mit $ zurückgeben
    return f"{t_income:.2f} $"
    
def income_category_bar_component(avg_income_str, timed_branchen_data):
    if avg_income_str == "Keine Daten":
        return html.P("Keine Daten verfügbar.")

    income_value = float(avg_income_str.replace(" $", "").replace(",", ""))

    if timed_branchen_data.empty:
        return html.P("Keine Transaktionsdaten verfügbar.")

    # hole die passenden User-Daten
    unique_clients = timed_branchen_data['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].astype(str).isin(unique_clients)]

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

def calculate_mean_monthly_spending_per_customer(timed_branchen_data):

    if timed_branchen_data.empty:
        return "Keine Daten"

    # Neue Spalte: Jahr + Monat
    timed_branchen_data['year_month'] = timed_branchen_data['date'].dt.to_period('M')

    # Summe pro Kunde
    total_by_client = timed_branchen_data.groupby('client_id')['amount'].sum()

    # Anzahl Monate pro Kunde
    months_by_client = timed_branchen_data.groupby('client_id')['year_month'].nunique()

    # Durchschnitt pro Monat
    monthly_avg = total_by_client / months_by_client

    if monthly_avg.empty:
        return "Keine Daten"

    # Durchschnitt aller Kunden
    mean_value = monthly_avg.mean()

    # Kürzen auf 2 Nachkommastellen
    truncated = int(mean_value * 100) / 100

    return f"{truncated:.2f} $"

def get_customer_spending_distribution_pie_chart(current_mcc_code, timed_branchen_data):
    if timed_branchen_data.empty:
        return go.Figure()

    #  Kunden filtern → nur Kunden aktiv in aktueller Branche
    df_branche = timed_branchen_data[timed_branchen_data['mcc'] == int(current_mcc_code)]
    kunden_in_branche = df_branche['client_id'].unique()

    if len(kunden_in_branche) == 0:
        return go.Figure()

    # Transaktionen aller MCCs dieser Kunden
    df_clients = timed_branchen_data[timed_branchen_data['client_id'].isin(kunden_in_branche)]
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

    if len(values) > 1:
        blues_colors = px.colors.sample_colorscale("Blues", [i/(len(values)-1) for i in range(len(values))])
    else:
        blues_colors = [px.colors.sample_colorscale("Blues", [0.5])[0]]

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

    return fig



def get_dominant_gender_in_branche(timed_branchen_data):
   
    users_data['id'] = users_data['id'].astype(str)

    # Wenn keine Transaktionen
    if timed_branchen_data.empty:
        return "Keine Transaktionen im Zeitraum/MCC"

    # Kunden holen
    unique_clients = timed_branchen_data['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)]

  
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

def get_average_age_in_branche(selected_year, selected_month, mcc_code, timed_branchen_data):
    df = timed_branchen_data
    users_data['id'] = users_data['id'].astype(str)

    if df.empty:
        return None

    unique_clients = df['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)]

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

    # Nutze das ausgewählte Jahr und den Monat als Referenzdatum
    try:
        reference_date = pd.Timestamp(year=int(selected_year), month=int(selected_month), day=1)
    except Exception:
        return None

    matched_users['age'] = matched_users['birthdate'].apply(lambda b: (reference_date - b).days // 365)

    if matched_users['age'].empty:
        return None

    mean_age = matched_users['age'].mean()
    return int(mean_age * 100) / 100

def create_age_histogram(selected_year, selected_month, mcc_code, timed_branchen_data):
    timed_branchen_data['date'] = pd.to_datetime(timed_branchen_data['date'])
    users_data['id'] = users_data['id'].astype(str)

    if timed_branchen_data.empty:
        return go.Figure()

    unique_clients = timed_branchen_data['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)]

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

    # Nutze das ausgewählte Jahr und den Monat als Referenzdatum
    try:
        reference_date = pd.Timestamp(year=int(selected_year), month=int(selected_month), day=1)
    except Exception:
        return go.Figure()

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



def get_average_credit_score_in_branche(timed_branchen_data):

    users_data['id'] = users_data['id'].astype(str)

    # Wenn keine Daten, dann nichts zurückgeben
    if timed_branchen_data.empty:
        return None

    # Kunden-IDs sammeln
    unique_clients = timed_branchen_data['client_id'].astype(str).unique()

    # Passende Nutzer finden
    matched_users = users_data[users_data['id'].isin(unique_clients)]

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


def plot_card_type_distribution_by_brand(timed_branchen_data , show_percentage=False):

    # Wenn keine Daten vorhanden sind, gib leere Grafik zurück
    if timed_branchen_data.empty:
        return go.Figure()

    # Verbinde Transaktionen mit Karteninformationen
    merged = timed_branchen_data.merge(cards_data, left_on='card_id', right_on='id', how='left')

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