from __future__ import print_function
#from apiclient.discovery import build
#from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
#import geopandas as gpd
import numpy as np
#from pprint import pprint
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
#import dash_table_experiments as dt
import dash_table
#import plotly.graph_objs as go
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

#gdf = pd.read_csv("ref.csv")

#with open("map_geojson.json", "r") as file:
    #map = json.load(file)

token = "C7g8c1wejc|j@O1OEd1!vTm[kU`nJCzk/dS{|v+2FK-kJOI+OoZK)0>$)qYr!"
plotly.express.set_mapbox_access_token(token)

zone_colormap = {'unset'        : '#454140',
                 'natural'      : '#405d27',
                 'public'       : '#ffcc5c',
                 'residential'  : '#bd5734',
                 'commercial'   : '#034f84',
                 'government'   : '#622569',
                 'military'     : '#c83349'}
# disassemble dictionary so it is readable in html
zones = list(zone_colormap.keys())
colors = list(zone_colormap.values())
print("colors: ", colors)
print("zones: ", zones )

# Figure Generation ------------------------------------------------------------
def makeDiscreteFigure(df, colormap, use_type, inTitle):
    fig = px.scatter_mapbox(df, lat='lat', lon='lon', color=use_type, size='marker',
                        hover_name=df.index, hover_data=None, zoom=12,
                        mapbox_style='open-street-map',
                        width=1200, height=1000, opacity=0.5,
                        center=dict(lat=-7.33274864, lon=72.42798532),
                        title = inTitle,
                        color_discrete_map=zone_colormap )

    fig.update_layout(coloraxis_showscale=False, clickmode='event+select')

    return fig

def makeContinuousFigure(df, colormap):
    return 'test'

# Handle Google Sheet information ----------------------------------------------
def sheet2gdf():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def df2sheet(df):
    # refetch dataframe from sheet to better prevent overwriting during high traffic
    #df1 = sheet2gdf()
    #df1['land use'] = df['land use']
    for i in range(6, len(zones)+6):
        zone = zones[i-6]
        for j in range(len(df[zone])):
            if df.iloc[j].at['land use']==zone:
                oval = df.iloc[j].at[zone]
                row = df.iloc[j]
                row[i] = oval+1
                df.iloc[j] = row
                #df1.iat[j, i] = oval+1
    for j in range(len(df["top land use"])):
        row = df.iloc[j].to_list()
        zrow = row[6:]
        midx = zrow.index(max(zrow))
        col = df.columns.values.tolist()
        max_zone = col[midx+6]
        row[5] = max_zone
        df.iloc[j] = row


    df['land use'] = 'unset'
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    return df

# Initialization ---------------------------------------------------------------
df = sheet2gdf()
df.reset_index()
jdf = df.to_json()
print(df.head())
fig = makeDiscreteFigure(df, zone_colormap, 'land use', 'User Choices')
tfig = makeDiscreteFigure(df, zone_colormap, 'land use', 'Top Choices from All Users')

# Styling ----------------------------------------------------------------------
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

# App Layout -------------------------------------------------------------------
app.layout = html.Div([
    html.H1('Diego Garcia Native Zoning Plan - Demo Build 4/19', style={'text-align' : 'center'}),
    html.Br(),
    dcc.Markdown("Choose a zone and click on a point to change to your choice"),
    dcc.Dropdown(id='zone-dropdown',
                 options=[{'label' : z, 'value' : z} for z in zones],
                 value='unset',
                 clearable=False),

    dcc.Graph(id='DG_map', figure=fig),

    html.Button('Submit', id='submit-button', n_clicks=0),
    html.Div(id='container-button-basic',
             children='Enter a value and press submit'),

     dcc.Graph(id='Totals_map', figure=tfig),

    html.Div([
        dcc.Markdown('*** DEBUG: Hover Data: ***'),
        html.Pre(id='hover-data', style=styles['pre']),
    ], className='debug'),

     html.Div([
        dcc.Markdown("*** DEBUG: Click Data: ***"),
        html.Pre(id='click-data', style=styles['pre']),
    ], className='debug'),


    dcc.Store(id='container-selector',
              storage_type='local',
              data='unset'),

    dash_table.DataTable(id='table',
                         columns= [{"name": i, "id": i} for i in df.columns],
                         data = df.to_dict('records')),

    html.Div(id='container-df', children=jdf, style={'display': 'none'}),
    html.Div(id='container-zones', children=zones, style={'display': 'none'}),
    html.Div(id='container-colors', children=colors, style={'display': 'none'}),
    html.Div(id='container-submitflag', children=False, style={'display': 'none'})
])

# Event Handling ---------------------------------------------------------------

# Hover Text Debug
@app.callback(
      Output('hover-data', 'children'),
      Input('DG_map', 'hoverData'))
def display_hover_data(hoverData):
    return json.dumps(hoverData, indent=2)

# Handle zone selection and setting
@app.callback(
      Output('container-selector', 'data'),
      Output('click-data', 'children'),
      Output('container-df', 'children'),
      Output('DG_map', 'figure'),
      Output('table', 'data'),
      [Input('DG_map', 'clickData'),
       Input('zone-dropdown', 'value'),
       Input('container-selector', 'data'),
       Input('container-df', 'children'),
       Input('container-zones', 'children'),
       Input('container-colors', 'children'),
       Input('DG_map', 'figure')])
def handle_click_data(clickData, dropdown, selector_val, jsondat, zones, colors, fig):
    jdata = json.loads(jsondat)
    ldf = pd.DataFrame(jdata)
    level = str(ldf.index)
    if dropdown!=selector_val or not clickData:
        clickDat = ""
        level = "NULL"
        selector_val = dropdown
    else:
        idx = int(clickData['points'][0]['hovertext'])
        loc = ldf.iloc[idx].at['location']
        lat = ldf.iloc[idx].at['lat']
        lon = ldf.iloc[idx].at['lon']
        mar = ldf.iloc[idx].at['marker']
        top = ldf.iloc[idx].at['top land use']
        uns = ldf.iloc[idx].at['unset']
        nat = ldf.iloc[idx].at['natural']
        pub = ldf.iloc[idx].at['public']
        res = ldf.iloc[idx].at['residential']
        com = ldf.iloc[idx].at['commercial']
        gov = ldf.iloc[idx].at['government']
        mil = ldf.iloc[idx].at['military']

        row = [loc, lat, lon, mar, selector_val, top, uns, nat, pub, res, com, gov, mil]
        ldf.iloc[idx] = row
        #ldf.iat[idx, selector_val] = ldf.iat[idx, selector_val]+1


        #level ="idx: " + str(idx) + ", loc:" + str(loc) + ", lat:"+ str(lat) + ", lon:" + str(lon) + ", mar:" + str(mar) + ", res:" + str(res) + ", nat:" + str(nat) + ", com:" + str(com) + ", oce:", str(oce) + ", lan:" + str(lan)
        level = "cheese crackers"

        colormap = {zones[i]: colors[i] for i in range(len(zones))}
        fig = makeDiscreteFigure(ldf, colormap, 'land use', 'User Choices')



    ljdf = ldf.to_json()
    outdata = ldf.to_dict('records')
    zChange = False
    return selector_val, level, ljdf, fig, outdata

# Handle Submission Button
@app.callback(
      Output('container-button-basic', 'children'),
      Output('submit-button', 'n_clicks'),
      Output('Totals_map', 'figure'),
      [Input('submit-button', 'n_clicks'),
       Input('container-df', 'children'),
       Input('Totals_map', 'figure')])
def handle_submission(n_clicks, jsondat, fig):
    jdata = json.loads(jsondat)
    ldf = pd.DataFrame(jdata)
    if n_clicks==1:
        fdf = df2sheet(ldf)
        #to ensure only one tally of updated df
        n_clicks+=1
        fig = makeDiscreteFigure(fdf, zone_colormap, 'top land use', 'Top Choices from All Users')

    outstr = '''Once you are sure of your choices, press submit. Once you have submitted\n
                you will be able to see the top choices from other users on the map below.\n
                Don't submit until you are absolutely sure though, you cannot change your\n
                choices after pressing submit!'''
    return outstr, n_clicks, fig

if __name__ == "__main__":
    app.run_server(debug=True)
