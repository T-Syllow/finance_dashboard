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

# --- Read in data ---
data_folder = "./newData/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data_10k.csv", sep=",",  encoding="utf8")
cards_data = pd.read_csv(data_folder + "cleaned_cards_data.csv", sep=",",  encoding="utf8")
users_data = pd.read_csv(data_folder + "cleaned_users_data.csv", sep=",",  encoding="utf8")
with open(data_folder + 'mcc_codes.json', 'r', encoding='utf-8') as f:
    mcc_dict = json.load(f)
mcc_codes_data = pd.DataFrame(list(mcc_dict.items()), columns=['mcc_code', 'description'])

# alle Händler
merchants = transaction_data['merchant_id'].unique()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([ 
    dcc.Store(id='timed_transaction_data'),
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
                dbc.Button("KPIs", color="primary", className="col-6 navigation-button active", id="kpi-btn"),
                dbc.Button("Branchenübersicht", color="primary", className="col-6 navigation-button", id="branchenuebersicht_btn"),
            ], width=12),
        ], className="popup-header"),
        dbc.Row([
            dbc.Col([

            ], width=12, className="d-flex p-3", id="detail-view")
        ], className="h-100")
    ], width=12, className="h-100 position-absolute left-0", id="popup")
], fluid=True, className="body position-relative")

@app.callback(
    Output('timed_transaction_data', 'data'),
    Input('date-range-start', 'start_date'),
    Input('date-range-start', 'end_date'),
)
def update_timed_transaction_data(start_date, end_date):
    df = transaction_data.copy()
    df['date'] = pd.to_datetime(df['date'])
    filtered = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
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
        title_text = f"Umsatz pro Bundesstaat für Branche: {mcc_dict.get(str(entity_value), 'Unbekannt')} ({entity_value})"
    elif category_value == 'Unternehmen' and entity_value is not None:
        # Filtern nach merchant_id (Unternehmen)
        df_filtered = filtered_data[filtered_data['merchant_id'] == int(entity_value)]
        # Berechnung des Umsatzes pro Bundesstaat für das Unternehmen
        marketcap = df_filtered.groupby(geo_col)['amount'].sum().reset_index(name="marketcap")
        title_text = f"Umsatz pro Bundesstaat für Unternehmen: {entity_value}"

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
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, title_text=title_text)
        return dcc.Graph(figure=fig)
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

def create_merchant_card(merchant_id, total_revenue, transaction_count, standorte):
    return dbc.Card([
        dbc.CardHeader(f"Händler-ID: {merchant_id}"),
        dbc.CardBody([
            html.H5("Unternehmensprofil", className="card-title"),
            html.P(f"Gesamtumsatz: {total_revenue:.2f} €", className="card-text"),
            html.P(f"Anzahl Transaktionen: {transaction_count}", className="card-text"),
            html.H6("Niederlassungen:"),
            len(standorte),
        ])
    ], color="light", outline=True)

def create_ranklist(title, content, list_id):
    return dbc.Row([
        dbc.Label(title, className="fs-2 text"),
        dbc.ListGroup(content, numbered=True, id=list_id, className="ranklist p-4")
    ])
   
def handle_unternehmen(df, entity_value):
    merchant_id = int(entity_value)
    df_merchant = df[df['merchant_id'] == merchant_id]

    if df_merchant.empty:
        return dbc.Alert("Keine Daten für dieses Unternehmen verfügbar.", color="warning")

    total_revenue = df_merchant['amount'].sum()
    standorte = (
        df_merchant[['merchant_city', 'merchant_state']]
        .drop_duplicates()
        .sort_values(by=['merchant_state', 'merchant_city'])
    )

    return create_merchant_card(merchant_id, total_revenue, len(df_merchant), standorte)

def handle_branchen(df, entity_value):
    df_branche = df[df['mcc'] == int(entity_value)]

    if df_branche.empty:
        return dbc.Col([
            dbc.Row([
                dbc.Alert('keine Daten in diesem Zeitraum verfügbar!', className="fs-5 text", color="danger"),
            ]),
        ], className="ranklist_container p-4")

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
            f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €",
            className="ranklist_item"
        )
        for _, row in top_5.iterrows()
    ]

    flop_content = [
        dbc.ListGroupItem(
            f"Händler {row['merchant_id']:.0f} – Umsatz: {row['total_revenue']:.2f} €",
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
def update_right_section(category, entity_value, timed_transaction_data):
    if timed_transaction_data is None or entity_value is None:
        return None

    df = pd.DataFrame(timed_transaction_data)

    if category == 'Unternehmen':
        return handle_unternehmen(df, entity_value)

    if category == 'Branchen':
        return handle_branchen(df, entity_value)

    return None

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
    
def process_branchen_data(df, entity, start_date, end_date):
    time_transaction_data = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    branchen_transaktionen = time_transaction_data[time_transaction_data['mcc'] == int(entity)]
    branchen_transaktionen["year"] = pd.to_datetime(branchen_transaktionen["date"]).dt.year
    umsatz_Jahr_Merchant = branchen_transaktionen.groupby(["year", "merchant_id"])["amount"].sum().reset_index(name="Umsatz_im_Jahr")
    umsatz_pro_merchant = umsatz_Jahr_Merchant.groupby("merchant_id")["Umsatz_im_Jahr"].sum().reset_index(name="gesamtumsatz")
    return umsatz_Jahr_Merchant, umsatz_pro_merchant, branchen_transaktionen

def create_kpi_cards(kpis):
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5(value),
                    html.P(key),
                ], className="kpi-card-body"),
            ], color="success", outline=True)
        ], width=5, className="kpi-card p-2")
        for kpi in kpis
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
    Input('kpi-btn', 'n_clicks'),
    Input('branchenuebersicht_btn', 'n_clicks'),
    Input('timed_transaction_data', 'data')
)
def render_detailview(category, entity, start_date_first, end_date_first, kpi_btn, uebersicht_btn, timed_transaction_data):
    if timed_transaction_data is None:
        return dbc.Alert("Keine Transaktionsdaten verfügbar.", color="warning")

    df = pd.DataFrame(timed_transaction_data)
    df['date'] = pd.to_datetime(df['date'])

    if category == 'Branchen' and entity is not None:
        umsatz_Jahr_Merchant, umsatz_pro_merchant, branchen_transaktionen = process_branchen_data(df, entity, start_date_first, end_date_first)
        top_5 = umsatz_pro_merchant.nlargest(5, 'gesamtumsatz')
        flop_5 = umsatz_pro_merchant.nsmallest(5, 'gesamtumsatz')
        fig1, fig2 = create_branchen_charts(umsatz_Jahr_Merchant, top_5, flop_5)

        # ============================= Code Start ============================================

         #Marktkapitalisierung berechnet

        Marktkapitalisierung = umsatz_pro_merchant["gesamtumsatz"].sum()  
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

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
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} € ".replace(",", "X").replace(".", ",").replace("X", ".")

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

        # =====================================================================================

        #Unique Customers
        EinzigartigeKäufer = branchen_transaktionen["client_id"].nunique()

       

    #Marktkapitalisierung berechnet

        Marktkapitalisierung = umsatz_pro_merchant["gesamtumsatz"].sum()  
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
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
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} € ".replace(",", "X").replace(".", ",").replace("X", ".")

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

       


        # ============================= Code Ende =============================================
        kpis = [
                {'Marktkapitalisierung': Marktkapitalisierung},   # Berechnet die Marktkapitalisierung 
                {'durchschn. Transaktionshöhe': DurchschnittTransaktionshöhe},    # Berechnet die durchschn. Transaktionshöhe einer Transaktion in dem ausgewählten Zeitraum in Euro 
                {'durchschn. Transaktionen pro Käufer': DurchschnittTransaktionenProKäufer}, # Berechnet die Menge an Transaktionen, die ein Käufer im Durchschnitt im ausgewählten Zeitraum tätigt.
                {'Umsatzwachstum (%)': 87.42},  # (optional) diese KPI müsst ihr nicht berechnen!! 
                {'Consumer Money Spent (%)': ConsumerMoneySpent},  # Berechnet zunächst die durchschn. Menge an Geld, die ein User im Schnitt im ausgewählten Zeitraum ausgibt. Dann berechnet wie viel er für die Branche im durchschnitt ausgibt. und setzt es anschließend ins Verhältnis! ==> %
                {'Käufer':  EinzigartigeKäufer}, # Wie viele einzigartige User haben im ausgewählten Zeitrsaum bei der Branche eingekauft?
            ]

        return [
            dbc.Col(create_kpi_cards(kpis), width=5, className="detail-view-left-section d-flex flex-wrap justify-content-start align-content-start p-3 overflow-y-scroll"),
            dbc.Col([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Tabs([
                                dbc.Tab(dcc.Graph(figure=fig1, id="card-content", className="card-text"), label="Top 5", tab_id="tab-1"),
                                dbc.Tab(dcc.Graph(figure=fig2, id="card-content", className="card-text"), label="Flop 5", tab_id="tab-2"),
                            ], active_tab="tab-1"),
                        ),
                    ]),
                ], width=12, className="detail-view-right-section-1"),
                dbc.Col([html.Div("Persona")], width=12, className="detail-view-right-section-2"),
            ], width=7, className="detail-view-right-section")
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
        
       
        
        
        #Berechnungen Kreisdiagramme (beispiel1)
        #branchen_transaktionen = transaction_data[transaction_data['mcc'] == unternehmen_transaktionen]  
        #Marktkapitalisierung = unternehmen_transaktionen["amount"].sum()
        #Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        #gesamtMarktkapitalisierung = branchen_transaktionen["amount"].sum()
        #gesamtMarktkapitalisierung = f"{gesamtMarktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        

        # Branchen-Marktkapitalisierung (beispiel2)
        
        #branchen_transaktionen = transaction_data[transaction_data["mcc"] == unternehmen_mcc]
        #Marktkapitalisierung = unternehmen_mcc["amount"].sum()
        #Marktkapitalisierung_Branche = branchen_transaktionen["amount"].sum()
        #gesamtMarktkapitalisierung = branchen_transaktionen["amount"].sum()
        #DurchschnittBranche = branchen_transaktionen.groupby("client_id")["amount"].sum().mean()
        
        
      
        unternehmen_transaktionen = df[df['merchant_id'] == entity]     # Transaktionen des Unternehmens filtern (von oben)
        unternehmen_mcc = unternehmen_transaktionen['mcc'].iloc[0]      # MCC des Unternehmens holen, iloc[0] nimmt 1 Zeile aus Transaktionen – weil alle Zeilen dieses Unternehmens selben MCC haben sollten.
        
       
        branchen_transaktionen = transaction_data[transaction_data['mcc'] == unternehmen_mcc]    # Alle Transaktionen dieser Branche holen
        
        
        MarktkapitalisierungUnternehmen = unternehmen_transaktionen["amount"].sum()
        GesamtMarktkapitalisierungBranche = branchen_transaktionen["amount"].sum()
        
        
        
        
        
        unternehmen_preisbereich = df['amount'] = df['amount'].replace('[\$,]', '', regex=True).astype(float) 
        unternehmen_transaktionen = df[df['merchant_id'] == entity] 
        unternehmen_mcc = unternehmen_transaktionen['mcc'].iloc[0]  
        
        #Bereiche definieren (<50, 50-200, >20)
        Bereiche = [-float('inf'), 50, 200, float('inf')] 
        labels = ['Klein (<=50)', 'Mittel (50-200)', 'Groß (>200)']


        #Transaktionshöhe anzahl pro Bereich 
        ErsterPreisbereich = unternehmen_transaktionen[unternehmen_transaktionen['amount']<50]['amount'].count()
        #ZweiterPreisbereich = unternehmen_transaktionen[unternehmen_transaktionen['amount']>=50 & unternehmen_transaktionen['amount']<=200].count()
        ZweiterPreisbereich = unternehmen_transaktionen[(unternehmen_transaktionen['amount'] >= 50) & (unternehmen_transaktionen['amount'] <= 200)]['amount'].count()
        DritterPreisbereich = unternehmen_transaktionen[unternehmen_transaktionen['amount']>200]['amount'].count()
    

      
        # Kreisdiagramme 
        fig_pie = px.pie(
        names=["Marktkapitalisierung", "Gesamtkapitalisierung je Branche"],
        values=[MarktkapitalisierungUnternehmen, GesamtMarktkapitalisierungBranche],
        title="Marktkapitalverteilung"
        )
        
        
        #2. Kreisdiagramm 
        fig_pie_2 = px.pie(
        names=["Preisbereich1", "Preisbereich2", "Preisbereich3"],
        values=[ErsterPreisbereich, ZweiterPreisbereich, DritterPreisbereich],
        title='Anteil der Transaktionshöhe nach Bereichen',
        labels = ['Klein (<=50)', 'Mittel (50-200)', 'Groß (>200)']
        )
        
        
        # Bar-Chart erstellen
        fig_bar_chart = px.bar(
            umsatz_pro_monat,
            x='month',
            y='amount',
            title='Umsatz je Monat',
            labels={'month': 'Monat', 'amount': 'Umsatz (€)'},
            text_auto=True
        )
        

        # Formatierung des Bar-Charts
        fig_bar_chart.update_layout(
            xaxis_title="Monat",
            yaxis_title="Umsatz (€)",
            template="plotly_white"
        )


        Marktkapitalisierung = unternehmen_transaktionen["amount"].sum()
        Marktkapitalisierung = f"{Marktkapitalisierung:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

        DurchschnittTransaktionshöhe = unternehmen_transaktionen['amount'].mean()
        DurchschnittTransaktionshöhe = f"{DurchschnittTransaktionshöhe:,.2f} € ".replace(",", "X").replace(".", ",").replace("X", ".")

        GesamtTransaktionen = unternehmen_transaktionen["merchant_id"].count()
        EinzigartigeKäufer = unternehmen_transaktionen["client_id"].nunique()
        DurchschnittTransaktionenProKäufer = GesamtTransaktionen / EinzigartigeKäufer
        DurchschnittTransaktionenProKäufer = f"{DurchschnittTransaktionenProKäufer:,.2f} ".replace(",", "X").replace(".", ",").replace("X", ".")

        GesamtAusgabenProClient = df.groupby("client_id")["amount"].sum()
        Durchschnitt_gesamt = GesamtAusgabenProClient.mean()
        UnternehmensAusgabenProClient = unternehmen_transaktionen.groupby("client_id")["amount"].sum()

        DurchschnittBranche = UnternehmensAusgabenProClient.mean()
        ConsumerMoneySpent = (DurchschnittBranche / Durchschnitt_gesamt) * 100
        ConsumerMoneySpent = f"{ConsumerMoneySpent:,.2f} % ".replace(",", "X").replace(".", ",").replace("X", ".")

        CustomerLifetimeValue = Durchschnitt_gesamt / EinzigartigeKäufer * 100
        CustomerLifetimeValue = f"{CustomerLifetimeValue:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


        kpis = [
            {'Marktkapitalisierung': Marktkapitalisierung},
            {'durchschn. Transaktionshöhe': DurchschnittTransaktionshöhe},
            {'durchschn. Transaktionen pro Käufer': DurchschnittTransaktionenProKäufer},
            {'Umsatzwachstum (%)': 87.42},
            {'Consumer Money Spent (%)': ConsumerMoneySpent},
            {'Käufer': EinzigartigeKäufer},
            {'Customer Lifetime Value': CustomerLifetimeValue},
        ]

        return [
            dbc.Col([
                dbc.Col(
                    create_kpi_cards(kpis),
                    width=12, className="detail-view-kpis d-flex flex-wrap justify-content-start align-content-start p-3 overflow-y-scroll"
                ),
                html.Div("Kreisdiagramm", className="fw-bold"),  # fetter Text
                dbc.Col([ 
                    dcc.Graph(figure=fig_pie),
                    dcc.Graph(figure=fig_pie_2),
                ], width=6)
            ])
        ]

        # dbc.Col([
        #         dbc.Col([
        #             html.Div("Plots"),
        #             dcc.Graph(figure=fig_bar_chart)
        #         ], width=12, className="detail-view-right-section"),
                
                
                
        #         dbc.Col([
        #             html.Div("Persona")
        #         ], width=12, className="detail-view-right-section-2"),
        #     ], width=7, className="detail-view-right-section")
        # ]
    
    


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