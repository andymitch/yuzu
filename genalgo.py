from random import uniform, choice

def genalgo(func, target, pop_count=1000, gen_count=10000, select_count=100, max_diff=.01, verbose=True):

    def populate():
        return [(uniform(0,10000),uniform(0,10000),uniform(0,10000)) for _ in range(pop_count)]

    def fitness(x,y,z):
        ans = func(x,y,z)
        if ans == target:
            return 99999
        else:
            return abs(1/(ans - target))

    def select(pop):
        return sorted([(fitness(p[0],p[1],p[2]),p) for p in pop], reverse=True)[:select_count]

    def crossover(pop):
        xpop = []
        for s in pop:
            xpop.append(s[1][0])
            xpop.append(s[1][1])
            xpop.append(s[1][2])
        return xpop

    def mutate(xpop):
        new_gen = []
        for _ in range(pop_count):
            e1 = choice(xpop) * uniform(1-max_diff,1+max_diff)
            e2 = choice(xpop) * uniform(1-max_diff,1+max_diff)
            e3 = choice(xpop) * uniform(1-max_diff,1+max_diff)
            new_gen.append((e1,e2,e3))
        return new_gen

    pop = populate()
    for i in range(gen_count):
        pop = select(pop)
        if verbose:
            print(f'== gen {i} best: {pop[0]}')
        if pop[0][0] > 9999:
            return pop[0]
        pop = mutate(crossover(pop))
    return pop[0]

#print(genalgo(lambda x,y,z: 6*x**3 + 9*y**2 + 90*z, 25, verbose=False))

def genalgo2(func, param_ranges, target, pop_count=1000, gen_count=10000, select_count=100, max_diff=.01, verbose=True):

    def populate():
        return [{k: uniform(v[0], v[1]) for k,v in param_ranges.items()} for _ in range(pop_count)]

    def fitness(config):
        ans = func(config)
        if ans == target:
            return 99999
        else:
            return abs(1/(ans - target))
    
    def select(pop):
        return sorted([(fitness(config), config) for config in pop], reverse=True)[:select_count]

    def crossover(pop):
        l = []
        for p in pop:
            l += [v for v in p[1].values()]
        return l

    def mutate(pop, elems):
        return [{k: choice(elems) * uniform(1-max_diff,1+max_diff) for k,v in pop[0][1].items()} for _ in range(pop_count)]

    pop = populate()
    for i in range(gen_count):
        pop = select(pop)
        if verbose:
            print(f'== gen {i} best: {pop[0]}')
        if pop[0][0] > 9999:
            return pop[0]
        pop = mutate(pop, crossover(pop))
    return pop[0]
'''
func = lambda config: 6*config['x']**3 + 9*config['y']**2 + 90*config['z']
param_ranges = {'x': [0,10000], 'y': [0,10000], 'z': [0,10000]}
target = 25
print(genalgo2(func, param_ranges, target, verbose=False))
'''

from utils import get_strategy, get_backdata, get_timeframe
from pandas import DataFrame
import math

data = get_backdata('BTCUSDT', '1m', get_timeframe('1m', 3000))
strategy = get_strategy('macdas_strat')
config_ranges = {
    'slow_len': [25,50],
    'fast_len': [5,24],
    'sig_len': [1,12],
    'rsi_len': [5,50],
    'rsi_lb': [0,50],
    'rsi_ub': [50,100]
}
def backtest(data: DataFrame) -> float:
    data = data.dropna(subset=['buy','sell'], how='all')
    data.loc[((data.buy.notnull()) & (data.buy.shift().isnull())), 'bought'] = data.buy
    data.loc[((data.sell.notnull()) & (data.sell.shift().isnull())), 'sold'] = data.sell
    data.dropna(subset=['bought','sold'], how='all', inplace=True)
    data.fillna(0, inplace=True)
    if data.empty:
        return -math.inf
    if data['sold'].iat[0] > 0:
        data.drop(data.head(1).index)
    if data['bought'].iat[-1] > 0:
        data.drop(data.tail(1).index)
    return sum(data.sold) - sum(data.bought)

def genalgo3(data, strategy, config_ranges, backtest, pop_count=1000, gen_count=1000, select_count=100, max_diff=.01, verbose=True):
    def populate():
        return [{k: uniform(v[0], v[1]) for k,v in config_ranges.items()} for _ in range(pop_count)]

    def fitness(config):
        temp = data.copy(deep=False)
        return backtest(strategy(temp, config))

    def select(pop):
        return sorted([(fitness(config), config) for config in pop], reverse=True)[:select_count]

    def crossover(pop):
        l = []
        for p in pop:
            l += [v for v in p[1].values()]
        return l

    def mutate(pop, elems):
        return [{k: choice(elems) * uniform(1-max_diff,1+max_diff) for k,v in pop[0][1].items()} for _ in range(pop_count)]

    pop = populate()
    for i in range(gen_count):
        pop = select(pop)
        if verbose:
            print(f'== gen {i} best: {pop[0]}')
        if pop[0][0] > 9999:
            return pop[0]
        pop = mutate(pop, crossover(pop))
    return pop[0]
genalgo3(data, strategy, config_ranges, backtest)