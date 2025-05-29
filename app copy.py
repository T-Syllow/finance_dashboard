# Imports
import json
from urllib.request import urlopen
from dash import Dash, html, dash_table, Input, Output, callback, dcc, State
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import re
import plotly.graph_objects as go


with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

counties["features"][0] 

country_config = {
    'scope': 'usa',
    'geo_column': 'merchant_state',
    'location_mode': 'USA-states'
}

# --- Read in data ---
data_folder = "newData/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data.csv", sep=",", encoding="utf8")
cards_data = pd.read_csv(data_folder + "cards_data.csv", sep=",", encoding="utf8")
users_data = pd.read_csv(data_folder + "users_data.csv", sep=",", encoding="utf8")
with open(data_folder + 'mcc_codes.json', 'r', encoding='utf-8') as f:
    mcc_dict = json.load(f)
mcc_codes_data = pd.DataFrame(list(mcc_dict.items()), columns=['mcc_code', 'description'])
merchant_stats = pd.read_csv(data_folder + "merchant_stats.csv", sep=",", encoding="utf8")

# Sicherstellen, dass 'date' Spalte ein Datetime-Objekt ist
transaction_data['date'] = pd.to_datetime(transaction_data['date'], errors='coerce')

# alle Händler
merchants = transaction_data['merchant_id'].unique()

# Jede Transaktion hat eine Merchant_id und einen mcc_code --> Dataframe
merchant_mcc_relations = transaction_data[['merchant_id', 'mcc']].copy()

# Händler Kategorien (Klartext)
merchant_categories = mcc_codes_data['description'].unique().tolist()

# Händler Kategorie Codes (ID)
merchant_branche_codes = mcc_codes_data['mcc_code'].unique()

state_counts = transaction_data.groupby("merchant_state").size().reset_index(name="transaction_count")

# ALLE STANDARDWERTE FÜR UN-FILTER
min_niederlassungen = int(merchant_stats['niederlassungen'].min())
max_niederlassungen = int(merchant_stats['niederlassungen'].max())

min_avg_transaction = float(merchant_stats['avg_transaction'].min())
max_avg_transaction = float(merchant_stats['avg_transaction'].max())

min_revenue = float(merchant_stats['revenue'].min())
max_revenue = float(merchant_stats['revenue'].max())

# Beginn Layout
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([
    dbc.Row([
        html.Div('Finance Table Transaction Data', className="text-primary text-center fs-3")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Col([
                dcc.DatePickerRange(
                    id='main-date-range', # Geändert zu einer einzigen, eindeutigen ID
                    min_date_allowed=transaction_data['date'].min(),
                    max_date_allowed=transaction_data['date'].max(),
                    start_date=transaction_data['date'].min(),
                    end_date=transaction_data['date'].max(),
                    className=""
                ),
            ], width=12, className="gap-5", id='zeitraum_container'),
            dbc.Col([
                dbc.Col([
                    dcc.Dropdown(['Unternehmen', 'Branchen'], 'Branchen', id='category_dropdown')
                ], width=3),
                dbc.Col([
                    dcc.Dropdown(id='entity_dropdown',
                        # Initial Wert
                        options=[{"label": cat, "value": str(mcc)} for mcc, cat in mcc_codes_data[["mcc_code", "description"]].drop_duplicates().values],
                        value='5411' # Initialwert Brancehn
                        ),
                    html.Div(id='additional-filters') # FILTER (Simon)
                ], width=8),
            ], width=12, className="d-flex py-2 gap-2 justify-content-start"),
        ], width=6, className="navbar"),
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id="map-graph") # explizite ID für das Graphen-Objekt
        ], width=6, className="d-flex justify-content-center align-items-center", id="map-container"),
        dbc.Col([
            dbc.Row([
            ], id="right_section")
        ], width=6),
    ]),
], fluid=True, className="body")


# Einklappbare Filter (HTML)----------------------------------------------------------------
@callback(
    Output('additional-filters', 'children'),
    Input('category_dropdown', 'value'),
)
def display_additional_filters(category_value):
    if category_value != 'Unternehmen':
        return None

    return dbc.Card([
        dbc.CardHeader(
            dbc.Button(
                "Erweiterte Filter anzeigen / ausblenden",
                id="toggle-filters-button",
                color="secondary",
                n_clicks=0,
                className="w-100"
            )
        ),
        dbc.Collapse(
            dbc.CardBody([

                # Niederlassungen
                dbc.Row([
                    dbc.Col(html.Label("Anzahl der Niederlassungen"), width=3, style={"textAlign": "right", "paddingTop": "10px"}),
                    dbc.Col(dcc.RangeSlider(
                        id='niederlassungen_range_slider',
                        min=min_niederlassungen,
                        max=max_niederlassungen,
                        step=1,
                        value=[min_niederlassungen, max_niederlassungen],
                        tooltip={"always_visible": False, "placement": "top"},
                        marks={
                            min_niederlassungen: str(min_niederlassungen),
                            max_niederlassungen: str(max_niederlassungen)
                        }
                    ), width=9),
                ], className="mb-3"),

                # durchschn. Transaktionshöhe
                dbc.Row([
                    dbc.Col(html.Label("Ø Transaktionshöhe (€)"), width=3, style={"textAlign": "right", "paddingTop": "10px"}),
                    dbc.Col(dcc.RangeSlider(
                        id='avg_transaction_range_slider',
                        min=min_avg_transaction,
                        max=max_avg_transaction,
                        step=10,
                        value=[min_avg_transaction, max_avg_transaction],
                        tooltip={"always_visible": False, "placement": "top"},
                        marks={
                            min_avg_transaction: str(min_avg_transaction),
                            max_avg_transaction: str(max_avg_transaction)
                        }
                    ), width=9),
                ], className="mb-3"),

                # Gesamtumsatz
                dbc.Row([
                    dbc.Col(html.Label("Gesamtumsatz (€)"), width=3, style={"textAlign": "right", "paddingTop": "10px"}),
                    dbc.Col(dcc.RangeSlider(
                        id='revenue_range_slider',
                        min=min_revenue,
                        max=max_revenue,
                        step=1000,
                        value=[min_revenue, max_revenue],
                        tooltip={"always_visible": False, "placement": "top"},
                        marks={
                            min_revenue: str(min_revenue),
                            max_revenue: str(max_revenue)
                        }
                    ), width=9),
                ]),
            ]),
            id="filter-collapse",
            is_open=True
        )
    ])

# Callback für das Umschalten des Collapse-Elements
@callback(
    Output("filter-collapse", "is_open"),
    [Input("toggle-filters-button", "n_clicks")],
    [State("filter-collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

#callback für output der unternehmensliste nach filtern
@callback(
    Output('entity_dropdown', 'options'),
    Input('niederlassungen_range_slider', 'value'),
    Input('avg_transaction_range_slider', 'value'),
    Input('revenue_range_slider', 'value'),
    Input('category_dropdown', 'value')
)
def filter_merchants_or_mcc(niederlassungen_range, avg_trans_range, revenue_range, category_value):
    if category_value == 'Unternehmen':
        filtered_df = merchant_stats.copy()

        # Weitere Filter anwenden
        filtered_df = filtered_df[
            (filtered_df['niederlassungen'] >= niederlassungen_range[0]) &
            (filtered_df['niederlassungen'] <= niederlassungen_range[1]) &
            (filtered_df['avg_transaction'] >= avg_trans_range[0]) &
            (filtered_df['avg_transaction'] <= avg_trans_range[1]) &
            (filtered_df['revenue'] >= revenue_range[0]) &
            (filtered_df['revenue'] <= revenue_range[1])
        ]
        # Rückgabe der gefilterten Händler als Dropdown-Optionen (String-Werte!)
        return [{'label': str(mid), 'value': str(mid)} for mid in filtered_df['merchant_id'].unique()]
    else: # category_value == 'Branchen'
        # Hier Branchenfilteroption: alle Branchen
        return [
            {"label": cat, "value": str(mcc)}
            for mcc, cat in mcc_codes_data[["mcc_code", "description"]].drop_duplicates().values
        ]

@callback(
    Output('map-graph', 'figure'), # Output ist jetzt direkt 'figure'
    Input('main-date-range', 'start_date'), 
    Input('main-date-range', 'end_date'),  
    Input('entity_dropdown', 'value'),
    Input('category_dropdown', 'value')
)
def renderMap(start_date, end_date, entity_value, category_value):
    filtered_data = transaction_data.copy()
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])
    filtered_data = filtered_data[(filtered_data['date'] >= pd.to_datetime(start_date)) & 
                                  (filtered_data['date'] <= pd.to_datetime(end_date))]

    geo_col = country_config['geo_column']
    scope = country_config['scope']
    location_mode = country_config.get('location_mode', None)

    fig = go.Figure() # Eine leere Figur initialisieren für den Fehlerfall

    if entity_value is None: # Behandle den Fall, dass noch nichts ausgewählt ist
        return fig # Leere Figur zurückgeben

    if category_value == 'Branchen':
        # Filtern nach MCC Code (Branche)
        df_filtered = filtered_data[filtered_data['mcc'] == int(entity_value)]
        
        # Berechnung der Marktkapitalisierung (Umsatz) pro Bundesstaat für die Branche
        marketcap = df_filtered.groupby(geo_col)['amount'].sum().reset_index(name="marketcap")
        
        title_text = f"Umsatz pro Bundesstaat für Branche: {mcc_dict.get(str(entity_value), 'Unbekannt')} ({entity_value})"
        
    elif category_value == 'Unternehmen':
        # Filtern nach merchant_id (Unternehmen)
        df_filtered = filtered_data[filtered_data['merchant_id'] == int(entity_value)]

        # Berechnung des Umsatzes pro Bundesstaat für das Unternehmen
        marketcap = df_filtered.groupby(geo_col)['amount'].sum().reset_index(name="marketcap")

        title_text = f"Umsatz pro Bundesstaat für Unternehmen: {entity_value}"
    else:
        # Falls category_value unerwartet ist oder keine Auswahl vorliegt
        marketcap = pd.DataFrame(columns=[geo_col, 'marketcap']) # Leeres DataFrame
        title_text = "Bitte wählen Sie eine Kategorie und ein Element aus."

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
    else:
     
        fig = go.Figure()
        fig.update_layout(title_text="Keine Daten für die aktuelle Auswahl verfügbar.")

    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, title_text=title_text)

    return fig


@callback(
    Output('entity_dropdown', 'value'), # Setze den Wert des Dropdowns zurück
    Input('category_dropdown', 'value')
)
def reset_entity_dropdown_value(category_value):
    # Setzt den initialen Wert des entity_dropdown, wenn die Kategorie geändert wird
    if category_value == 'Branchen':
        # Standard-MCC-Code für Branchen (z.B. Supermärkte)
        return '5411'
    elif category_value == 'Unternehmen':
        # Ersten verfügbaren Händler als Standard auswählen
        if len(merchants) > 0:
            return str(merchants[0])
    return None # Oder ein anderer sinnvoller Standardwert


@callback(
    Output('right_section', 'children'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value')
)
def update_right_section(category, entity_value):
    # Sicherstellen, dass ein Wert ausgewählt ist, bevor wir fortfahren
    if entity_value is None:
        return html.Div("Bitte wählen Sie ein Element aus.")

    if category == 'Unternehmen':
        merchant_id = int(entity_value)
        df_merchant = transaction_data[transaction_data['merchant_id'] == merchant_id]

        if df_merchant.empty:
            return dbc.Alert("Keine Daten für dieses Unternehmen verfügbar.", color="warning")

        total_revenue = df_merchant['amount'].sum()
        
        # Berechnung der eindeutigen Standorte (Stadt und Bundesstaat)
        standorte = (
            df_merchant[['merchant_city', 'merchant_state']]
            .drop_duplicates()
            .sort_values(by=['merchant_state', 'merchant_city'])
        )

        # Finde den MCC-Code für dieses Unternehmen, um die Branche anzuzeigen
        mcc_for_merchant = df_merchant['mcc'].iloc[0] if not df_merchant.empty else None
        mcc_description = mcc_dict.get(str(mcc_for_merchant), "Unbekannt") if mcc_for_merchant else "Unbekannt"


        return dbc.Card([
            dbc.CardHeader(f"Unternehmens-ID: {merchant_id}"),
            dbc.CardBody([
                html.H5("Unternehmensprofil", className="card-title"),
                html.P(f"Branche (MCC): {mcc_description} ({mcc_for_merchant})", className="card-text"),
                html.P(f"Gesamtumsatz: {total_revenue:.2f} €", className="card-text"),
                html.P(f"Anzahl Transaktionen: {len(df_merchant)}", className="card-text"),
                html.H6("Niederlassungen:"),
                html.P(f"Anzahl eindeutiger Standorte: {len(standorte)}", className="card-text"),
                # standort_liste_html # Auskommentiert, wenn Sie nur die Anzahl möchten
            ])
        ], color="light", outline=True)

    elif category == 'Branchen':
        branche_mcc = int(entity_value) # entity_value ist jetzt ein mcc_code
        branche = transaction_data.query(f"mcc == {branche_mcc}")
        
        # Gruppiere nach merchant_id und summiere den Umsatz (amount)
        umsatz_pro_merchant = (
            branche.groupby("merchant_id")['amount']
            .sum()
            .reset_index()
            .rename(columns={"amount": "total_revenue"})
            .sort_values(by="total_revenue", ascending=False)
        )
        
        if umsatz_pro_merchant.empty:
            return dbc.Alert("Keine Unternehmen für diese Branche verfügbar.", color="info")

        top_5 = umsatz_pro_merchant.nlargest(5, 'total_revenue')
        flop_5 = umsatz_pro_merchant.nsmallest(5, 'total_revenue')

        top_content = [
            dbc.ListGroupItem(
                f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €"
            , className="ranklist_item")
            for i, row in top_5.iterrows()
        ]

        flop_content = [
            dbc.ListGroupItem(
                f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €"
            , className="ranklist_item")
            for i, row in flop_5.iterrows()
        ]

        return dbc.Col([
            dbc.Row([
                dbc.Label('Top 5 Umsatz', className="fs-2 text"),
                dbc.ListGroup(top_content, numbered=True, id="top_list", className="ranklist p-4")
            ]),
            dbc.Row([
                dbc.Label('Flop 5 Umsatz', className="fs-2 text"),
                dbc.ListGroup(flop_content, numbered=True, id="flop_list", className="ranklist p-4")
            ])
        ], className="ranklist_container p-4")
    
    return html.Div("Bitte wählen Sie eine Kategorie und ein Element aus, um Details anzuzeigen.")


if __name__ == '__main__':
    app.run(debug=True)