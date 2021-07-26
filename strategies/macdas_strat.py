from strategies.utils.indicators import EMA
from strategies.utils.utils import xup, xdn
from ta.momentum import RSIIndicator
from pandas import DataFrame
from plot import Plot


def macdas_strat(
    data: DataFrame,
    config: object = {"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': 8, 'rsi_lb': 35, 'rsi_ub': 65}
) -> DataFrame:
    data['rsi'] = RSIIndicator(data.close, config['rsi_len']).rsi()
    data['fast'] = EMA(data.close, config['fast_len'])
    data['slow'] = EMA(data.close, config['slow_len'])
    macd = data.fast - data.slow
    signal = EMA(macd, config['sig_len'])
    macdas = macd - signal
    sigdas = EMA(macdas, config['sig_len'])
    data['hist'] = macdas - sigdas
    data.loc[((data['hist']>0) & (data.rsi < config['rsi_lb'])), 'buy'] = data.close
    data.loc[((data['hist']<0) & (data.rsi > config['rsi_ub'])), 'sell'] = data.close
    return data

def plot(data, pair, interval):
    plot = Plot(data, f"macdas_strat ({pair} {interval})")
    plot.add_trace('hist', 1, 'bar')
    plot.add_trace('rsi', 1, 'line', 'purple', True)
    return plot

config_bounds = {
    'slow_len': [25,50],
    'fast_len': [5,24],
    'sig_len': [1,12],
    'rsi_len': [5,50],
    'rsi_lb': [0,50],
    'rsi_ub': [50,100]
}