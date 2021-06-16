#from multiprocessing import Pool
#from utils import get_strategy_class

##########################
from binance import Client
import pandas as pd
import numpy as np
import datetime
import json
import os

from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator, WilliamsRIndicator
from ta.volatility import AverageTrueRange
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from p_tqdm import p_map

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

class IStrategy:
    def __init__(self, pair, interval, config=None, recent=False):
        self.timeframe = get_timeframe(interval)
        self.interval = interval
        self.pair = pair
        self.data = populate_backdata(pair, interval, self.timeframe, recent=recent)
        self.populate_indicators()
        self.populate_buys()
        self.populate_sells()

    def populate_indicators(self, config=None):
        pass

    def populate_buys(self, config=None):
        pass

    def populate_sells(self, config=None):
        pass

    def plot(self, config=None):
        pass

    def backtest(self, stop_loss=.1, trading_fee=.001, verbose=False):
        starting_amount = 100.0
        self.data['trade_profit'] = [1] * len(self.data)
        self.data['hodl_profit'] = [1] * len(self.data)
        bought_in = None
        self.data['stop_loss'] = [None] * len(self.data)
        wallet = {
            'base': starting_amount,
            'asset': 0.0
        }
        stop_loss_value = None
        for i, row in self.data.iterrows():
            if not np.isnan(row['buy']) and wallet['base'] > 0:
                fee = wallet['base'] * trading_fee
                wallet['asset'] = (wallet['base'] - fee) / row['buy']
                wallet['base'] = 0.0
                stop_loss_value = row['buy'] * (1-stop_loss)
                if bought_in is None:
                    bought_in = wallet['asset']
                if verbose:
                    colorprint(i, 'buy', row['buy'], self.interval[-1] != 'd')
            elif not stop_loss_value is None and stop_loss_value > row['low']:
                fee = wallet['asset'] * trading_fee
                wallet['base'] = (wallet['asset'] - fee) * stop_loss_value
                wallet['asset'] = 0.0
                self.data.loc[i, 'stop_loss'] = stop_loss_value
                if verbose:
                    colorprint(i, 'stop_loss', stop_loss_value, self.interval[-1] != 'd')
                stop_loss_value = None
            elif not np.isnan(row['sell']) and wallet['asset'] > 0:
                fee = wallet['asset'] * trading_fee
                wallet['base'] = (wallet['asset'] - fee) * row['sell']
                wallet['asset'] = 0.0
                stop_loss_value = None
                if verbose:
                    colorprint(i, 'sell', row['sell'], self.interval[-1] != 'd')
            if not np.isnan(row['close']):
                self.data.loc[i, 'trade_profit'] = (((wallet['base'] + (wallet['asset'] * row['close'])) / starting_amount) - 1) * 100
                if not bought_in is None:
                    self.data.loc[i, 'hodl_profit'] = (((bought_in * row['close']) / starting_amount) - 1) * 100

        return self.data, self.plot()

class AwesomeOscillatorStrategy(IStrategy):

    def populate_indicators(self, config=None, confirm_with_rsi=False):
        self.data['ao'] = AwesomeOscillatorIndicator(self.data.high, self.data.low, window1=config and config.get('window1', 5) or 5, window2=config and config.get('window2', 34) or 34).awesome_oscillator()
        #self.data['rsi'] = RSIIndicator(self.data.close).rsi()
        self.data['rsi'] = WilliamsRIndicator(self.data.high, self.data.low, self.data.close).williams_r()
        #self.data['rsi'] = AverageTrueRange(self.data.high, self.data.low, self.data.close).average_true_range()

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

        marker_colors = np.full(self.data['aob'].shape, np.nan, dtype=object)
        marker_colors[self.data['aob'] >= self.data['aob'].shift()] = 'green'
        marker_colors[self.data['aob'] < self.data['aob'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.ao, x=self.data.index, name="awesome oscillator (buy)", marker_color=marker_colors), row=3, col=1)

        

        self.data["profit"] = self.data['trade_profit'] - self.data['hodl_profit']
        marker_colors[self.data['profit'] > self.data['profit'].shift()] = 'green'
        marker_colors[self.data['profit'] == self.data['profit'].shift()] = 'grey'
        marker_colors[self.data['profit'] < self.data['profit'].shift()] = 'red'
        fig.add_trace(go.Bar(y=self.data.profit, x=self.data.index, name="profit", marker_color=marker_colors), row=4, col=1)

        fig.add_trace(go.Scatter(y=self.data.hodl_profit, x=self.data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=4, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=self.data.trade_profit, x=self.data.index, mode='lines', line_shape='spline', name='trade_profit', line=dict(color='green')), row=4, col=1, secondary_y=True)

        fig.update_yaxes(spikemode='across', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode='across', spikesnap='cursor', spikedash='dot', spikecolor='grey', spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode='x', spikedistance=-1)
        fig.update_traces(xaxis='x')
        return fig
###########################

def evaluate(config):
    sucess, StrategyClass = True, AwesomeOscillatorStrategy#get_strategy_class(config['strategy'])
    if sucess:
        result, _ = StrategyClass(pair=config['pair'], interval=config['interval']).backtest(stop_loss=config['stop_loss'])
        config['score'] = result.trade_profit.iloc[-1]
        return config
    else:
        raise Exception(StrategyClass)

def Optimize(refresh_data=False):
    intervals = ['1m', '5m', '15m', '1h', '1d']
    stop_loss = [.3] # .1 # ==no stop_loss (not ideal, maybe set to a high .30-.50 ~ value just in case)
    window1s = [5] # leave at 5
    window2s = [34] # leave at 34
    strategy = 'AwesomeOscillatorStrategy'
    pair = 'ADABTC'
    configs = [{
        'interval': i,
        'stop_loss': s,
        'window1': w1,
        'window2': w2,
        'pair': pair,
        'strategy': strategy,
        'score': None
    } for i in intervals for s in stop_loss for w1 in window1s for w2 in window2s]

    '''
    with Pool() as p:
        configs = p.map(evaluate, configs)
    '''
    if refresh_data:
        from tqdm import tqdm
        for interval in tqdm(intervals):
            populate_backdata(pair, interval, get_timeframe(interval), recent=True)
    configs = p_map(evaluate, configs)
    '''
    progress, total = 0, len(configs)
    for config in configs:
        progress += 1
        print(f'[{progress}/{total}]')
        evaluate(config)
    '''
    configs.sort(key=lambda c: c['score'])
    og_data, _ = AwesomeOscillatorStrategy(pair='ADABTC', interval='1d').backtest(stop_loss=.15)
    aos = AwesomeOscillatorStrategy(pair=configs[-1]['pair'], interval=configs[-1]['interval'])
    aos.backtest(stop_loss=configs[-1]['stop_loss'])
    aos.data['hodl_profit'] = og_data['trade_profit']
    aos.get_plot().show()
    print(json.dumps(configs, indent=2))

Optimize(refresh_data=True)