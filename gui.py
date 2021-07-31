from binance import Client
from pandas import DataFrame, to_numeric, read_json
import dash
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


def get_backdata(pair, interval, min_ticks):
    url = 'http://127.0.0.1:8000/'
    data = read_json(requests.get(url).text)
    data['bought'] = None
    data['sold'] = None
    data['stop_lossed'] = None
    data['stop_loss'] = None
    return data
    klines = json.loads(requests.get(url).text)
    cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
    data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
    data["time"] = data["time"].apply(lambda t: datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%dT%H:%M:%S'))
    data['bought'] = None
    data['sold'] = None
    data['stop_lossed'] = None
    data['stop_loss'] = None
    return data.set_index("time").sort_index()


app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        dcc.Graph(id='live-update-graph', style={'height': '99vh', 'padding': '0', 'margin': '0'}),
        dcc.Interval(
            id='interval-component',
            interval=10*1000, # milliseconds
            n_intervals=0
        )
    ], style={'height': '100%', 'padding': '0', 'margin': '0'})
, style={'height': '100%', 'padding': '0', 'margin': '0'})

@app.callback(Output('live-update-graph', 'figure'), Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    pair, interval = 'BTCUSDT', '1h'
    data = get_backdata(pair, interval, 1000)
    data = macdas_strat(data, best_config)
    return plot(data, pair, interval).get()

app.run_server(port=8090)