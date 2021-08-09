from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas import DataFrame
from numpy import full, nan
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output
from time import sleep
from threading import Thread
from IPython.display import clear_output

def plot(data):
    def render():
        while(True):
            fig = make_subplots(rows=1, cols=1)
            fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close))
            fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
            fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
            fig.update_traces(xaxis="x")
            fig.show()
            sleep(5)
            clear_output(wait=True)
    render_thread = Thread(target=render)
    render_thread.start()

'''
def plot(data):

    app = dash.Dash(__name__)
    app.layout = html.Div([
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=10*1000, # in milliseconds
            n_intervals=0
        )
    ])

    @app.callback(Output('live-update-graph', 'figure'), Input('interval-component', 'n_intervals'))
    def update_graph_live(n):
        print(len(data))
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close))
        fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
        fig.update_traces(xaxis="x")
        return fig

    app.run_server(port=7000)'''