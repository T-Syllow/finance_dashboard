seitebsp.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px

# Beispiel-Daten
branche = "Fast Food Restaurants"
umsatz = 100_000

# Beispiel-Unternehmensdaten für das Kreisdiagramm
unternehmen = {
    "McDonald's": 40000,
    "Burger King": 25000,
    "Subway": 15000,
    "Domino's": 12000,
    "KFC": 8000
}

# Erzeuge Kreisdiagramm
fig_pie = px.pie(
    names=list(unternehmen.keys()),
    values=list(unternehmen.values()),
    hole=0.4,
    title="Umsatzverteilung"
)

# App starten
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2(f"Branche: {branche}", className="my-4"),

    dbc.Card([
        dbc.Row([
            # Umsatz groß links
            dbc.Col([
                html.Div([
                    html.H3("Umsatz", className="text-muted"),
                    html.H1(f"{umsatz:,.0f} €", style={"fontSize": "48px", "fontWeight": "bold"})
                ], className="text-center")
            ], width=4),

            # Kreisdiagramm rechts
            dbc.Col([
                dcc.Graph(figure=fig_pie, config={"displayModeBar": False})
            ], width=8),
        ], className="p-4"),
    ], style={"boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "borderRadius": "16px"})
], fluid=True)
