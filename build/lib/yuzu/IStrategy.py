from binance import Client
import pandas as pd
import numpy as np
import datetime


def colorprint(i, col, val, include_time=True):
    time_str = "%b %d, %Y [%H:%M]" if include_time else "%b %d, %Y"
    if col == 'buy':
        print(f'\033[96m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}       @ {val}\033[00m')
    elif col == 'sell':
        print(f'\033[93m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
    elif col == 'stop_loss':
        print(f'\033[91m{datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col} @ {val}\033[00m')

def populate_backdata(pair, interval, timeframe, recent=False):
    file_path = f'./backdata/{pair}-{interval.upper()}.csv'
    if recent:
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
    def __init__(self, pair, interval):
        self.timeframe = get_timeframe(interval)
        self.interval = interval
        self.pair = pair
        self.data = populate_backdata(pair, interval, self.timeframe)
        self.populate_indicators()
        self.populate_buys()
        self.populate_sells()

    def populate_indicators(data):
        pass

    def populate_buys(data):
        pass

    def populate_sells(data):
        pass

    def plot(data):
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


print(populate_backdata('ADABTC', '1d', '1000 days ago', recent=True))
print(populate_backdata('ADABTC', '1d', '1000 days ago'))