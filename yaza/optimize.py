from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas import DataFrame
from numpy import isnan


########################################## BACKTEST

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

    # not stop_buy is None or 

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
        fig = make_subplots(rows=2, cols=1)
        fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.buy, x=data.index, name="buy", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10, opacity=.5)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.sell, x=data.index, name="sell", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10, opacity=.5)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.bought, x=data.index, name="bought", mode="markers", marker=dict(color="cyan", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.sold, x=data.index, name="sold", mode="markers", marker=dict(color="yellow", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.stop_lossed, x=data.index, name="stop lossed", mode="markers", marker=dict(color="magenta", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.balance, x=data.index, mode="lines", line_shape="spline", name='balance', line=dict(color='green')), row=2, col=1)
        fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
        fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
        fig.update_traces(xaxis="x")
        fig.show()

    return data['balance'].iat[-1]


########################################## OPTIMIZE

from random import uniform, choice
from tqdm import tqdm
from functools import partial
from p_tqdm import p_map

def populate(size, config_range):
    get_val = lambda k,v: uniform(v[0], v[1]) if isinstance(v[0], float) else int(uniform(v[0], v[1]))
    return [{'fitness': None, 'config': {k: get_val(k,v) for k,v in config_range.items()}} for _ in range(size)]

def fit(p, data, strategy):
    p['fitness'] = backtest(strategy(data, p['config']), p['config']['stop_limit_buy'], p['config']['stop_limit_sell'], p['config']['stop_limit_loss'])
    return p

def select(data, pop, i, n_iter, strategy):
    pop = list(p_map(partial(fit, data=data, strategy=strategy), pop, desc='   fitting', leave=False))
    pop = sorted(pop, reverse=True, key=lambda p: p['fitness'])
    return pop[:int(len(pop)/3)]

def crossover(selected):
    return [{'fitness': None, 'config': {k: choice(selected)['config'][k] for k in selected[0]['config'].keys()}} for _ in range(len(selected))]

def mutate(subpop, config_range, max_mut_diff):
    def mut_val(k,v):
        new_val = -1
        while new_val < config_range[k][0] or new_val > config_range[k][1]:
            new_val = v * uniform(1-max_mut_diff,1+max_mut_diff)
            if not isinstance(config_range[k][0], float):
                new_val = int(new_val)
        return new_val
    return [{'fitness': None, 'config': {k: mut_val(k,v) for k,v in p['config'].items()}} for p in subpop]

def optimize(data, strategy, config_range, pop_size=1000, n_iter=200, max_mut_diff=.2, max_reps=-1):
    ticks = len(data)
    reps, best = 0, None
    pop = populate(pop_size, config_range)
    for i in tqdm(range(n_iter), desc='Generation', leave=False):
        selected = select(data, pop, i, n_iter, strategy)
        if max_reps > 0:
            if selected[0] == best:
                reps += 1
            else:
                best = selected[0]
                reps = 0
            if reps > max_reps:
                return selected[0]['config']
        crossed = crossover(selected)
        mutated = mutate(selected, config_range, max_mut_diff)
        fill_count = pop_size - 5 - len(mutated) - len(crossed)
        pop = [*selected[:5], *mutated, *crossed, *populate(fill_count, config_range)]
    return pop[0]['config']


########################################## DRIVER

if __name__ == '__main__':
    from yuzu.exchanges.BinanceUS import get_backdata
    from yuzu.strategies.macdas_strat import macdas_strat

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
        'rsi_ub': [30.0,100.0],
        'stop_limit_buy': [0.001,0.01],
        'stop_limit_sell': [0.001,0.01],
        'stop_limit_loss': [0.001,0.01]
    }

    data = get_backdata('BTCUSD', '1m', 5000)
    config = optimize(data, macdas_strat, config_range)
    print(config)
    backtest(macdas_strat(data, config), config['stop_limit_buy'], config['stop_limit_sell'], config['stop_limit_loss'], plot=True)


# TODO: update yuzu.py
'''
Update yuzu.py to include trading specific configs when optimizing
Be sure that yuzu.py works with new optimize.py
Create json configs tree for all user information and strategy configs
'''