from binance import Client
from pandas import DataFrame, to_numeric, read_json
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime
from pytz import reference
from strategies.macdas_strat import macdas_strat, min_ticks, best_config, plot
import requests
import json


pair, interval = 'BTCUSDT', '1m'

app = dash.Dash(__name__, title=f'{pair} ({interval}) - macdas_strat')
app.layout = html.Div([
    dcc.Graph(id='live-update-graph', style={'height': '99vh', 'padding': '0', 'margin': '0'}),
    dcc.Interval(
        id='interval-component',
        interval=10*1000, # milliseconds
        n_intervals=0
    )
], style={'height': '100%', 'padding': '0', 'margin': '0'})

@app.callback(Output('live-update-graph', 'figure'), Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    data = read_json(requests.get('http://127.0.0.1:8000/').text)
    return plot(data, pair, interval, dark_mode=True).get()

app.run_server(port=7000)