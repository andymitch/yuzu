from random import uniform, choice, shuffle
from pandas import DataFrame, notna
import math
from tqdm import tqdm
from numpy.random import rand
from p_tqdm import p_map
from numpy import isnan
from random import choice, randint
from functools import partial
import sys
import datetime
from pytz import reference
from itertools import groupby

def win_rate(trades):
    return len(list(filter(lambda t: t['win'], trades))) / len(trades) if len(trades) > 0 else 0

def consectutive_win_rate(trades):
    consecs = [(n,len(list(c))) for n,c in groupby(trades,lambda t: t['win'])]
    most_consec_wins = 0
    try:
        most_consec_wins = max([t[1] for t in list(filter(lambda t: t[0], consecs))])
    except:pass
    most_consec_loses = 0
    try:
        most_consec_loses = max([t[1] for t in list(filter(lambda t: not t[0], consecs))])
    except:pass
    return most_consec_wins / (most_consec_wins + most_consec_loses)

def avg_profit(trades):
    return sum([t['close']-t['open'] for t in trades]) / len(trades) if len(trades) > 0 else 0

def avg_drawdown(trades):
    wins = list(filter(lambda t: t['win'], trades))
    drops = [(t['open']-t['low'])/t['open'] for t in trades]
    return sum(drops)/len(drops)

def score(trades):
    try:
        if 'i' in trades[-1].keys(): trades.pop()
        return win_rate(trades) + consectutive_win_rate(trades) + avg_profit(trades) - avg_drawdown(trades)
    except: return 0

def quick_backtest(data: DataFrame, trading_fee=0.001) -> float:
    final_price = data.close.iat[-1]
    sub_data = data[['buy','sell']].copy(deep=False)
    sub_data = sub_data.dropna(subset=['buy','sell'], how='all')
    if not sub_data.empty:
        if not sub_data.sell.iat[0] is None:
            sub_data.loc[sub_data.index[0], "sell"] = None
        if not sub_data.buy.iat[-1] is None:
            sub_data.loc[sub_data.index[-1], "buy"] = None
    trades = []
    open_trade = False
    for index, tick in sub_data.iterrows():
        if not open_trade and not isnan(tick.buy):
            trades.append({'open': tick.buy, 'i': index})
            open_trade = True
        elif open_trade and not isnan(tick.sell):
            curr_trade = trades[-1]
            trades[-1] = {
                'open': curr_trade['open'],
                'close': tick.sell,
                'low': min(data.loc[curr_trade['i']:index, 'low']),
                'win': tick.sell > curr_trade['open']
            }
            open_trade = False
    return score(trades)

def populate(size, config_range):
    get_val = lambda k,v: uniform(v[0], v[1]) if isinstance(v[0], float) else int(uniform(v[0], v[1]))
    return [{'fitness': None, 'config': {k: get_val(k,v) for k,v in config_range.items()}} for _ in tqdm(range(size), desc='populating', leave=False)]

def fit(samples, strategy, p):
    p['fitness'] = sum(quick_backtest(strategy(s, p['config'])) for s in samples)
    return p

def select(samples, pop, i, n_iter, strategy):
    pop = list(p_map(partial(fit, samples, strategy), pop, desc='   fitting', leave=False))
    pop = sorted(pop, reverse=True, key=lambda p: p['fitness'])
    return pop[:int(len(pop)/3)]

def crossover(selected):
    return [{'fitness': None, 'config': {k: choice(selected)['config'][k] for k in selected[0]['config'].keys()}} for _ in tqdm(range(len(selected)), desc='mixing', leave=False)]

def mutate(subpop, config_range, max_mut_diff):
    def mut_val(k,v):
        new_val = -1
        while new_val < config_range[k][0] or new_val > config_range[k][1]:
            new_val = v * uniform(1-max_mut_diff,1+max_mut_diff)
            if not k in ['rsi_lb', 'rsi_ub']:
                new_val = int(new_val)
        return new_val
    return [{'fitness': None, 'config': {k: mut_val(k,v) for k,v in p['config'].items()}} for p in tqdm(subpop, desc='mutating', leave=False)]

def optimize(strategy, config_range, data, pop_size=1000, n_iter=100, max_mut_diff=.2):
    ticks = len(data)

    best_rep, curr_best, max_rep = 0, [None,None,None,None,None], 5
    pop = populate(pop_size, config_range)
    '''
    samples = []
    for _ in tqdm(range(10), desc='sampling data', leave=False):
        rt = randint(int(ticks/100), int(ticks/10))
        ri = randint(0, ticks-rt)
        samples.append(data.iloc[ri:ri+rt].copy(deep=False))
    '''
    for i in tqdm(range(n_iter), desc='Generation', leave=False):
        selected = select([data], pop, i, n_iter, strategy)
        crossed = crossover(selected)
        mutated = mutate(selected, config_range, max_mut_diff)
        fill_count = pop_size - 5 - len(mutated) - len(crossed)
        pop = [*selected[:5], *mutated, *crossed, *populate(fill_count, config_range)]
    return pop[0]['config']
