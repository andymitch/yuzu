from binance import Client
import pandas as pd
import numpy as np
import datetime
import os


def colorprint(i, col, val, include_time=True):
    time_str = "%b %d, %Y [%H:%M]" if include_time else "%b %d, %Y"
    if col == 'buy':
        print(f'\033[96m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}       @ {val}\033[00m')
    elif col == 'sell':
        print(f'\033[93m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
    elif col == 'stop_loss':
        print(f'\033[91m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col} @ {val}\033[00m')

def populate_backdata(pair, interval, start, finish, update=False):
    file_path = f'./yuzu/backdata/{pair}-{interval.upper()}.csv'
    if update or not os.path.exists(file_path):
        client = Client()
        klines = client.get_historical_klines(pair, interval, start, finish)
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

def get_timeframe(interval, max_ticks):
    interval_map = {'m': 'minutes', 'h': 'hours', 'd': 'days'}
    num = int(interval[:-1]) * max_ticks
    return f'{num} {interval_map[interval[-1]]} ago'

class IStrategy:
    def __init__(self, pair, interval, config=None, update=False, max_ticks=1000, timeframes_back=0):
        start = get_timeframe(interval, max_ticks + (max_ticks * timeframes_back))
        finish = get_timeframe(interval, max_ticks * timeframes_back)
        self.interval = interval
        self.pair = pair
        self.data = populate_backdata(pair, interval, start=start, finish=finish, update=update)
        self.populate_indicators()
        self.populate_buys(config)
        self.populate_sells(config)

    def populate_indicators(self, config=None):
        pass

    def populate_buys(self, config=None):
        pass

    def populate_sells(self, config=None):
        pass

    def get_plot(self, config=None):
        pass

    def backtest(self, stop_loss=.35, trading_fee=.001, verbose=False):
        starting_amount = 100.0
        self.data['trade_profit'] = [0] * len(self.data)
        self.data['hodl_profit'] = [0] * len(self.data)
        bought_in = None
        self.data['stop_loss'] = [None] * len(self.data)
        wallet = {
            'base': starting_amount,
            'asset': 0.0
        }
        self.data['bought'] = [None] * len(self.data)
        self.data['sold'] = [None] * len(self.data)
        self.data['stoped_loss'] = [None] * len(self.data)
        stop_loss_value = None
        for i, row in self.data.iterrows():
            if not np.isnan(row['buy']) and wallet['base'] > 0:
                self.data.loc[i, 'bought'] = self.data.loc[i, 'close']
                fee = wallet['base'] * trading_fee
                wallet['asset'] = (wallet['base'] - fee) / row['buy']
                wallet['base'] = 0.0
                stop_loss_value = row['buy'] * (1-stop_loss)
                if bought_in is None:
                    bought_in = wallet['asset']
                if verbose:
                    colorprint(i, 'buy', row['buy'], self.interval[-1] != 'd')
            elif not stop_loss_value is None and stop_loss_value > row['low']:
                self.data.loc[i, 'stoped_loss'] = self.data.loc[i, 'close']
                fee = wallet['asset'] * trading_fee
                wallet['base'] = (wallet['asset'] - fee) * stop_loss_value
                wallet['asset'] = 0.0
                self.data.loc[i, 'stop_loss'] = stop_loss_value
                if verbose:
                    colorprint(i, 'stop_loss', stop_loss_value, self.interval[-1] != 'd')
                stop_loss_value = None
            elif not np.isnan(row['sell']) and wallet['asset'] > 0:
                self.data.loc[i, 'sold'] = self.data.loc[i, 'close']
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

        return self.data, self.get_plot()