# Imports
import json
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

counties["features"][0]

country_config = {
    'scope': 'usa',
    'geo_column': 'merchant_state',
    'location_mode': 'USA-states'
}

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

timed_transaction_data = transaction_data
#timed_branche_data = transaction_data
timed_unternehmen_data = transaction_data


#######################
def calculate_avg_income_for_branche(start_date, end_date, mcc_code):
    # Datum umwandeln
    transaction_data['date'] = pd.to_datetime(transaction_data['date'])
    users_data['id'] = users_data['id'].astype(str)

    # Nach Datum und Branche filtern
    filtered_tx = transaction_data[
        (transaction_data['date'] >= pd.to_datetime(start_date)) &
        (transaction_data['date'] <= pd.to_datetime(end_date)) &
        (transaction_data['mcc'] == int(mcc_code))
    ]

    # Kund*innen-IDs holen
    unique_clients = filtered_tx['client_id'].dropna().astype(str).unique()

    # Passende Nutzer*innen finden
    matching_users = users_data[users_data['id'].astype(str).isin(unique_clients)]

    # Durchschnitt berechnen
    avg_income = matching_users['per_capita_income'].mean()

    # Wenn kein Wert, dann "Keine Daten"
    if pd.isna(avg_income):
        return "Keine Daten"

    # Auf 2 Stellen kürzen
    t_income = int(avg_income * 100) / 100

    # Ergebnis mit $ zurückgeben
    return f"{t_income:.2f} $"


def income_category_bar_component(avg_income_str):
    # Wenn keine Daten vorhanden sind
    if avg_income_str == "Keine Daten":
        return html.P("Keine Daten verfügbar.")

    # Zahl aus dem String holen (z. B. "12345.67 $")
    income_value = float(avg_income_str.replace(" $", "").replace(",", ""))

    # Skala von 0 bis 300.000 €
    scale_min = 0
    scale_max = 300000

    # Position auf der Skala berechnen (in %)
    relative_pos = ((income_value - scale_min) / (scale_max - scale_min)) * 100
    relative_pos = max(0, min(relative_pos, 100))  # Begrenzen zwischen 0 und 100 %

    # Farben und Kategorien definieren
    color_segments = ["#d73027", "#fc8d59", "#fee08b", "#91bfdb", "#4575b4"]
    categories = [
        "Unterschicht: < 30.000 €",
        "Untere Mittelschicht: 30.000 – 50.000 €",
        "Mittlere Mittelschicht: 50.000 – 135.000 €",
        "Obere Mittelschicht: 135.000 – 250.000 €",
        "Oberschicht: > 250.000 €"
    ]

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
    

#############

def calculate_mean_monthly_spending_per_customer(start_date, end_date, mcc_code):
    # Daten kopieren und Datum umwandeln
    df = transaction_data.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Nach Datum und Branche filtern
    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    # Wenn keine Daten, gib Info zurück
    if df.empty:
        return "Keine Daten"

    # Neue Spalte: Jahr + Monat
    df['year_month'] = df['date'].dt.to_period('M')

    # Summe pro Kunde
    total_by_client = df.groupby('client_id')['amount'].sum()

    # Wie viele Monate aktiv pro Kunde
    months_by_client = df.groupby('client_id')['year_month'].nunique()

    # Durchschnitt pro Monat
    monthly_avg = total_by_client / months_by_client

    # Wenn leer, gib Info zurück
    if monthly_avg.empty:
        return "Keine Daten"

    # Durchschnitt aller Kunden
    mean_value = monthly_avg.mean()

    # Auf 2 Nachkommastellen abschneiden
    truncated = int(mean_value * 100) / 100

    return f"{truncated:.2f} $"







def get_dominant_gender_in_branche(start_date, end_date, mcc_code, show_full_distribution=False):
    # Daten kopieren
    df = transaction_data.copy()
    df['date'] = pd.to_datetime(df['date'])
    users_data['id'] = users_data['id'].astype(str)

    # Transaktionen nach Datum und Branche filtern
    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
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
    diverse = gender_counts.get('diverse', 0)
    total = male + female + diverse

    # Wenn keine Angaben, Hinweis zurückgeben
    if total == 0:
        return "Keine Geschlechtsangaben"

    # Prozent berechnen 
    def truncate(val):
        return int(val * 10000) / 100

    percents = {
        "Männlich": truncate(male / total),
        "Weiblich": truncate(female / total),
        "Divers": truncate(diverse / total)
    }

    # Nach Prozent sortieren
    sorted_percents = sorted(percents.items(), key=lambda x: x[1], reverse=True)
    top1, top2 = sorted_percents[0], sorted_percents[1]

    # Entscheiden, ob ein Geschlecht dominiert
    dominant_text = "Ausgeglichen" if abs(top1[1] - top2[1]) < 1.0 else f"{top1[0]} ({top1[1]:.2f}%)"

   
    if show_full_distribution:
        return {
            "Dominant": dominant_text,
            "Verteilung": percents
        }
    else:
        return dominant_text



def get_average_age_in_branche(start_date, end_date, mcc_code):
    # Daten vorbereiten
    df = transaction_data.copy()
    df['date'] = pd.to_datetime(df['date'])
    users_data['id'] = users_data['id'].astype(str)

    # Nach Datum und Branche filtern
    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['mcc'] == int(mcc_code)) &
        (df['client_id'].notna())
    ]

    if df.empty:
        return None

    # Passende Nutzer*innen holen
    unique_clients = df['client_id'].astype(str).unique()
    matched_users = users_data[users_data['id'].isin(unique_clients)].copy()

    if 'birth_year' not in matched_users.columns or 'birth_month' not in matched_users.columns:
        return None

    # Geburtsdatum berechnen
    matched_users['birthdate'] = pd.to_datetime(
        matched_users['birth_year'].astype(str) + "-" +
        matched_users['birth_month'].astype(str).str.zfill(2) + "-01",
        errors='coerce'
    )
    matched_users = matched_users[matched_users['birthdate'].notna()]

    if matched_users.empty:
        return None

    # Alter berechnen
    reference_date = pd.to_datetime(end_date)
    matched_users['age'] = matched_users['birthdate'].apply(lambda b: (reference_date - b).days // 365)

    if matched_users['age'].empty:
        return None

    # Durchschnitt zurückgeben
    mean_age = matched_users['age'].mean()
    return int(mean_age * 100) / 100


#####################




def get_average_credit_score_in_branche(start_date, end_date, mcc_code):
    # Daten kopieren
    df = transaction_data.copy()
    df['date'] = pd.to_datetime(df['date'])
    users_data['id'] = users_data['id'].astype(str)

    # Nach Datum und Branche filtern
    df = df[
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date)) &
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




def plot_card_type_distribution_by_brand(start_date, end_date, mcc_code, show_percentage=False):
    # Kopiere die Transaktions- und Kartendaten
    df_tx = transaction_data.copy()
    df_tx['date'] = pd.to_datetime(df_tx['date'])
    df_cards = cards_data.copy()

    # Filtere nach Datum, Branche (MCC) und gültigen IDs
    df_tx = df_tx[
        (df_tx['date'] >= pd.to_datetime(start_date)) &
        (df_tx['date'] <= pd.to_datetime(end_date)) &
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

    # Wenn Prozentdarstellung gewünscht ist
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
        title='Kartennutzung nach Typ & Marke' + (' (in %)' if show_percentage else ''),
        labels={'card_type': 'Kartentyp', 'card_brand': 'Kartenmarke', y_val: y_title}
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


################




app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([ 
    dbc.Row([
        dbc.Col([
            dbc.Col([
                dcc.DatePickerRange(
                    id='date-range-start',
                    min_date_allowed=transaction_data['date'].min(),
                    max_date_allowed=transaction_data['date'].max(),
                    start_date=transaction_data['date'].min(),
                    end_date=transaction_data['date'].max(),
                    className=""
                ),
            ], width=12, className="gap-5" ,id='zeitraum_container'),
            dbc.Col([
                dbc.Col([
                    dcc.Dropdown(['Unternehmen', 'Branchen'], 'Branchen', id='category_dropdown')
                ], width=3),
                dbc.Col([
                    dcc.Dropdown(['5411'],'5411', id='entity_dropdown'),
                ], width=8),
            ], width=12, className="d-flex py-2 gap-2 justify-content-start"),
        ], width=6, className="py-3 filterbar"),
        dbc.Col([
            dbc.Button('Detailansicht anzeigen', className='btn primary', id="toggle-button" , n_clicks=0)
        ])
    ], className="navbar"),
    dbc.Row([
        dbc.Col([
                
        ], width=6, className="d-flex justify-content-center align-items-start", id="map-container"),
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
            
            ], id="right_section"),
        ], width=6,),
    ], className="h-100"),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H2("", id="branche_title"),
                html.Img(src="./assets/x.png", className="icon1", id="toggle-button-close")
            ], width=12, className="px-5 py-4 d-flex justify-content-between"),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([
                # dbc.Button("KPIs", color="primary", className="col-6 navigation-button active", id="kpi-btn"),
                # dbc.Button("Branchenübersicht", color="primary", className="col-6 navigation-button", id="branchenuebersicht_btn"),
            ], width=12),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([

            ], width=12, className="d-flex p-3", id="detail-view")
        ], className="h-100")
    ], width=12, className="h-100 position-absolute left-0", id="popup")
], fluid=True, className="body position-relative")

#ZUGEWIESEN AN -------- TOMMY --------
# TODOS: wenn "Branche" ausgewählt wird: alle Unternehmen in einer Branche
# 1. Ist Umsatz auf Landkarte anzeigen
# 2. Vergleich Umsatz (damals/heute) anzeigen in Prozent als Tooltip.

#ZUGEWIESEN AN -------- TOMMY --------
# TODOS: wenn "Unternehmen" ausgewählt wird: alle Standorte (States) eines Unternehmens
# 1. Unternehmensniederlassungen (States) nach Ist Umsatz einfärben
# 2. Vergleich Umsatz (damals/heute) anzeigen in Prozent als Tooltip.
@callback(
    Output('map-container', 'children'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
    Input('entity_dropdown', 'value'),
    Input('category_dropdown', 'value'),
)
def renderMap(start_date, end_date, entity_value, category_value):

# BRANCHE: 
# 1. Ist Umsatz(gesamt) der Branche - in jedem Bundesstaat - auf der Landkarte anzeigen:
    filtered_data = transaction_data.copy()
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])
    filtered_data = filtered_data[(filtered_data['date'] >= pd.to_datetime(start_date)) & 
                                  (filtered_data['date'] <= pd.to_datetime(end_date))]

    geo_col = country_config['geo_column']
    scope = country_config['scope']
    location_mode = country_config.get('location_mode', None)

    fig = go.Figure() # Eine leere Figur initialisieren für den Fehlerfall

    if entity_value is None: # Behandle den Fall, dass noch nichts ausgewählt ist
        dcc.Graph(figure=fig) # Leere Figur zurückgeben

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
        marketcap = pd.DataFrame(columns=[geo_col, 'marketcap']) 
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

    return dcc.Graph(figure=fig)


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


def getDateSelectionFrames(start_date, end_date, mcc):
    transaction_data['date'] = pd.to_datetime(transaction_data['date'])
    timed_transaction_data = transaction_data[(transaction_data['date'] >= pd.to_datetime(start_date)) & (transaction_data['date'] <= pd.to_datetime(end_date))]
    timed_branche_data = timed_transaction_data[timed_transaction_data['mcc'] == int(mcc)]
    transaction_data['mcc'] == int(mcc)
    timed_unternehmen_data = transaction_data
    
        
@callback(
    Output('right_section', 'children'),
    Input('category_dropdown', 'value'),
    Input('entity_dropdown', 'value'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
)
def update_right_section(category, entity_value, start_date_first, end_date_first):
    
    if category == 'Unternehmen' and entity_value is not None:
        getDateSelectionFrames(start_date_first, end_date_first, entity_value)
        print(entity_value)
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

    df_branche = transaction_data.query(f"mcc == {entity_value}")

    df = df_branche

    # Transaktionen im Zeitraum zwischen Start und End -- ERSTER DATEPICKER
    df['date'] = pd.to_datetime(df['date'])
    filtered_transaction_data = df[(df['date'] >= pd.to_datetime(start_date_first)) & (df['date'] <= pd.to_datetime(end_date_first))]
    filtered_transaction_data['date'] = pd.to_datetime(filtered_transaction_data['date']).dt.date
    start_date_first = pd.to_datetime(start_date_first).date() 
    end_date_first = pd.to_datetime(end_date_first).date() 

    if filtered_transaction_data.empty: 
        return dbc.Col([
            dbc.Row([
                dbc.Alert('keine Daten in diesem Zeitraum verfügbar!', className="fs-5 text", color="danger"),
            ]),
        ], className="ranklist_container p-4")
    
    print(filtered_transaction_data['date'])
    print('start Date format: ######## ', start_date_first)
    print('end Date format: ######## ', end_date_first)

    umsatz_am_start = (
        filtered_transaction_data[filtered_transaction_data['date'] == start_date_first]
        .groupby('merchant_id')['amount']
        .sum()
        .reset_index(name="start_revenue")
    )

    # for i, row in umsatz_am_start.iterrows():
    #     print(f"Händler {row['merchant_id']}: start_revenue = {row['start_revenue']}")
    # for i, row in umsatz_am_start.iterrows():
    #     print(f"Händler {row['merchant_id']}: start_revenue = {row['start_revenue']}")
    
    umsatz_am_ende = (
        filtered_transaction_data[(filtered_transaction_data['date'] == end_date_first)]
        .groupby('merchant_id')['amount']
        .sum()
        .reset_index(name="end_revenue")
    )
    # print('endDate: Selected ==> ', end_date_first)
    # for i, row in umsatz_am_ende.iterrows():
    #     print(f"Händler {row['merchant_id']}: end_revenue = {row['end_revenue']}")

    umsatz_vergleich = pd.merge(
        umsatz_am_start,
        umsatz_am_ende,
        'left',
        'merchant_id'
    ).fillna(0)

    umsatz_vergleich['veränderung'] = np.where(
        umsatz_vergleich['start_revenue'] == 0,
        np.nan,
        ((umsatz_vergleich['end_revenue'] - umsatz_vergleich['start_revenue']) / umsatz_vergleich['start_revenue']) * 100
    )

    #Gruppiere nach merchant_id und summiere den Umsatz (amount)
    umsatz_pro_merchant = (
        filtered_transaction_data.groupby("merchant_id")['amount']
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_revenue"})
        .sort_values(by="total_revenue", ascending=False)
    )

    umsatz_pro_merchant = pd.merge(
        umsatz_pro_merchant,
        umsatz_vergleich,
        'left',
        'merchant_id'
    )

    top_5 = umsatz_pro_merchant.nlargest(5, 'total_revenue')
    flop_5 = umsatz_pro_merchant.nsmallest(5, 'total_revenue')

    top_content = [
        dbc.ListGroupItem(
            f" Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} € - Veränderung: {row['veränderung']:.2f} %"
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


# ---- CSS Gimmics hinzufügen und entfernen hier ----




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
    Output("detail-view", "children"),
    Input("category_dropdown", "value"),
    Input("entity_dropdown", "value"),
    Input("date-range-start", "start_date"),
    Input("date-range-start", "end_date"),
)
def render_detailview(category, entity, start_date_first, end_date_first):
    if category == 'Branchen':
        transaction_data['date'] = pd.to_datetime(transaction_data['date'])
        time_transaction_data = transaction_data[(transaction_data['date'] >= pd.to_datetime(start_date_first)) & (transaction_data['date'] <= pd.to_datetime(end_date_first))]
        branchen_transaktionen = time_transaction_data[time_transaction_data['mcc'] == int(entity)]
        branchen_transaktionen["year"] = pd.to_datetime(branchen_transaktionen["date"]).dt.year 
        umsatz_Jahr_Merchant = branchen_transaktionen.groupby(["year","merchant_id"])["amount"].sum().reset_index(name="Umsatz_im_Jahr")
        
        umsatz_pro_merchant = umsatz_Jahr_Merchant.groupby("merchant_id")["Umsatz_im_Jahr"].sum().reset_index(name="gesamtumsatz")

        top_5 = umsatz_pro_merchant.nlargest(5, 'gesamtumsatz')
        flop_5 = umsatz_pro_merchant.nsmallest(5, 'gesamtumsatz')

        umsatz_Jahr_Merchant_top = umsatz_Jahr_Merchant[umsatz_Jahr_Merchant['merchant_id'].isin(top_5['merchant_id'])]
        umsatz_Jahr_Merchant_flop = umsatz_Jahr_Merchant[umsatz_Jahr_Merchant['merchant_id'].isin(flop_5['merchant_id'])]

        kpis = [
            {'Marktkapitalisierung': 100000000},
            {'durchschn. Transaktionshöhe': 380.20},
            {'durchschn. Transaktionen pro Käufer': 100000000},
            {'Umsatzwachstum (%)': 87.32},
            {'Consumer Money Spent (%)': 100000000},
            {'Unique Customers': 2102},
        ]
        
        fig1 = px.line(umsatz_Jahr_Merchant_top, x='year', y='Umsatz_im_Jahr', color='merchant_id', markers=True, title="Jährlicher Gesamtumsatz aller Händler in der Branche")
        fig2 = px.line(umsatz_Jahr_Merchant_flop, x='year', y='Umsatz_im_Jahr', color='merchant_id', markers=True, title="Jährlicher Gesamtumsatz aller Händler in der Branche")

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
                                        dbc.Tab(dcc.Graph(figure=fig1, id="card-content",className="card-text"),label="Top 5", tab_id="tab-1"),
                                        dbc.Tab(dcc.Graph(figure=fig2, id="card-content",className="card-text"),label="Flop 5", tab_id="tab-2"),
                                    ],
                                    active_tab="tab-1",
                                )
                            ),
                        ]
                    ),
                ], width=12, className="detail-view-right-section-1"),
                
                ####################

                dbc.Col([
    html.H4("Persona", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Durchschnittsalter", className="card-title"),
                            html.P(
                                f"{get_average_age_in_branche(start_date_first, end_date_first, entity)} Jahre",
                                className="card-text"
                    )
                ])

            ], className="h-100")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Durchschnittliches Einkommen (€)", className="card-title"),
                    html.P(
                        avg := calculate_avg_income_for_branche(start_date_first, end_date_first, entity),
                        className="card-text fw-bold"
                    ),
                    income_category_bar_component(avg)
                ])

            ], className="h-100")
        ], width=4),
       dbc.Col([
    dbc.Card([
        dbc.CardBody([
            html.H6("Monatsausgaben vom Kunde in der Branche", className="card-title"),
            html.P(
                calculate_mean_monthly_spending_per_customer(start_date_first, end_date_first, entity),
                className="card-text"
            )
        ])
    ], className="h-100")
], width=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Kartennutzung nach Typ & Marke", className="card-title"),
            dcc.Graph(figure=plot_card_type_distribution_by_brand(start_date_first, end_date_first, entity))
                ])
            ], className="h-100")
        ], width=4),
        dbc.Col([
             dbc.Card([
                dbc.CardBody([
                    html.H4("Geschlechterverteilung", className="mb-3"),
                    html.P(
                        f"Dominierendes Geschlecht: {get_dominant_gender_in_branche(start_date_first, end_date_first, entity)}",
                        className="fs-5 fw-bold"
                    ),
    
                ])
            ], className="h-100")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Durchschnittlicher Credit Score", className="card-title"),
                    html.P(
                        f"{get_average_credit_score_in_branche(start_date_first, end_date_first, entity)}",
                        className="card-text")
                ])
            ], className="h-100")
        ], width=4),
    ], className="g-2")
], width=12, className="detail-view-right-section-2"),



#####################################


######################################



                ################################


            ], width=7, className="detail-view-right-section")
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
    Output("branche_title", "children"),
    Input("category_dropdown", "value"),
    Input("entity_dropdown", "value"),
)
def update_detailView(category, entity):
    if category == 'Branchen' and entity is not None:
        beschreibung = mcc_codes_data.loc[
            mcc_codes_data["mcc_code"] == entity, "description"
        ].values

        if beschreibung.size > 0:
            return f"{entity} – {beschreibung[0]}"
        else:
            return f"{entity} – Beschreibung nicht gefunden"
    return ""

if __name__ == '__main__':
    app.run(debug=True)