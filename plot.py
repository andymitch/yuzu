from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas import DataFrame
from numpy import full, nan


class Plot:
    fig = None
    additional_traces = {}
    def __init__(self, data: DataFrame, name: str):
        self.data = data
        self.candle_traces = [
            {'trace': go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=name), 'secondary': False},
            {'trace': go.Scatter(y=self.data.bought, x=self.data.index, name="bought", mode="markers", marker=dict(color="cyan", symbol="circle", size=10)), 'secondary': False},
            {'trace': go.Scatter(y=self.data.sold, x=self.data.index, name="sold", mode="markers", marker=dict(color="yellow", symbol="circle", size=10)), 'secondary': False},
            {'trace': go.Scatter(y=self.data.stop_lossed, x=self.data.index, name="stop_lossed", mode="markers", marker=dict(color="magenta", symbol="circle", size=10)), 'secondary': False},
            {'trace': go.Scatter(y=self.data.buy, x=self.data.index, name="buy", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10)), 'secondary': False},
            {'trace': go.Scatter(y=self.data.sell, x=self.data.index, name="sell", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10)), 'secondary': False},
            {'trace': go.Scatter(y=self.data.stop_loss, x=self.data.index, name="stop_loss", mode="markers", marker=dict(color="magenta", symbol="circle-open", size=10)), 'secondary': False}
        ]
        self.profit_traces = [
            {'trace': self.bar('profit_diff_change'), 'secondary': False},
            {'trace': self.line('hodl_profit', 'yellow'), 'secondary': True},
            {'trace': self.line('trade_profit', 'green'), 'secondary': True}
        ]

    def add_trace(self, col: str, row: int, _type: str, color=None, secondary=False):
        trace = {'trace': None, 'secondary': secondary}
        if _type == 'bar':
            trace['trace'] = self.bar(col)
        else: # _type == 'line'
            trace['trace'] = self.line(col, color)
        if row == 0:
            self.candle_traces.append(trace)
        else:
            if row in self.additional_traces.keys():
                self.additional_traces[row].append(trace)
            else:
                self.additional_traces[row] = [trace]

    def bar(self, col):
        marker_colors = full(self.data[col].shape, nan, dtype=object)
        marker_colors[self.data[col] > self.data[col].shift()] = "green"
        marker_colors[self.data[col] == self.data[col].shift()] = "grey"
        marker_colors[self.data[col] < self.data[col].shift()] = "red"
        return go.Bar(y=self.data[col], x=self.data.index, name=col, marker_color=marker_colors)

    def line(self, col, color):
        return go.Scatter(y=self.data[col], x=self.data.index, mode="lines", line_shape="spline", name=col, line=dict(color=color))

    def __setup_fig(self):
        row_count = 2 + len(self.additional_traces)
        self.fig = make_subplots(rows=row_count, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]] * row_count)
        for trace in self.candle_traces:
            self.fig.add_trace(trace['trace'], row=1, col=1, secondary_y=trace['secondary'])
        for row, subplots in self.additional_traces.items():
            for subplot in subplots:
                self.fig.add_trace(subplot['trace'], row=row+1, col=1, secondary_y=subplot['secondary'])
        for trace in self.profit_traces:
            self.fig.add_trace(trace['trace'], row=row_count, col=1, secondary_y=trace['secondary'])
        self.fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
        self.fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
        self.fig.update_traces(xaxis="x")

    def show(self):
        self.__setup_fig()
        self.fig.show()

    def get(self):
        self.__setup_fig()
        return self.fig

from numpy import linspace
def plot_compare(profit_lines, index):
    def format_str(c):
        s = str(hex(int(c)))[2:]
        for _ in range(6-len(s)):
            s = '0' + s
        return '#' + s
    line_count = len(profit_lines)
    green, yellow = 0x00ff00, 0xffff00
    colors_int = list(linspace(green, yellow, line_count))
    colors_str = [format_str(c) for c in colors_int]
    colors_str.reverse()
    fig = make_subplots(rows=1, cols=1)
    for i in range(len(profit_lines)):
        fig.add_trace(go.Scatter(y=profit_lines[i], x=index, mode="lines", line_shape="spline", line=dict(color=colors_str[i])), row=1, col=1)
    fig.show()
