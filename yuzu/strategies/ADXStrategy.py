from IStrategy import IStrategy
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
from binance import Client
import pandas as pd
import datetime
import os
from p_tqdm import p_map

class ADXStrategy(IStrategy):

    def populate_indicators(self):
        adx = ADXIndicator(self.data['high'], self.data['low'], self.data['close'])
        self.data['adx'] = adx.adx()
        self.data['adx_pos'] = adx.adx_pos()
        self.data['adx_neg'] = adx.adx_neg()
        self.data['rsi'] = RSIIndicator(self.data.close).rsi()

    def populate_buys(self, config=None):
        rsi_buy_range = config and config.get('rsi_buy_range', 30) or 30
        adx_filter = config and config.get('adx_filter', 20) or 20
        self.data.loc[(
            (self.data['adx'] > adx_filter) & (self.data['adx_pos'] > self.data['adx_neg'])
            & (
                (self.data['adx'].shift() < adx_filter) | (self.data['adx_pos'].shift() < self.data['adx_neg'].shift())
            ) & (self.data.rsi < rsi_buy_range)
        ), "buy"] = self.data["close"]


    def populate_sells(self, config=None):
        rsi_sell_range = config and config.get('rsi_sell_range', 70) or 70
        adx_filter = config and config.get('adx_filter', 20) or 20
        self.data.loc[(
            (self.data['adx'] > adx_filter) & (self.data['adx_pos'] < self.data['adx_neg'])
            & (
                (self.data['adx'].shift() < adx_filter) | (self.data['adx_pos'].shift() > self.data['adx_neg'].shift())
            ) & (self.data.rsi > rsi_sell_range)
        ), "sell"] = self.data["close"]

    def get_plot(self):
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]])

        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.open, high=self.data.high, low=self.data.low, close=self.data.close, name=self.pair), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.buy, x=self.data.index, mode='markers', marker=dict(color='cyan', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.sell, x=self.data.index, mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=self.data.stop_loss, x=self.data.index, name='stop_loss', mode='markers', marker=dict(color='magenta', symbol='circle-open', size=10)), row=1, col=1)

        fig.add_trace(go.Scatter(y=self.data.adx_pos, x=self.data.index, mode='lines', line_shape='spline', name='DI+', line=dict(color='green')), row=2, col=1)
        fig.add_trace(go.Scatter(y=self.data.adx_neg, x=self.data.index, mode='lines', line_shape='spline', name='DI-', line=dict(color='red')), row=2, col=1)
        fig.add_trace(go.Scatter(y=self.data.adx, x=self.data.index, mode='lines', line_shape='spline', name='ADX', line=dict(color='white')), row=2, col=1)

        fig.add_trace(go.Scatter(y=self.data.rsi, x=self.data.index, mode='lines', line_shape='spline', name='RSI', line=dict(color='purple')), row=3, col=1)

        self.data["profit_diff"] = self.data['trade_profit'] - self.data['hodl_profit']
        marker_colors = np.full(self.data['profit_diff'].shape, np.nan, dtype=object)
        marker_colors[self.data['profit_diff'] > self.data['profit_diff'].shift()] = 'green'
        marker_colors[self.data['profit_diff'] == self.data['profit_diff'].shift()] = 'grey'
        marker_colors[self.data['profit_diff'] < self.data['profit_diff'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit_diff, x=self.data.index, name="profit_diff", marker_color=marker_colors), row=4, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=4, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit', line=dict(color='green')), row=4, col=1, secondary_y=True)

        fig.update_yaxes(spikemode='across', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig

#data, plot = ADXStrategy(pair='ETHBTC', interval='1d', max_ticks=1000).backtest()
#plot.show()

def colorprint(i, col, val, include_time=True):
    time_str = "%b %d, %Y [%H:%M]" if include_time else "%b %d, %Y"
    if col == 'buy':
        print(f'\033[96m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}       @ {val}\033[00m')
    elif col == 'sell':
        print(f'\033[93m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
    elif col == 'stop_loss':
        print(f'\033[91m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col} @ {val}\033[00m')

def populate_backdata(pair, interval, timeframe, recent=False):
    file_path = f'./yuzu/backdata/{pair}-{interval.upper()}.csv'
    if recent or not os.path.exists(file_path):
        client = Client()
        klines = client.get_historical_klines(pair, interval, timeframe)
        cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
        data = pd.DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric, axis=1)
        data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(float(t / 1000)).isoformat())
        data = data.set_index("time").sort_index()
        data.to_csv(file_path)
        return data
    else:
        data = pd.read_csv(file_path)
        data = data.set_index("time").sort_index()
        return data

def get_timeframe(interval):
    interval_map = {'m': 'minutes', 'h': 'hours', 'd': 'days'}
    num = int(interval[:-1]) * 1000
    return f'{num} {interval_map[interval[-1]]} ago'

def evaluate(config):
    sucess, StrategyClass = True, ADXStrategy
    if sucess:
        result, _ = StrategyClass(pair=config['pair'], interval=config['interval'], config=config).backtest(stop_loss=config['stop_loss'])
        config['score'] = result.trade_profit.iloc[-1]
        return config
    else:
        raise Exception(StrategyClass)

def Optimize():
    intervals = ['1m', '5m', '15m', '1h', '1d']
    stop_loss = [.1, .2, .3, .4]
    rsi_buy_ranges = [30, 40, 50, 60, 70]
    rsi_sell_ranges = [30, 40, 50, 60, 70]
    adx_filters = [10, 20, 30, 40, 50]
    strategy = 'ADXStrategy'
    pair = 'ADABTC'
    configs = [{
        'interval': i,
        'stop_loss': s,
        'rsi_buy_range': rbr,
        'rsi_sell_range': rsr,
        'adx_filter': adxf,
        'pair': pair,
        'strategy': strategy,
        'score': None
    } for i in intervals for s in stop_loss for rbr in rsi_buy_ranges for rsr in rsi_sell_ranges for adxf in adx_filters]

    from tqdm import tqdm
    for interval in tqdm(intervals):
        populate_backdata(pair, interval, get_timeframe(interval), recent=True)
    configs = p_map(evaluate, configs)
    configs.sort(key=lambda c: c['score'])
    _, plot = ADXStrategy(pair=configs[-1]['pair'], interval=configs[-1]['interval'], config=configs[-1]).backtest(stop_loss=configs[-1]['stop_loss'])
    plot.show()
    print(pd.DataFrame(configs).to_markdown())

Optimize()