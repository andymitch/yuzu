import requests
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas import DataFrame
from numpy import full, nan

def bar(data, name):
    marker_colors = full(data[name].shape, nan, dtype=object)
    marker_colors[(data[name] > data[name].shift()) & (data[name] > 0)] = "green"
    marker_colors[(data[name] > data[name].shift()) & (data[name] < 0)] = "RGBA(255, 0, 0, .25)"
    marker_colors[data[name] == data[name].shift()] = "grey"
    marker_colors[(data[name] < data[name].shift()) & (data[name] > 0)] = "RGBA(0, 255, 0, .25)"
    marker_colors[(data[name] < data[name].shift()) & (data[name] < 0)] = "red"
    return go.Bar(y=data[name], x=data.index, name=name, marker_color=marker_colors)

def line(data, name, color):
    return go.Scatter(y=data[name], x=data.index, mode="lines", line_shape="spline", name=name, line=dict(color=color))

def plot(data):
    fig = make_subplots(rows=3, cols=1)
    fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name='ADAUSD'), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.buy, x=data.index, name="buy", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.sell, x=data.index, name="sell", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(bar(data, 'hist'), row=2, col=1)
    fig.add_trace(line(data, 'rsi', 'purple'), row=3, col=1)
    fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
    fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
    fig.update_traces(xaxis="x")
    fig.show()

raw = requests.get('http://127.0.0.1:8000/').json()
data = DataFrame.from_dict(raw)
print(data)
plot(data)