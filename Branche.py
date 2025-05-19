import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import json
import random

# MCC-Codes laden
with open("mcc_codes.json", "r") as f:
    mcc_codes = json.load(f)

app = dash.Dash(__name__)

# Beispielhafte Unternehmensdaten pro Branche simulieren
def generate_fake_data(mcc):
    unternehmen = [f"Unternehmen {i+1}" for i in range(5)]
    werte = [random.randint(5000, 25000) for _ in unternehmen]
    return unternehmen, werte

app.layout = html.Div([
    html.H2("Branchenübersicht", style={"textAlign": "center"}),
    html.Div([
        dcc.Dropdown(
            id="branche-dropdown",
            options=[{"label": name, "value": code} for code, name in mcc_codes.items()],
            value="5812",  # Default MCC-Code
            placeholder="Branche auswählen",
            style={"width": "400px"}
        )
    ], style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"}),

    html.Div(id="branche-anzeige")
], style={"fontFamily": "Arial, sans-serif", "padding": "20px"})


@app.callback(
    Output("branche-anzeige", "children"),
    Input("branche-dropdown", "value")
)
def update_branchenansicht(mcc_code):
    if not mcc_code:
        return ""

    branchenname = mcc_codes.get(mcc_code, "Unbekannte Branche")
    unternehmen, werte = generate_fake_data(mcc_code)
    gesamtumsatz = sum(werte)

    pie_chart = px.pie(
        names=unternehmen,
        values=werte,
        hole=0.4,
        title="Umsatzverteilung"
    )
    pie_chart.update_traces(textposition="inside", textinfo="percent+label")

    return html.Div([
        html.H3(branchenname, style={"textAlign": "center", "marginBottom": "30px"}),

        html.Div([
            html.Div([
                html.Div("Umsatz", style={"fontSize": "20px", "marginBottom": "5px"}),
                html.Div(f"{gesamtumsatz:,.0f} €", style={"fontSize": "40px", "fontWeight": "bold", "color": "#2E8B57"})
            ], style={"width": "40%", "padding": "20px"}),

            html.Div([
                dcc.Graph(figure=pie_chart, config={"displayModeBar": False})
            ], style={"width": "60%", "padding": "10px"})
        ], style={
            "display": "flex",
            "border": "1px solid #ccc",
            "borderRadius": "10px",
            "boxShadow": "2px 2px 10px rgba(0,0,0,0.1)",
            "padding": "10px",
            "backgroundColor": "#f9f9f9"
        })
    ])
    
if __name__ == "__main__":
    app.run(debug=True)


