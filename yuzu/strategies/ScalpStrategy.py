from IStrategy import IStrategy
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

class ScalpStrategy(IStrategy):
    config = {
        'rsi_t': 21,
        'rsi_above': 70,
        'rsi_below': 30,
        'ema_fast_short': 8,
        'ema_slow_short': 21,
        'ema_fast_long': 50,
        'ema_slow_long': 100
    }

    def populate_indicators(self, config=None):
        if not config is None:
            self.config = config

        self.data['rsi'] = RSIIndicator(self.data.close, self.config['rsi_t']).rsi()
        self.data['ema_fast_short'] = EMAIndicator(self.data.close, self.config['ema_fast_short']).ema_indicator()
        self.data['ema_slow_short'] = EMAIndicator(self.data.close, self.config['ema_slow_short']).ema_indicator()
        self.data['ema_fast_long'] = EMAIndicator(self.data.close, self.config['ema_fast_long']).ema_indicator()
        self.data['ema_slow_long'] = EMAIndicator(self.data.close, self.config['ema_slow_long']).ema_indicator()

    def populate_buys(self, config=None):
        self.data.loc[((self.data.ema_fast_short.shift() < self.data.ema_slow_short.shift()) & (self.data.ema_fast_short > self.data.ema_slow_short) & (self.data.ema_fast_long > self.data.ema_slow_long)), "buy"] = self.data["close"]
        self.data.loc[((self.data.ema_fast_short.shift() < self.data.ema_slow_short.shift()) & (self.data.ema_fast_short > self.data.ema_slow_short) & (self.data.rsi < self.config['rsi_below'])), "buy_r"] = self.data["close"]

    def populate_sells(self, config=None):
        self.data.loc[((self.data.ema_fast_short.shift() > self.data.ema_slow_short.shift()) & (self.data.ema_fast_short < self.data.ema_slow_short) & (self.data.ema_fast_long < self.data.ema_slow_long)), "sell"] = self.data["close"]
        self.data.loc[((self.data.ema_fast_short.shift() < self.data.ema_slow_short.shift()) & (self.data.ema_fast_short > self.data.ema_slow_short) & (self.data.rsi > self.config['rsi_above'])), "sell_r"] = self.data["close"]

    def get_plot(self, config=None):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]])

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1)

        fig.add_trace(go.Scatter(y=self.data.ema_fast_short, x=self.data.index, mode='lines', line_shape='spline', name='EMA fast/fast', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.ema_slow_short, x=self.data.index, mode='lines', line_shape='spline', name='EMA fast/slow', line=dict(color='aqua')), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.ema_fast_long, x=self.data.index, mode='lines', line_shape='spline', name='EMA slow/fast', line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.ema_slow_long, x=self.data.index, mode='lines', line_shape='spline', name='EMA slow/slow', line=dict(color='salmon')), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.buy, x=self.data.index, name='buy (double ema)', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.sell, x=self.data.index, name='sell (double ema)', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.buy_r, x=self.data.index, name='buy (rsi)', mode='markers', marker=dict(color='cyan', symbol='x', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.sell_r, x=self.data.index, name='sell (rsi)', mode='markers', marker=dict(color='yellow', symbol='x', size=10)), row=1, col=1)

        fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name='rsi', line=dict(color='purple')), row=2, col=1)
        
        marker_colors = np.full(self.data.trade_profit.shape, np.nan, dtype=object)
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


data, plot = ScalpStrategy('ADABTC', '5m', max_ticks=100000, recent=True).backtest()
plot.show()