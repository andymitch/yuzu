from strategies.utils.indicators import EMA
from strategies.utils.utils import xup, xdn
from ta.momentum import RSIIndicator
from pandas import DataFrame
from plot import Plot


best_config = {
    '1m': {'slow_len': 41, 'fast_len': 12, 'sig_len': 9, 'rsi_len':  5, 'rsi_lb': 49.6, 'rsi_ub': 76.6},
    '15m':{'slow_len': 46, 'fast_len': 17, 'sig_len': 8, 'rsi_len':  5, 'rsi_lb': 36.2, 'rsi_ub': 85.0},
    '1h': {'slow_len': 44, 'fast_len':  5, 'sig_len': 2, 'rsi_len': 34, 'rsi_lb': 35.0, 'rsi_ub': 96.3},
    '1d': {'slow_len': 38, 'fast_len':  6, 'sig_len': 2, 'rsi_len': 33, 'rsi_lb': 33.3, 'rsi_ub': 83.0}
}

# {'slow_len': 34, 'fast_len': 23, 'sig_len': 11, 'rsi_len': 6, 'rsi_lb': 20.237913834834835, 'rsi_ub': 70.87008898625974}

min_ticks = 44

def macdas_strat(
    data: DataFrame,
    config: object = best_config
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

def plot(data, pair, interval, show_profit=True, dark_mode: bool = True):
    plot = Plot(data, interval, show_profit, dark_mode)
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