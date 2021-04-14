from __future__ import print_function
#from apiclient.discovery import build
#from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
#import geopandas as gpd
import numpy as np
from pprint import pprint
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go
import plotly.express as px
import plotly
import json
from credentials import Credentials

app = dash.Dash(__name__)
server = app.server

# -----------------------------------------------------------------------------
# Fetch Data from Google Sheets and geojson files

scope = ["https://spreadsheets.google.com/feeds",
         'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

sheet = client.open("DiegoGarciaEntries").sheet1
# Google Sheet Credentials
#SPREADSHEET_ID = '1Fu5xHJhINxRlEPzYZezSIQsJSB_g9xGTBjpg0vPYTUU'
#RANGE_NAME = 'volcanos!A:T'

# Map Credentials
#MAPBOX_API_TOKEN = Credentials.MAPBOX_API_TOKEN
def sheet2gdf(sheet):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    print(df['location'].head())
    return df

df = sheet2gdf(sheet)
#gdf = pd.read_csv("ref.csv")

#with open("map_geojson.json", "r") as file:
    #map = json.load(file)

# figure ---------------------------------------------------------------------

#fig = px.choropleth(gdf, locations='location', geojson=map,
#                           color_continuous_scale="Viridis", fitbounds='geojson',
#                           range_color=(0, 12), width=700, height=900,
#                           center= dict(lat=-7.33274864, lon=72.42798532) )
token = "C7g8c1wejc|j@O1OEd1!vTm[kU`nJCzk/dS{|v+2FK-kJOI+OoZK)0>$)qYr!"
plotly.express.set_mapbox_access_token(token)

colormap = {"ocean" : "#87bdd8",
            "land"  : "#B6E880"}

fig = px.scatter_mapbox(df, lat="lat", lon="lon", color="land use", size='size',
                        hover_name=None, hover_data=None, zoom=12,
                        mapbox_style="open-street-map",
                        width=1200, height=1000, opacity=0.5,
                        center=dict(lat=-7.33274864, lon=72.42798532),
                        title = "Diego Garcia - User Set Map",
                        color_discrete_map=colormap )

fig.update_layout(coloraxis_showscale=False)

# ----------------------------------------------------------------------------
# app layout
app.layout = html.Div([
    html.H1("Get yo ass off my island", style={'text-align' : 'center'}),
    html.Div(id='output_container', children=[]),
    html.Br(),
    dcc.Graph(id='DG_map', figure=fig)

])


if __name__ == "__main__":
    app.run_server(debug=True)
