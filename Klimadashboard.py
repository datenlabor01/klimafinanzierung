from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

#Read in data:
dat = pd.read_csv('data.csv')
#Set stylesheet:
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Set-up static graphs:
#Bar for sectors:
datBar = dat.groupby(["Ressort", "Jahr", "TypeOfSupport", "FinancialInstrument"])[["Klimafinanzierung in USD"]].sum()
datBar = datBar.reset_index()
#Bar for Bi-/Multi:
datBarMulti = dat.groupby(["Jahr", "Channel"])[["Klimafinanzierung in USD"]].sum()
datBarMulti = datBarMulti.reset_index()
figMultiBar = px.bar(datBarMulti, x="Jahr", y="Klimafinanzierung in USD", color="Channel", barmode="group")
#Bar for Ressort:
datBarRessort = dat.groupby(["Jahr", "Ressort"])[["Klimafinanzierung in USD"]].sum()
datBarRessort = datBarRessort.reset_index()
figRessortBar = px.bar(datBarRessort, x="Jahr", y="Klimafinanzierung in USD", color="Ressort")

#Set-up dynamic elements:
#Slider Type of Support:
slider = dcc.Slider(0, 3, step=None,
    marks={
        0: "Total",
        1: 'adaptation',
        2: 'mitigation',
        3: 'cross-cutting'},
    value= 0)

slider_txt = ["Total", "adaptation", "mitigation", "cross-cutting"]

#Dropdown for Year:
year_dropdown_map = dcc.Dropdown(options=["All", 2021, 2022],
                             value='All', style={"textAlign": "center"}, clearable=False, placeholder='Alle Jahre')

#Dropdown for Country:
country_dropdown = dcc.Dropdown(options=dat['Recipient'].unique(),
                                value="All", style = {"textAlign": "center"}, clearable=False,
                                searchable= True, placeholder='Alle Empfänger')
#App Layout: 
app.layout = dbc.Container([
      #Header:
      dbc.Row([
         html.H1(children='Dashboard Klimafinanzierung', style={'textAlign': 'center'})
      ]),
      #Dropdown for year:
      dbc.Row([
         dbc.Col([
         html.Br(), year_dropdown_map, html.Br(),
         ], width = 6),
         ], justify = "center"),
      #Slider for type of support:
      dbc.Row([
         dbc.Col([
         slider, html.Br(),
         ],  width = 6),
      ], justify = 'center'),
      #Worldmap and Top-5 bar-chart in same row: 
      dbc.Row([
         dbc.Col([
            dcc.Graph(id = "map"),
            ]),
         dbc.Col([
            dcc.Graph(id = "BarTop5"),
         ]),
      ]), 
      #Bar-chart for finance type in single row:
      dbc.Row([
         html.P('Nach Finanztyp:'), dcc.Graph(id = "bar"),
      ]),
      #two static graphs in same row:
      dbc.Row([
         dbc.Col([
            html.P('Nach Bi-/Multilateral:'),
            dcc.Graph(figure = figMultiBar, id = "barMulti"),
         ]),
         dbc.Col([
            html.P('Nach Ressort:'),
            dcc.Graph(figure = figRessortBar, id = "barRessort"),
         ])
      ]),
      #Dropdown for country:
      dbc.Row([
         dbc.Col([
         html.H4("Empfänger auswählen:", style={'textAlign': 'center'}), 
         country_dropdown, html.Br(),
         ], width = 6),
      ], justify = "center"),
      #Two cards to display text in same row:
      dbc.Row([
         dbc.Col([
            dbc.Card(
             dbc.CardBody([
               html.H4("Projektanzahl:", className="card-title"),
               html.H5(id="number_projects", style={"fontWeight": "bold"}),
             ]),
            ),    
      ]),
         dbc.Col([
            dbc.Card(
               dbc.CardBody([
               html.H4("Summe aller Projekte:", className="card-title"),
               html.H5(id="sum_projects", style={"fontWeight": "bold"}),
             ]),
            ),
      ]),
      ]),
      #Pie-chart:
      dbc.Row([
         dcc.Graph(id='pie', style={'textAlign': 'center'}),
      ]),
      #Data Table:
      dbc.Row([
         my_table := dash_table.DataTable(
         dat.to_dict('records'), [{"name": i, "id": i} for i in dat.columns],
         filter_action="native", sort_action="native", page_size= 25, style_cell={'textAlign': 'left'},
         style_header={'backgroundColor': 'rgb(210, 210, 210)', 'color': 'black', 'fontWeight': 'bold'})
         ]),
    ])

#First callback-function for graphs only dependent on year-dropdown and slider:
@app.callback(
    [Output('map', 'figure'), Output("BarTop5", "figure"), Output('bar', 'figure')],
    [Input(year_dropdown_map, 'value'), Input(slider, "value")]
)

def update_graph_1(selected_year_map, slider):
   #Filter data based on cases for user input: 
   if (selected_year_map == "All") & (slider == 0):
      dat_map = dat
      dat_bar = datBar.groupby(["Ressort", "FinancialInstrument"])[["Klimafinanzierung in USD"]].sum()
      dat_bar = dat_bar.reset_index()
   if (selected_year_map == "All") & (slider != 0):
      dat_map = dat[dat["TypeOfSupport"] == slider_txt[slider]]
      dat_bar = datBar.groupby(["Ressort", "TypeOfSupport", "FinancialInstrument"])[["Klimafinanzierung in USD"]].sum()
      dat_bar = dat_bar.reset_index()
      dat_bar = dat_bar[dat_bar["TypeOfSupport"] == slider_txt[slider]]
   if (selected_year_map != "All") & (slider == 0):
      dat_map = dat[dat["Jahr"] == selected_year_map]
      dat_bar = datBar[datBar["Jahr"] == selected_year_map]
   if (selected_year_map != "All") & (slider != 0):
      dat_map = dat[(dat["Jahr"] == selected_year_map) & (dat["TypeOfSupport"] == slider_txt[slider])]
      dat_bar = datBar[(datBar["Jahr"] == selected_year_map) & (datBar["TypeOfSupport"] == slider_txt[slider])]
   #Prepare data for map and display it:
   dat_map = dat_map.groupby(["Recipient"])[["Klimafinanzierung in USD"]].sum()
   dat_map = dat_map.reset_index()

   figMap = px.choropleth(dat_map, locations ="Recipient", locationmode="country names", 
   color_continuous_scale="Viridis", color="Klimafinanzierung in USD", range_color=(min(dat["Klimafinanzierung in USD"]), max(dat["Klimafinanzierung in USD"]*0.05)))
   figMap.update_layout(coloraxis_showscale=False, title = "Nach Empfängerländern")
   #Graph for Top-5 bar-chart 
   figBarTop = px.bar(dat_map.nlargest(5, "Klimafinanzierung in USD"), x='Klimafinanzierung in USD', y='Recipient', orientation="h")
   figBarTop.update_layout(yaxis={'title': ""}, xaxis={'title': ""}, title = "Top-5 Empfänger")
   #Graph for bar chart:
   figBar = px.bar(dat_bar, x='FinancialInstrument', y='Klimafinanzierung in USD', color="Ressort", hover_name = "Ressort")
   figBar.update_layout(yaxis={'title': ""}, xaxis={'title': ""})

   return (figMap, figBarTop, figBar)

#Second callback for country-dropdown:
@app.callback(
    [Output("pie", "figure"), Output("number_projects", "children"), Output("sum_projects", "children"), Output(my_table, "data")],
    [Input(country_dropdown, "value")]
)

def update_graph_2(selected_country):
   #Prepare graph for pie chart data based on user input:
   if "All" in selected_country:
      datPie = dat.groupby(["Recipient", "Jahr", "Sector"])[["Klimafinanzierung in USD"]].sum()
      datPie = datPie.reset_index()
      datPie.loc[datPie["Klimafinanzierung in USD"] < 40000000, ["Sector"]] = "Other"
      figPie = px.pie(datPie, values='Klimafinanzierung in USD', names='Sector')
   else:
      datPie = dat.groupby(["Recipient", "Jahr", "Sector"])[["Klimafinanzierung in USD"]].sum()
      datPie = datPie.reset_index()
      figPie = px.pie(datPie[datPie["Recipient"] == selected_country], values='Klimafinanzierung in USD', names='Sector')

   figPie.update_layout(yaxis={'title': ""}, xaxis={'title': ""})
   #Display two text elements:
   if "All" in selected_country:
      num_projects = len(dat["Recipient"])
      string_projects = "{} für alle Empfänger".format(num_projects)
      sum_projects = round(dat["Klimafinanzierung in USD"].sum()//1000000,2)
      string_projects_sum = "{} Mio. USD für alle Projekte".format(sum_projects)
   else:
      num_projects = len(dat[dat["Recipient"] == selected_country])
      string_projects = "{} in {}".format(num_projects, selected_country)
      sum_projects = round(dat["Klimafinanzierung in USD"][dat["Recipient"] == selected_country].sum()/1000000,2)
      string_projects_sum = "{} Mio. USD in {}".format(sum_projects, selected_country)
   #Set data for data table:
   if "All" in selected_country:
      dat_filter = dat
   else:
      dat_filter = dat[dat["Recipient"] == selected_country]

   return (figPie, string_projects, string_projects_sum, dat_filter.to_dict("records"))

if __name__ == '__main__':
    app.run_server(debug=True)