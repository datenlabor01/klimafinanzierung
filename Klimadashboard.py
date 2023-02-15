from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

#Read in data:
dat = pd.read_csv('data.csv')
#Set stylesheet:
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Set-up dynamic elements:
#Slider Type of Support:
slider = dcc.Slider(0, 3, step=None,
    marks={
        0: "Total",
        1: 'adaptation',
        2: 'mitigation',
        3: 'crosscutting'}, included=False,
    value= 0)

slider_txt = ["Total", "adaptation", "mitigation", "cross-cutting"]

#Dropdown for Year:
year_dropdown = dcc.Dropdown(options=dat["Jahr"].unique(),
                             value='All', style={"textAlign": "center"}, clearable=False, multi=True, placeholder='Alle Jahre')

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
         html.Br(), year_dropdown,
         ], width = 6),
         ], justify = "center"),
      #Slider for type of support:
      dbc.Row([
         dbc.Col([
         html.Br(),
         dcc.Dropdown(id = "ressort", style={"textAlign": "center"}, clearable=False, multi=True, placeholder='Alle Ressorts'),
         html.Br(), slider,
         ],  width = 6),
      ], justify = 'center'),
      dbc.Row([
         dbc.Col([
            dcc.Graph(id = "map"),
         ]),
         dbc.Col([
            dcc.Graph(id = "treemap"),
         ]),
      ]),
      dbc.Row([
         dbc.Col([
            dcc.Graph(id = "BarBiMulti"),
            ]),
         dbc.Col([
            dcc.Graph(id = "BarTop5"),
         ]),
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
         filter_action="native", sort_action="native", page_size= 25,
         style_cell={'textAlign': 'left', "whiteSpace": "normal", "height": "auto"},
         style_header={'backgroundColor': 'rgb(11, 148, 153)', 'color': 'black', 'fontWeight': 'bold'},
             style_data_conditional=[{
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(235, 240, 240)',
        }], export_format= "xlsx"),
         ]),
    ])

#Funktion um nur Länder anzuzeigen, die in gewählter Kategorie sind:
@app.callback(
    Output("ressort", "options"),
    [Input(year_dropdown, 'value'), Input(slider, 'value')],
)

def support_options(selected_year, slider):
   if (selected_year == "All") | (selected_year == []):
      dat_temp = dat
   else:
      dat_temp = dat[dat["Jahr"].isin(selected_year)]
   if slider == 0:
      dat_temp = dat_temp
   else:
      dat_temp = dat_temp[dat_temp["TypeOfSupport"] == slider_txt[slider]]
   return sorted(dat_temp['Ressort'].unique())
   
#First callback-function for graphs only dependent on year-dropdown and slider:
@app.callback(
    [Output('map', 'figure'), Output('treemap', 'figure'), Output("BarTop5", "figure"), Output("BarBiMulti", "figure")],
    [Input(year_dropdown, 'value'), Input(slider, 'value'), Input("ressort", "value")]
)

def update_graph_1(selected_year, slider, ressort_dropdown):
   #Filter data based on user input for year and slider:
   if (selected_year == "All") | (selected_year == []):
      dat_fil = dat
   else:
      dat_fil = dat[dat["Jahr"].isin(selected_year)]
   if slider == 0:
      dat_fil = dat_fil
   else:
      dat_fil = dat_fil[dat_fil["TypeOfSupport"] == slider_txt[slider]]
   if (ressort_dropdown == []) | (ressort_dropdown == None):
      dat_fil = dat_fil
   else:
      dat_fil = dat_fil[dat_fil["Ressort"].isin(ressort_dropdown)]
   
   if dat_fil.empty:
      dat_fil = dat
   
   #Prepare data for map and display it:
   dat_map = dat_fil.groupby(["Recipient"])[["Klimafinanzierung in USD"]].sum()
   dat_map = dat_map.reset_index()
   figMap = px.choropleth(dat_map, locations ="Recipient", locationmode="country names", 
   color_continuous_scale="Viridis", color="Klimafinanzierung in USD", range_color=(min(dat_map["Klimafinanzierung in USD"]), max(dat_map["Klimafinanzierung in USD"]*0.05)))
   figMap.update_layout(coloraxis_showscale=False)
   #Treemap:
   figTree = px.treemap(dat_fil, path=[px.Constant("Total"), 'Kontinent', "Region"], values='Klimafinanzierung in USD', color='Kontinent')
   #Graph for Top-5 bar-chart:
   dat_bartop = dat_fil.groupby(["Recipient", "Region", "Channel"])[["Klimafinanzierung in USD"]].sum()
   dat_bartop = dat_bartop.reset_index()
   #Set data according to dropdown options:
   #If Multilateral as only filter:
   if ressort_dropdown == ["Multilateral"]:
      dat_bartop = dat_bartop[dat_bartop["Channel"] == "multilateral"]   
   if ressort_dropdown != None:
      if "Multilateral" in ressort_dropdown:
         dat_bartop = dat_bartop.groupby(["Recipient"])[["Klimafinanzierung in USD"]].sum()
         dat_bartop = dat_bartop.reset_index()
      #Discard multilateral recipients if "multilateral" not chosen as reporter:
      else:
         dat_bartop = dat_bartop[dat_bartop["Region"] != "Andere/nicht aufteilbar"]
   else:
      dat_bartop = dat_bartop[dat_bartop["Region"] != "Andere/nicht aufteilbar"]

   figBarTop = px.bar(dat_bartop.nlargest(5, "Klimafinanzierung in USD"), x='Klimafinanzierung in USD', y='Recipient', orientation="h")
   figBarTop.update_layout(yaxis={'title': ""}, xaxis={'title': ""}, title = "Top-5 Empfänger")
   #Bi-/Multi Bar-chart:
   datBarMulti = dat_fil.groupby(["Jahr", "Channel"])[["Klimafinanzierung in USD"]].sum()
   datBarMulti = datBarMulti.reset_index()
   figMultiBar = px.bar(datBarMulti, x="Jahr", y="Klimafinanzierung in USD", color="Channel", barmode="group")

   return (figMap, figTree, figBarTop, figMultiBar)

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
