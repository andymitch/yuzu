from yuzu.strategies.utils.indicators import EMA
from yuzu.strategies.utils.utils import xup, xdn
from ta.momentum import RSIIndicator
from pandas import DataFrame


min_ticks = 44

def macdas_strat(
    data: DataFrame,
    config: dict
) -> DataFrame:
    data['buy_rsi'] = RSIIndicator(data.close, config['buy_rsi_len']).rsi()
    data['buy_fast'] = EMA(data.close, config['buy_fast_len'])
    data['buy_slow'] = EMA(data.close, config['buy_slow_len'])
    macd = data['buy_fast'] - data['buy_slow']
    signal = EMA(macd, config['buy_sig_len'])
    macdas = macd - signal
    sigdas = EMA(macdas, config['buy_sig_len'])
    data['buy_hist'] = macdas - sigdas

    data['sell_rsi'] = RSIIndicator(data.close, config['sell_rsi_len']).rsi()
    data['sell_fast'] = EMA(data.close, config['sell_fast_len'])
    data['sell_slow'] = EMA(data.close, config['sell_slow_len'])
    macd = data['sell_fast'] - data['sell_slow']
    signal = EMA(macd, config['sell_sig_len'])
    macdas = macd - signal
    sigdas = EMA(macdas, config['sell_sig_len'])
    data['sell_hist'] = macdas - sigdas

    data.loc[((data['buy_hist'] > 0) & (data['buy_rsi'] < config['rsi_lb'])), 'buy'] = data.close
    data.loc[((data['sell_hist'] < 0) & (data['sell_rsi'] > config['rsi_ub'])), 'sell'] = data.close
    return data

configs = {
    '1h': {'buy_slow_len': 30, 'buy_fast_len': 11, 'buy_sig_len': 8, 'buy_rsi_len': 6, 'sell_slow_len': 41, 'sell_fast_len': 5, 'sell_sig_len': 3, 'sell_rsi_len': 10, 'rsi_lb': 39.9, 'rsi_ub': 31.9},
    '1m': {'buy_slow_len': 37, 'buy_fast_len': 6, 'buy_sig_len': 3, 'buy_rsi_len': 7, 'sell_slow_len': 28, 'sell_fast_len': 11, 'sell_sig_len': 7, 'sell_rsi_len': 36, 'rsi_lb': 18.0, 'rsi_ub': 30.0, 'stop_limit_buy': 0.0029, 'stop_limit_sell': 0.0020, 'stop_limit_loss': 0.0081} 
}

config_range = {
    'buy_slow_len': [25,50],
    'buy_fast_len': [5,24],
    'buy_sig_len': [1,12],
    'buy_rsi_len': [5,50],
    'sell_slow_len': [25,50],
    'sell_fast_len': [5,24],
    'sell_sig_len': [1,12],
    'sell_rsi_len': [5,50],
    'rsi_lb': [0.0,70.0],
    'rsi_ub': [30.0,100.0]
}

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from yuzu.utils import add_common_plot_traces, trace_bar, trace_line

def plot(data, config, trade_mode=None):
    fig = make_subplots(rows=3 if trade_mode is None else 4, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]] * (3 if trade_mode is None else 4))

    fig = add_common_plot_traces(fig, data, trade_mode=trade_mode)

    fig.add_trace(trace_bar(data, 'buy_hist'), row=2 if trade_mode is None else 3, col=1, secondary_y=True)
    fig.add_trace(trace_line(data, 'buy_rsi', 'purple'), row=2 if trade_mode is None else 3, col=1)

    fig.add_trace(trace_bar(data, 'sell_hist'), row=3 if trade_mode is None else 4, col=1, secondary_y=True)
    fig.add_trace(trace_line(data, 'sell_rsi', 'purple'), row=3 if trade_mode is None else 4, col=1)

    fig.add_hrect(y0=0, y1=config['rsi_lb'], line_width=0, fillcolor='blue', x0=data.index[0], x1=data.index[-1], opacity=.5, row=2 if trade_mode is None else 3, col=1)
    fig.add_hrect(y0=config['rsi_ub'], y1=100, line_width=0, fillcolor='yellow', x0=data.index[0], x1=data.index[-1], opacity=.5, row=2 if trade_mode is None else 3, col=1)
    fig.add_hrect(y0=0, y1=config['rsi_lb'], line_width=0, fillcolor='blue', x0=data.index[0], x1=data.index[-1], opacity=.5, row=3 if trade_mode is None else 4, col=1)
    fig.add_hrect(y0=config['rsi_ub'], y1=100, line_width=0, fillcolor='yellow', x0=data.index[0], x1=data.index[-1], opacity=.5, row=3 if trade_mode is None else 4, col=1)

    return fig