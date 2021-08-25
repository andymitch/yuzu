from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.io import to_html

def plot(data, as_html: bool = False, embed: bool = False):
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.buy, x=data.index, name="buy", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.sell, x=data.index, name="sell", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.bought, x=data.index, name="bought", mode="markers", marker=dict(color="cyan", symbol="circle", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.sold, x=data.index, name="sold", mode="markers", marker=dict(color="yellow", symbol="circle", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.stop_lossed, x=data.index, name="stop lossed", mode="markers", marker=dict(color="magenta", symbol="circle", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.balance, x=data.index, mode="lines", line_shape="spline", name='balance', line=dict(color='green')), row=2, col=1)
    fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
    fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
    fig.update_traces(xaxis="x")
    return to_html(fig, full_html=not embed) if as_html else fig