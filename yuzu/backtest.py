from pandas import DataFrame
from numpy import isnan
from .plot import plot as _plot


def buy(data, i, row, stop_buy, stop_limit_buy, stop_loss, stop_limit_loss, wallet):
    if stop_buy and stop_buy < row['high']:
        wallet['left'] = wallet['right'] * (1-wallet['fee']) / stop_buy
        wallet['right'] = 0.0
        data.at[i, 'bought'] = stop_buy
        stop_loss = stop_buy - (stop_buy * stop_limit_loss)
        stop_buy = None
        return data, stop_buy, stop_loss, True, wallet
    if not isnan(row['buy']) and (stop_buy is None or row['close'] + (row['close'] * stop_limit_buy) < stop_buy):
        stop_buy = row['close'] + (row['close'] * stop_limit_buy)
    return data, stop_buy, stop_loss, False, wallet

def sell(data, i, row, stop_sell, stop_limit_sell, stop_loss, wallet):
    if stop_sell and stop_sell > row['low']:
        wallet['right'] = wallet['left'] * (1-wallet['fee']) * stop_sell
        wallet['left'] = 0.0
        data.at[i, 'sold'] = stop_sell
        stop_sell = None
        stop_loss = None
        return data, stop_sell, stop_loss, False, wallet
    elif stop_loss and stop_loss > row['low']:
        wallet['right'] = wallet['left'] * (1-wallet['fee']) * stop_loss
        wallet['left'] = 0.0
        data.at[i, 'stop_lossed'] = stop_loss
        stop_sell = None
        stop_loss = None
        return data, stop_sell, stop_loss, False, wallet
    if not isnan(row['sell']) and (stop_sell is None or row['close'] + (row['close'] * stop_limit_sell) > stop_sell):
        stop_sell = row['close'] - (row['close'] * stop_limit_sell)
    return data, stop_sell, stop_loss, True, wallet

def backtest(data: DataFrame, config, fee: float = .001, plot: bool = False):
    stop_limit_buy: float = config['stop_limit_buy']
    stop_limit_sell: float = config['stop_limit_sell']
    stop_limit_loss: float = config['stop_limit_loss']
    wallet = {'left': 0.0, 'right': 100.0, 'fee': fee}
    stop_buy, stop_sell, stop_loss = None, None, None
    data[['bought', 'sold', 'stop_lossed', 'balance']] = [None, None, None, None]
    open_trade = False

    for i, row in data.iterrows():
        if open_trade:
            data, stop_sell, stop_loss, open_trade, wallet = sell(data, i, row, stop_sell, stop_limit_sell, stop_loss, wallet)
        else:
            data, stop_buy, stop_loss, open_trade, wallet = buy(data, i, row, stop_buy, stop_limit_buy, stop_loss, stop_limit_loss, wallet)
        data.at[i, 'balance'] = wallet['right'] + (wallet['left'] * row['close'])

    data['balance'] -= 100.0

    if plot:
        try: _plot(data)
        except: pass

    return data['balance'].iat[-1]