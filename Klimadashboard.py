from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

#Read in data:
dat = pd.read_csv('klifi_deu.csv', sep= ";")
#Set stylesheet:
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Set-up dynamic elements:
#Dropdown for Year:
year_dropdown = dcc.Dropdown(options=dat["Year"].unique(),
                             value='All', style={"textAlign": "center"}, clearable=False, multi=True, placeholder='Alle Jahre')

#Dropdown for ressort:
ressort_dropdown = dcc.Dropdown(options=sorted(dat['Ressort'].unique()),
                             value='All', style={"textAlign": "center"}, clearable=False, multi=True, placeholder='Alle Ressorts')

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
         html.Br(), ressort_dropdown, 
         html.Br(),
         dcc.Slider(id = "typesupport_slider", min = 0, max = 3, step=None, value = 0, included=False),
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
    [Output("typesupport_slider", "marks"), Output("typesupport_slider", "max")],
    [Input(year_dropdown, 'value'), Input(ressort_dropdown, 'value')],
)

def support_options(selected_year, ressort_dropdown):
   if (selected_year == "All") | (selected_year == []):
      dat_temp = dat
   else:
      dat_temp = dat[dat["Year"].isin(selected_year)]
   if (ressort_dropdown == "All") | (ressort_dropdown == []):
      dat_temp = dat_temp
   else:
      dat_temp = dat_temp[dat_temp["Ressort"].isin(ressort_dropdown)]
   #Get available values for type of supports in filtered dataframe:
   slider_txt = dat_temp["TypeOfSupport"].unique()
   slider_txt = slider_txt.tolist()
   #Add element for total:
   slider_txt.insert(0, "Total")
   #Set marks based on available values in filtered dataframe and max:
   marks_slider = {i: slider_txt[i] for i in range(0,  len(slider_txt))}
   max_slider = len(slider_txt)-1
   return marks_slider, max_slider
   
#First callback-function for graphs only dependent on year-dropdown and slider:
@app.callback(
    [Output('map', 'figure'), Output('treemap', 'figure'), Output("BarTop5", "figure"), Output("BarBiMulti", "figure")],
    [Input(year_dropdown, 'value'), Input(ressort_dropdown, "value"), Input("typesupport_slider", "value")]
)

def update_graph_1(selected_year, ressort_dropdown, typesupport_slider):
   #Filter data based on user input for year, ressort and type of support:
   if (selected_year == "All") | (selected_year == []):
      dat_fil = dat
   else:
      dat_fil = dat[dat["Year"].isin(selected_year)]
   if (ressort_dropdown == []) | (ressort_dropdown == None) | (ressort_dropdown == "All"):
      dat_fil = dat_fil
   else:
      dat_fil = dat_fil[dat_fil["Ressort"].isin(ressort_dropdown)]
   if (typesupport_slider == 0):
      dat_fil = dat_fil
   else:
      slider_txt = dat_fil["TypeOfSupport"].unique()
      dat_fil = dat_fil[dat_fil["TypeOfSupport"] == slider_txt[typesupport_slider-1]]

   #Prepare data for map and display it:
   dat_map = dat_fil.groupby(["Recipient"])[["Klimafinanzierung"]].sum()
   dat_map = dat_map.reset_index()
   figMap = px.choropleth(dat_map, locations ="Recipient", locationmode="country names", 
   color_continuous_scale="Viridis", color="Klimafinanzierung", range_color=(min(dat_map["Klimafinanzierung"]), max(dat_map["Klimafinanzierung"]*0.05)))
   figMap.update_layout(coloraxis_showscale=False)
   #Treemap:
   figTree = px.treemap(dat_fil, path=[px.Constant("Total"), 'Kontinent', "Region"], values='Klimafinanzierung', color='Kontinent')
   #Graph for Top-5 bar-chart:
   dat_bartop = dat_fil.groupby(["Recipient Deutsch", "Region", "Channel"])[["Klimafinanzierung"]].sum()
   dat_bartop = dat_bartop.reset_index()
   dat_bartop = dat_bartop[dat_bartop["Recipient Deutsch"].str.contains("Nicht aufteilbar") == False]
   #Set data according to dropdown options:
   string = ["Nicht aufteilbar", ", regional"]
   #If Multilateral as only filter:
   if ressort_dropdown == ["Multilateral"]:
      dat_bartop = dat_bartop[dat_bartop["Channel"] == "Multilateral"]   
   if ressort_dropdown != None:
      if "Multilateral" in ressort_dropdown:
         dat_bartop = dat_bartop.groupby(["Recipient Deutsch"])[["Klimafinanzierung"]].sum()
         dat_bartop = dat_bartop.reset_index()
      #Discard multilateral recipients if "multilateral" not chosen as reporter:
      else:
         dat_bartop = dat_bartop[~dat_bartop["Region"].isin(string)]
   else:
      dat_bartop = dat_bartop[~(dat_bartop["Region"].isin(string)) & ~(dat_bartop["Recipient Deutsch"].isin(string))]

   figBarTop = px.bar(dat_bartop.nlargest(5, "Klimafinanzierung"), x='Klimafinanzierung', y="Recipient Deutsch", orientation="h")
   figBarTop.update_layout(yaxis={'title': ""}, xaxis={'title': ""}, title = "Top-5 Empfänger")
   #Bi-/Multi Bar-chart:
   datBarMulti = dat_fil.groupby(["Year", "Channel"])[["Klimafinanzierung"]].sum()
   datBarMulti = datBarMulti.reset_index()
   figMultiBar = px.bar(datBarMulti, x="Year", y="Klimafinanzierung", color="Channel", barmode="group")

   return (figMap, figTree, figBarTop, figMultiBar)

#Second callback for country-dropdown:
@app.callback(
    [Output("pie", "figure"), Output("number_projects", "children"), Output("sum_projects", "children"), Output(my_table, "data")],
    [Input(country_dropdown, "value")]
)

def update_graph_2(selected_country):
   #Prepare graph for pie chart data based on user input:
   if "All" in selected_country:
      datPie = dat.groupby(["Recipient", "Year", "Sector"])[["Klimafinanzierung"]].sum()
      datPie = datPie.reset_index()
      datPie.loc[datPie["Klimafinanzierung"] < 40000000, ["Sector"]] = "Other"
      figPie = px.pie(datPie, values='Klimafinanzierung', names='Sector')
   else:
      datPie = dat.groupby(["Recipient", "Year", "Sector"])[["Klimafinanzierung"]].sum()
      datPie = datPie.reset_index()
      figPie = px.pie(datPie[datPie["Recipient"] == selected_country], values='Klimafinanzierung', names='Sector')

   figPie.update_layout(yaxis={'title': ""}, xaxis={'title': ""})
   #Display two text elements:
   if "All" in selected_country:
      num_projects = len(dat["Recipient"])
      string_projects = "{} für alle Empfänger".format(num_projects)
      sum_projects = round(dat["Klimafinanzierung"].sum()//1000000,2)
      string_projects_sum = "{} Mio. USD für alle Projekte".format(sum_projects)
   else:
      num_projects = len(dat[dat["Recipient"] == selected_country])
      string_projects = "{} in {}".format(num_projects, selected_country)
      sum_projects = round(dat["Klimafinanzierung"][dat["Recipient"] == selected_country].sum()/1000000,2)
      string_projects_sum = "{} Mio. USD in {}".format(sum_projects, selected_country)
   #Set data for data table:
   if "All" in selected_country:
      dat_filter = dat
   else:
      dat_filter = dat[dat["Recipient"] == selected_country]

   return (figPie, string_projects, string_projects_sum, dat_filter.to_dict("records"))

if __name__ == '__main__':
    app.run_server(debug=True)
