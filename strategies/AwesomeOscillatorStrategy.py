from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from IStrategy import IStrategy
import numpy as np


class AwesomeOscillatorStrategy(IStrategy):

    def populate_indicators(self, confirm_with_rsi=False):
        self.data['ao'] = AwesomeOscillatorIndicator(self.data.high, self.data.low).awesome_oscillator()
        self.data['rsi'] = RSIIndicator(self.data.close).rsi()

    def populate_buys(self):
        self.data.loc[((self.data['ao'].shift() < 0) & (self.data['ao'] > 0)), "buy"] = self.data["close"]

    def populate_sells(self):
        self.data.loc[((self.data['ao'].shift() > 0) & (self.data['ao'] < 0)), "sell"] = self.data["close"]

    def plot(self):
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]])

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.buy, x=self.data.index, name='buy', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.sell, x=self.data.index, name='sell', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.stop_loss, x=self.data.index, name='stop_loss', mode='markers', marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1)

        fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name='rsi', line=dict(color='purple')), row=2, col=1)

        marker_colors = np.full(self.data['ao'].shape, np.nan, dtype=object)
        marker_colors[self.data['ao'] >= self.data['ao'].shift()] = 'green'
        marker_colors[self.data['ao'] < self.data['ao'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.ao, x=self.data.index, name="awesome oscillator", marker_color=marker_colors), row=3, col=1)

        self.data["profit"] = self.data['trade_profit'] - self.data['hodl_profit']
        marker_colors[self.data['profit'] >= self.data['profit'].shift()] = 'green'
        marker_colors[self.data['profit'] < self.data['profit'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit, x=self.data.index, name="profit", marker_color=marker_colors), row=4, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=4, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit', line=dict(color='green')), row=4, col=1, secondary_y=True)

        fig.update_yaxes(spikemode='across', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig


results, plot = AwesomeOscillatorStrategy(pair='ADABTC', interval='1d').backtest(verbose=True, stop_loss=.15)
print(results)
plot.show()
