# Imports
from dash import Dash, html, dash_table, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re

# --- Read in data ---
data_folder = "../assets/data/"
nutriton_data = pd.read_csv(data_folder + "nutrition.csv", sep=",",  encoding="utf8")

# --- Remove all units from the data ---

def get_unit(value):
    match = re.search(r'([\d\.]+)\s*([a-zA-Z%]+)$', str(value))
    return match.group(2) if match else ''

# remove the unit and return the value (as float)
def remove_unit(value):
    ret_val = re.sub(r'\s*[a-zA-Z%]+$', '', str(value))
    # make sure the result is not empty (return 0.0 if it is empty)
    return 0.0 if ret_val == '' else float(ret_val)

# dictionary for storing all found units
found_units = {}

# iterate over all columns
for column in nutriton_data.columns:
    # prepare a set for all units that are found in this column
    units = set()
    # search for units
    for value in nutriton_data[column][1:]:  # skip first row
        unit = get_unit(value)
        if unit:
            units.add(unit)

    # if all rows have the same unit (i.e., only one unit was found), store the unit and remove it
    if len(units) == 1:
        found_units[column] = units.pop()
        nutriton_data[column] = nutriton_data[column].apply(remove_unit)
    elif len(units) > 1:
        print("More than one unit found in column " + column + ":")
        print(units)
    else:
        print("No unit found in column " + column + ".")

#array for the column titles, we want to fill in Dropdown for x-/y-axe. (Aufgabe 1)
column_titles_with_num = []

#fill the array for the column titles with the keys (columns) in the Hashset 'found_units.keys()'. (Aufgabe 1)
for key in found_units.keys():
    column_titles_with_num.append(key)
    
# Calculate the top 10 Products in Vitamin C Property. (Aufgabe 3)
#nutriton_data['vitamin_c'] = pd.to_numeric(nutriton_data['vitamin_c'], errors='coerce')
top_10_vitamin_c = nutriton_data.nlargest(10, 'vitamin_c')

# --- Initialize the app ---
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
# see: https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/

#first tab, where the histogram is displayed. (Aufgabe 2)
tab1_content = dbc.Card(
    dbc.CardBody([
        dbc.Col([
            dbc.Label('Choose value: '),
            dbc.RadioItems(options=[{"label": x.capitalize(), "value": x} for x in ['calories', 'fat', 'sodium']],
                    value='calories',
                    inline=True,
                    id='histo-controls'),
            dbc.FormText("Choose the nutritional value that is to be displayed in the histogram below."),
            dcc.Graph(figure={}, id='histogram')
        ], width=12), # 50% --> the layout grid always has 1..12 columns
    ]),
    className="mt-3",
)

#second tab, where the two alerts are displayed. (Aufgabe 2)
tab2_content = dbc.Card(
    dbc.CardBody([
        dbc.Alert(id='tbl_out_1'),
        dbc.Alert(id='tbl_out_2'),
    ]),
    className="mt-3",
)

#third tab, where the scatterplot is displayed. (to make the layout look clean.)
tab3_content = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dbc.FormText("Choose an x-value"),
            ], width=6),
            dbc.Col([
                dbc.FormText("Choose an y-value"),
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    "Please enter different x and y values!",
                ],
                color="warning",
                className="d-flex align-items-center",
                id='dropdown_alert',
                is_open=False
                ),
            ])
        ]),
        dbc.Row([
            #chose two dropdowns for selecting the x- and y-axe for the scatterplot. (Aufgabe 1)
            dbc.Col([
                dcc.Dropdown(column_titles_with_num, 'sodium', id='x-dropdown'),
            ], width=6),
            dbc.Col([
                dcc.Dropdown(column_titles_with_num, 'fat', id='y-dropdown'),
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure={}, style={'width': '100%', 'height': '100%'}, id='scatterplot')
            ], width=12)
        ]),
    ]),
    className="mt-3",
)

#fourth tab, where the bar chart with top 10 vitamin C products is displayed. (Aufgabe 3)
tab4_content = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=px.bar(top_10_vitamin_c, x='name', y='vitamin_c',hover_data=['name', 'vitamin_c'], color='vitamin_c', color_continuous_scale='rainbow' ,labels={'vitamin_c':'Vitamin C in mg'}, height=1000))
            ], width=12)
        ]),
    ]),
    className="mt-3",
)

# App layout
app.layout = dbc.Container([
    dbc.Row([
        html.Div('Nutritional values for common foods and products', className="text-primary text-center fs-3")
    ]),
    dbc.Row([
        dash_table.DataTable(data=nutriton_data.to_dict('records'), page_size=10, style_table={'overflowX': 'auto'}, id='tbl'),
    ]),
    dbc.Row([
        dbc.Tabs([
            dbc.Tab(tab1_content, label="Histogram"),
            dbc.Tab(tab2_content, label="Alerts"),
            dbc.Tab(tab3_content, label="Scatter Plot"),
            dbc.Tab(tab4_content, label="Bar Chart")
        ])
    ])
], fluid=True)

# Callback for table cell 
@callback(Output('tbl_out_1', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    # first we print the value of the selected cell, second we print the product name. 
    return 'Value: ' + str(nutriton_data.iloc[active_cell['row'], active_cell['column']]) + ', Name: ' + str(nutriton_data.iloc[active_cell['row'], 1]) if active_cell else "Click the table"

@callback(Output('tbl_out_2', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"

#Callback for scatterplot where the user can pick values of both axes. (Aufgabe 1) --> incl. Errorhandling, due x and y values should'nt be equal!
@callback(
    Output('scatterplot', 'figure'),
    Output('dropdown_alert', 'is_open'),
    Output('x-dropdown', 'value'),
    Output('y-dropdown', 'value'),
    Input('x-dropdown', 'value'),
    Input('y-dropdown', 'value')
)
def update_scatterplot(x_value, y_value):
    if x_value != y_value:
        fig=px.scatter(nutriton_data, x=x_value, y=y_value, color="niacin", hover_data=['name'], trendline="ols")
        fig.update_layout()
        return fig, False, x_value, y_value
    fig=px.scatter(nutriton_data, x='sodium', y='vitamin_c', color="niacin", hover_data=['name'], trendline="ols")
    return fig, True, 'sodium', 'vitamin_c'

# Callback for histrogram
@callback(
    Output(component_id='histogram', component_property='figure'),
    Input(component_id='histo-controls', component_property='value')
)
def update_graph(col_chosen):
    fig=px.histogram(nutriton_data, x=col_chosen,
        title=col_chosen.capitalize() + (" (" + found_units[col_chosen] + ")" if col_chosen in found_units else ""),
        opacity=0.75,nbins=30)
    fig.update_layout(bargap=0.2)
    return fig

if __name__ == '__main__':
    app.run(debug=True)
