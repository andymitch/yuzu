from IStrategy import IStrategy
from ta.trend import EMAIndicator
from ta.momentum import StochasticOscillator
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
from binance import Client
import pandas as pd
import datetime
import os
from p_tqdm import p_map

class EMASOStrategy(IStrategy):
    def populate_indicators(self):
        self.data['ema_fast'] = EMAIndicator(self.data.close, window=50)
        self.data['ema_slow'] = EMAIndicator(self.data.close, window=100)
        self.data['stoch'] = StochasticOscillator(self.data.high, self.data.low, self.data.close, window=5, smooth_window=3)

    def get_plot(self):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]])#False}], [{"secondary_y": True}]])

        fig.add_trace(go.Scatter(y=self.data.ema_fast, x=self.data.index, mode='lines', line_shape='spline', name='EMA 50', line=dict(color='teal')), row=3, col=1)
        fig.add_trace(go.Scatter(y=self.data.ema_slow, x=self.data.index, mode='lines', line_shape='spline', name='EMA 100', line=dict(color='purple')), row=3, col=1)
        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1)
        #fig.add_trace(go.Scatter(y=self.data.buy, x=self.data.index, name='buy', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1)
        #fig.add_trace(go.Scatter(y=self.data.sell, x=self.data.index, name='sell', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        #fig.add_trace(go.Scatter(y=self.data.stop_loss, x=self.data.index, name='stop_loss', mode='markers', marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1)


        marker_colors = np.full(self.data['stoch'].shape, np.nan, dtype=object)
        marker_colors[self.data['stoch'] >= self.data['stoch'].shift()] = 'green'
        marker_colors[self.data['stoch'] < self.data['stoch'].shift()] = 'red'
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

EMASOStrategy(pair='ETHBTC', interval='1d', max_ticks=1000).get_plot().show()