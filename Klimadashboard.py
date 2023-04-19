from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import requests
import geopandas as gpd
import numpy as np

#Read in data:
dat = pd.read_csv('https://github.com/datenlabor01/klimafinanzierung/blob/main/klifi_deu.csv?raw=true', sep= ";")

searchstring = ["BMZ", "DEG", "KfW", "Multilateral"]
#dat = dat[dat["Ressort"].str.contains('|'.join(searchstring))]
dat = dat[dat["Year"] == 2022]
dat['Year'] = dat['Year'].astype(str)
dat = dat[dat["Klimafinanzierung"] > 0]

cont = requests.get(
    "https://gist.githubusercontent.com/hrbrmstr/91ea5cc9474286c72838/raw/59421ff9b268ff0929b051ddafafbeb94a4c1910/continents.json")
gdf = gpd.GeoDataFrame.from_features(cont.json())
gdf["Klimafinanzierung"] = np.nan
gdf = gdf.set_index("CONTINENT")

#Set stylesheet:
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Set-up dynamic elements:
#Dropdown for Country:
country_dropdown = dcc.Dropdown(id = "country",
                                value="All", style = {"textAlign": "center"}, clearable=True, multi=True,
                                searchable= True, placeholder='Alle Empfänger')

typesupport = dcc.Slider(min = 0, max = 3, step=1,
                         marks= {0: "Total", 1: "Adaptation", 2: "Mitigation", 3: "Cross-cutting"},
                         value = 0, included=False)

map_select = dcc.RadioItems(options=['Länder', 'Kontinent'], value='Länder')

#Dropdown financial instrument:
fininstrument = dcc.Dropdown(id="fininstrument",
                                value="All", style = {"textAlign": "center"}, clearable=True, multi=True,
                                placeholder='Alle Instrumente')
#App Layout:
app.layout = dbc.Container([
      #Header:
      dbc.Row([
         html.H1(children='Dashboard Klimafinanzierung BMZ', style={'textAlign': 'center'})
      ]),
      #Slider for type of support:
      dbc.Row([
         dbc.Col([
         typesupport, html.Br(), fininstrument,
         html.Br(), map_select], width=6)], justify = "center"),
      dbc.Row([
            dcc.Graph(id = "map")]),
      #Dropdown for country:
      dbc.Row([
         dbc.Col([
         country_dropdown, html.Br(),
         ], width = 6),
      ], justify = "center"),

      #Pie-chart:
      dbc.Row([
         dcc.Graph(id='pie', style={'textAlign': 'center'}),
      ]),

      dbc.Row([
            dbc.Col([dcc.Graph(id = "BarBiMulti")]),
            dbc.Col([dcc.Graph(id = "BarHaushalt")]),
            ]),
    ])

@app.callback(
    Output("fininstrument", "options"),
    Input(typesupport, 'value'),
    )

def fininstrument_options(typesupport_slider):
    typesupport_list = ["Total", "adaptation", "mitigation", "cross-cutting"]
    if typesupport_slider == 0:
      dat_fil = dat
    else:
      dat_fil = dat[dat["TypeOfSupport"] == typesupport_list[typesupport_slider]]
    return sorted(dat_fil['FinancialInstrument'].unique())

@app.callback(
    Output("country", "options"),
    [Input(typesupport, 'value'), Input("fininstrument", "value")]
    )

def country_options(typesupport_slider, fin_instrument):
    typesupport_list = ["Total", "adaptation", "mitigation", "cross-cutting"]
    if typesupport_slider == 0:
      dat_fil = dat
    else:
      dat_fil = dat[dat["TypeOfSupport"] == typesupport_list[typesupport_slider]]

    if (fin_instrument == "All") | (fin_instrument == []):
      dat_fil = dat_fil
    else:
      dat_fil = dat_fil[dat_fil["FinancialInstrument"].isin(fin_instrument)]

    return sorted(dat_fil['Recipient'].unique())

@app.callback(
    [Output('map', 'figure'), Output("BarBiMulti", "figure"), Output("BarHaushalt", "figure"), Output("pie", "figure")],
    [Input(typesupport, "value"), Input("fininstrument", "value"), Input(map_select, "value"), Input("country", "value")],
)

def update_graph_1(typesupport_slider, fin_instrument, map_select, selected_country):

   #Filter data based on user input for type of support:
   typesupport_list = ["Total", "adaptation", "mitigation", "cross-cutting"]
   if typesupport_slider == 0:
      dat_fil = dat
   else:
      dat_fil = dat[dat["TypeOfSupport"] == typesupport_list[typesupport_slider]]

   if (fin_instrument == "All") | (fin_instrument == []):
      dat_fil = dat_fil
   else:
      dat_fil = dat_fil[dat_fil["FinancialInstrument"].isin(fin_instrument)]

   #Prepare data for map and display it:
   dat_map = dat_fil.groupby(["Recipient", "ISOCode"])[["Klimafinanzierung"]].sum().reset_index()

   if dat_map.empty:
      figMap = px.choropleth()
   else:
      if map_select == "Länder":
         figMap = px.choropleth(dat_map, locations ="ISOCode", locationmode="ISO-3",
                             hover_data= ["Recipient"], color_continuous_scale="Viridis", color="Klimafinanzierung",
                             range_color=(min(dat_map["Klimafinanzierung"]), max(dat_map["Klimafinanzierung"]*0.05)))
      else:
         df_kon = dat_fil.groupby(["CONTINENT"])["Klimafinanzierung"].sum().reset_index()
         df_kon = df_kon.set_index("CONTINENT")
         map_con = gdf
         map_con.update(df_kon.Klimafinanzierung)
         map_con = map_con.dropna()
         figMap = px.choropleth(map_con, geojson=map_con.geometry, locations=map_con.index,
                             color="Klimafinanzierung", color_continuous_scale="Viridis")
   figMap.update_layout(coloraxis_showscale=False)

   #Bi-/Multi Bar-chart:
   datBarMulti = dat_fil.groupby(["Year", "Channel"])[["Klimafinanzierung"]].sum().reset_index()
   figMultiBar = px.bar(datBarMulti, x="Year", y="Klimafinanzierung", color="Channel", barmode="group")
   figMultiBar.update_layout(showlegend=False)
   #Bar-chart:
   datHaushalt = dat_fil.groupby(["Year", "Haushalt"])[["Klimafinanzierung"]].sum().reset_index()
   figHaushalt = px.bar(datHaushalt, x="Year", y="Klimafinanzierung", color="Haushalt", barmode="group")
   figHaushalt.update_layout(showlegend=False)

   if ("All" in selected_country) | (selected_country == []):
      datPie = dat_fil.groupby(["Sector"])[["Klimafinanzierung"]].sum().reset_index()
      minValue = datPie["Klimafinanzierung"].nlargest(8).min()
      datPie.loc[datPie["Klimafinanzierung"] <= minValue, ["Sector"]] = "Restliche Sektoren"
      figPie = px.pie(datPie[(datPie["Klimafinanzierung"] >= minValue)],
                      values='Klimafinanzierung', names='Sector')
   else:
      datPie = dat_fil[dat_fil["Recipient"].isin(selected_country)]
      datPie = datPie.groupby(["Sector"])[["Klimafinanzierung"]].sum().reset_index()
      minValue = datPie["Klimafinanzierung"].nlargest(8).min()
      datPie.loc[datPie["Klimafinanzierung"] <= minValue, ["Sector"]] = "Restliche Sektoren"
      #Only show projects that are above 0:
      figPie = px.pie(datPie[datPie["Klimafinanzierung"] > 0],
                      values='Klimafinanzierung', names='Sector')

   #Show pie chart without title and axis:
   figPie.update_layout(yaxis={'title': ""}, xaxis={'title': ""})

   return figMap, figMultiBar, figHaushalt, figPie

if __name__ == '__main__':
    app.run_server(debug=True)
