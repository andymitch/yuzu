from random import uniform, choice
from tqdm import tqdm
from functools import partial
from p_tqdm import p_map
from .backtest import backtest
from .utils.getters import get_strategy
from numpy import isnan, nan
import warnings
warnings.simplefilter(action='ignore', category=Warning)


def populate(size, config_range):
    get_val = lambda k,v: uniform(v[0], v[1]) if isinstance(v[0], float) else int(uniform(v[0], v[1]))
    return [{'fitness': None, 'config': {k: get_val(k,v) for k,v in config_range.items()}} for _ in range(size)]

def get(r, d):
    s = d.loc[r[-2]:r[-1],]
    low = s.loc[s['low']==min(s['low'])]['low'].iat[0]
    high = s.loc[s['high']==max(s['high'])]['high'].iat[0]
    return [low, high]

def _truncate(d):
    d['time'] = d.index
    d = d.reset_index()
    t = d[((~isnan(d['buy']))|(~isnan(d['sell'])))]
    t['ix'] = t.index
    t['iy'] = t['ix'].shift(-1)
    if len(t) > 0: t.at[t.index[-1], 'iy'] = d.index[-1]
    t['iy'] = t['iy'].apply(lambda i: int(i))
    t[['low','high']] = [get(r, d) for r in t.itertuples()]
    return t.set_index('time').drop(['ix','iy'], axis=1)

def fit(p, data, strategy, truncate):
    d = strategy(data.copy(deep=False), p['config'])
    t = _truncate(d) if truncate else d
    p['fitness'] = backtest(t, p['config'])
    return p

def select(data, pop, i, n_iter, strategy, truncate):
    pop = list(p_map(partial(fit, data=data, strategy_name=strategy, truncate=truncate), pop, desc='   fitting', leave=False))
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

def optimize(data, strategy, config_range, pop_size=1000, n_iter=100, max_mut_diff=.2, max_reps=-1, truncate: bool = False):
    min_ticks_options = config_range.pop('min_ticks')
    ticks = len(data)
    reps, best = 0, None
    pop = populate(pop_size, config_range)
    for i in tqdm(range(n_iter), desc='Generation', leave=False):
        selected = select(data, pop, i, n_iter, strategy, truncate)
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
    result = pop[0]['config']
    result['min_ticks'] = max([result[o] for o in min_ticks_options])
    return result