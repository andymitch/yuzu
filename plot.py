from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas import DataFrame
from numpy import full, nan


def bar(data, col):
    marker_colors = full(data[col].shape, nan, dtype=object)
    marker_colors[data[col] > data[col].shift()] = "green"
    marker_colors[data[col] == data[col].shift()] = "grey"
    marker_colors[data[col] < data[col].shift()] = "red"
    return go.Bar(y=data[col], x=data.index, name=col, marker_color=marker_colors)


def line(data, col, color):
    return go.Scatter(y=data[col], x=data.index, mode="lines", line_shape="spline", name=col, line=dict(color=color))


def plot(data: DataFrame, subplots: list[object], name: str):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]] * 4)
    fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name=name), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.bought, x=data.index, name="bought", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.sold, x=data.index, name="sold", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.stop_lossed, x=data.index, name="stop_lossed", mode="markers", marker=dict(color="magenta", symbol="circle-open", size=10)), row=1, col=1)

    for i, subplot in enumerate(subplots):
        if subplot.get("inline", False):
            if subplot["type"] == "line":
                fig.add_trace(line(data, subplot["column"], subplot["color"]), row=1, col=1)
            elif subplot["type"] == "bar":
                fig.add_trace(bar(data, subplot["column"]), row=1, col=1)
        if i < 4:
            if subplot["type"] == "line":
                fig.add_trace(line(data, subplot["column"], subplot["color"]), row=(i % 2) + 2, col=1, secondary_y=i + 1 > 2)
            elif subplot["type"] == "bar":
                fig.add_trace(bar(data, subplot["column"]), row=(i % 2) + 2, col=1, secondary_y=i + 1 > 2)

    marker_colors = full(data["profit_diff"].shape, nan, dtype=object)
    marker_colors[data["profit_diff"] > data["profit_diff"].shift()] = "green"
    marker_colors[data["profit_diff"] == data["profit_diff"].shift()] = "grey"
    marker_colors[data["profit_diff"] < data["profit_diff"].shift()] = "red"
    fig.add_trace(go.Bar(y=data.profit_diff, x=data.index, name="profit_diff", marker_color=marker_colors), row=4, col=1)
    fig.add_trace(go.Scatter(y=data.hodl_profit, x=data.index, mode="lines", line_shape="spline", name="hodl_profit", line=dict(color="yellow")), row=4, col=1, secondary_y=True)
    if "old_trade_profit" in data.columns:
        fig.add_trace(go.Scatter(y=data.old_trade_profit, x=data.index, mode="lines", line_shape="spline", name="trade_profit (old)", line=dict(color="lime")), row=4, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(y=data.trade_profit, x=data.index, mode="lines", line_shape="spline", name="trade_profit (new)", line=dict(color="green")), row=4, col=1, secondary_y=True)

    fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
    fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
    fig.update_traces(xaxis="x")
    return fig
