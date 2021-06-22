from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator, WilliamsRIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator, NegativeVolumeIndexIndicator
from ta.trend import ADXIndicator, EMAIndicator
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from IStrategy import IStrategy
import numpy as np


class AwesomeOscillatorStrategy(IStrategy):

    def populate_indicators(self, config=None, confirm_with_rsi=False):
        self.data['ao'] = AwesomeOscillatorIndicator(self.data.high, self.data.low, window1=config and config.get('window1', 5) or 5, window2=config and config.get('window2', 34) or 34).awesome_oscillator()
        self.data['rsi'] = RSIIndicator(self.data.close, 28).rsi()
        self.data['willr'] = WilliamsRIndicator(self.data.high, self.data.low, self.data.close).williams_r()
        self.data['atr'] = AverageTrueRange(self.data.high, self.data.low, self.data.close).average_true_range()
        bbands = BollingerBands(self.data.close)
        self.data['bband_upper'] = bbands.bollinger_hband()
        self.data['bband_middle'] = bbands.bollinger_mavg()
        self.data['bband_lower'] = bbands.bollinger_lband()
        self.data['bband_width'] = ((self.data.bband_upper - self.data.bband_lower) / self.data.bband_middle)
        self.data['obv'] = OnBalanceVolumeIndicator(self.data.close, self.data.volume).on_balance_volume()
        self.data['mfi'] = MFIIndicator(self.data.high, self.data.low, self.data.close, self.data.volume).money_flow_index()
        self.data['nvi'] = NegativeVolumeIndexIndicator(self.data.close, self.data.volume).negative_volume_index()

    def populate_buys(self, config=None):
        self.data.loc[((self.data['ao'].shift() < 0) & (self.data['ao'] > 0)), "buy"] = self.data["close"]

    def populate_sells(self, config=None):
        self.data.loc[((self.data['ao'].shift() > 0) & (self.data['ao'] < 0)), "sell"] = self.data["close"]

    def get_plot(self):
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}], [{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": True}]])
        marker_colors = np.full(self.data.volume.shape, np.nan, dtype=object)
        marker_colors[self.data.volume > self.data.volume.shift()] = 'green'
        marker_colors[self.data.volume == self.data.volume.shift()] = 'grey'
        marker_colors[self.data.volume < self.data.volume.shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.volume, x=self.data.index, name="Volume", marker_color=marker_colors), row=1, col=1)

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_upper, x=self.data.index, mode='lines', line_shape='spline', name='bband_upper', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_middle, x=self.data.index, mode='lines', line_shape='spline', name='bband_middle', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bband_lower, x=self.data.index, mode='lines', line_shape='spline', name='bband_lower', line=dict(color='magenta')), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.bought, x=self.data.index, name='bought', mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.sold, x=self.data.index, name='sold', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.stoped_loss, x=self.data.index, name='stoped_loss', mode='markers', marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(y=self.data.bband_width, x=self.data.index, mode='lines', line_shape='spline', name="bband width", marker_color='orange'), row=2, col=1)
        fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name="RSI", marker_color='purple'), row=2, col=1, secondary_y=True)
        #fig.add_trace(go.Scatter(y=self.data.nvi, x=self.data.index, mode='lines', line_shape='spline', name="Negative Volume Index", marker_color='grey'), row=2, col=1, secondary_y=True)
        
        #fig.add_trace(go.Scatter(y=self.data.adx_pos, x=self.data.index, mode='lines', line_shape='spline', name='DI+', line=dict(color='green')), row=2, col=1)
        #fig.add_trace(go.Scatter(y=self.data.adx_neg, x=self.data.index, mode='lines', line_shape='spline', name='DI-', line=dict(color='red')), row=2, col=1)
        #fig.add_trace(go.Scatter(y=self.data.adx, x=self.data.index, mode='lines', line_shape='spline', name='ADX', line=dict(color='white')), row=2, col=1)
        #fig.add_trace(go.Scatter(y=self.data.atr, x=self.data.index, mode='lines', line_shape='spline', name='ATR', line=dict(color='white')), row=2, col=1)

        marker_colors = np.full(self.data['ao'].shape, np.nan, dtype=object)
        marker_colors[self.data['ao'] >= self.data['ao'].shift()] = 'green'
        marker_colors[self.data['ao'] < self.data['ao'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.ao, x=self.data.index, name="awesome oscillator", marker_color=marker_colors), row=3, col=1)
        
        self.data["profit_diff"] = EMAIndicator((self.data['trade_profit'] - self.data['hodl_profit']) - (self.data['trade_profit'].shift() - self.data['hodl_profit'].shift()), 8).ema_indicator()

        marker_colors[self.data['profit_diff'] > self.data['profit_diff'].shift()] = 'green'
        marker_colors[self.data['profit_diff'] == self.data['profit_diff'].shift()] = 'grey'
        marker_colors[self.data['profit_diff'] < self.data['profit_diff'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit_diff, x=self.data.index, name="profit_diff", marker_color=marker_colors), row=4, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=4, col=1, secondary_y=True)
        if 'old_trade_profit' in self.data.columns: fig.add_trace(go.Scatter(y=self.data.old_trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit (old)', line=dict(color='lime')), row=4, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit (new)', line=dict(color='green')), row=4, col=1, secondary_y=True)
        
        fig.update_yaxes(spikemode='across', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig


if __name__ == "__main__":
    old_strat = AwesomeOscillatorStrategy(pair='ADABTC', interval='1d', max_ticks=3000, update=True)
    old_strat.backtest(verbose=True, stop_loss=.3, trading_fee=.005)
    old_strat.data.loc[(((old_strat.data.ao.shift() > 0) & (old_strat.data.ao < 0))) | ((old_strat.data.ao > 8e-6) & (old_strat.data.ao.shift() > old_strat.data.ao)), "sell"] = old_strat.data["close"]
    old_strat.data['old_trade_profit'] = old_strat.data.trade_profit
    data, plot = old_strat.backtest(verbose=True, stop_loss=.3, trading_fee=.005)
    #print(data.to_markdown())
    plot.show()
