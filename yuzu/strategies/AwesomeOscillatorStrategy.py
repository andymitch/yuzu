from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator, WilliamsRIndicator
from ta.volatility import AverageTrueRange
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from IStrategy import IStrategy
import numpy as np


class AwesomeOscillatorStrategy(IStrategy):

    def populate_indicators(self, config=None, confirm_with_rsi=False):
        self.data['ao'] = AwesomeOscillatorIndicator(self.data.high, self.data.low, window1=config and config.get('window1', 5) or 5, window2=config and config.get('window2', 34) or 34).awesome_oscillator()
        #self.data['rsi'] = RSIIndicator(self.data.close).rsi()
        #self.data['rsi'] = WilliamsRIndicator(self.data.high, self.data.low, self.data.close).williams_r()
        #self.data['rsi'] = AverageTrueRange(self.data.high, self.data.low, self.data.close).average_true_range()

    def populate_buys(self):
        self.data.loc[((self.data['ao'].shift() < 0) & (self.data['ao'] > 0)), "buy"] = self.data["close"]

    def populate_sells(self):
        self.data.loc[((self.data['ao'].shift() > 0) & (self.data['ao'] < 0)), "sell"] = self.data["close"]

    def get_plot(self):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]])#False}], [{"secondary_y": True}]])

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.buy, x=self.data.index, name='buy', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.sell, x=self.data.index, name='sell', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.stop_loss, x=self.data.index, name='stop_loss', mode='markers', marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1)

        #fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name='rsi', line=dict(color='purple')), row=2, col=1)

        marker_colors = np.full(self.data['ao'].shape, np.nan, dtype=object)
        marker_colors[self.data['ao'] >= self.data['ao'].shift()] = 'green'
        marker_colors[self.data['ao'] < self.data['ao'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.ao, x=self.data.index, name="awesome oscillator", marker_color=marker_colors), row=2, col=1)

        

        self.data["profit_diff"] = self.data['trade_profit'] - self.data['hodl_profit']
        marker_colors[self.data['profit_diff'] > self.data['profit_diff'].shift()] = 'green'
        marker_colors[self.data['profit_diff'] == self.data['profit_diff'].shift()] = 'grey'
        marker_colors[self.data['profit_diff'] < self.data['profit_diff'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit_diff, x=self.data.index, name="profit_diff", marker_color=marker_colors), row=3, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=3, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit', line=dict(color='green')), row=3, col=1, secondary_y=True)

        fig.update_yaxes(spikemode='across', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig


if __name__ == "__main__":
    results, plot = AwesomeOscillatorStrategy(pair='ETHBTC', interval='1d', max_ticks=1000).backtest(verbose=True, stop_loss=.3, trading_fee=.005)
    print(results.to_markdown())
    plot.show()
