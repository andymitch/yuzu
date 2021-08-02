from random import uniform, choice, shuffle
from pandas import DataFrame, notna
from utils import get_strategy, get_backdata, get_timeframe, get_strategy_plot, get_strategy_config_bounds
import math
from tqdm import tqdm
from numpy.random import rand
from p_tqdm import p_map
from backtest import backtest as og_backtest
from numpy import isnan
from random import choice, randint
import sys
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
from pytz import reference

def brute_optimize(pair, interval, strategy, configs, file_name=None):
    results = DataFrame(p_map(lambda config: og_backtest({"pair": pair, "interval": interval, "strategy": strategy, "strategy_config": config, "stop_loss": config.get('stop_loss', .35)}, verbose=False, update=False, plot=False)[1], configs)).drop(['best_trade_buy', 'best_trade_sell', 'best_trade_win', 'worst_trade_buy', 'worst_trade_sell', 'worst_trade_win'], axis=1)
    try:
        results = results.drop(['best_trade', 'worst_trade'])
    except: pass
    results.to_csv(f'./results/{strategy}-{pair}-{interval}')
    return results.sort_values('score', ascending=False)


def quick_backtest(data: DataFrame, trading_fee=0.001) -> float:
    final_price = data.close.iat[-1]
    data = data[['buy','sell']]
    data = data.dropna(subset=['buy','sell'], how='all').copy()
    if not data.empty:
        if not data.sell.iat[0] is None:
            data.loc[data.index[0], "sell"] = None
        if not data.buy.iat[-1] is None:
            data.loc[data.index[-1], "buy"] = None
    base, asset = 100.0, 0.0
    for index, tick in data.iterrows():
        if base > 0 and not isnan(tick.buy):
            asset += base * (1-trading_fee) / tick.buy
            base = 0.0
        elif asset > 0 and not isnan(tick.sell):
            base += asset * (1-trading_fee) * tick.sell
            asset = 0.0
    if asset > 0:
        base += asset * final_price
    return (base - 100.0) / 100.0

def optimize(strategy_name, pair, interval, pop_size=1000, n_iter=100, max_mut_diff=.2, ticks=40000, save=False, plot=False):

    def rand_end(interval):
        value, base = int(interval[:-1]), interval[-1]
        if base == 'm':
            value *= 60 * 10000
        elif base == 'h':
            value *= 3600 * 10000
        elif base == 'd':
            value *= 86400 * 10000
        curr_time: datetime = datetime.datetime.now(tz=reference.LocalTimezone())
        epoch: long = int(curr_time.timestamp())
        return (epoch - randint(0, value)) * 1000

    data = get_backdata(pair, interval, ticks, rand_end(interval))#[get_backdata(pair, interval, ticks, rand_end(interval)) for _ in tqdm(range(100), desc='collecting data sets')]
    print(len(data))
    strategy = get_strategy(strategy_name)
    config_bounds = get_strategy_config_bounds(strategy_name)

    # TODO: since this is collected off various data sets, there isn't just one data set to plot or record a single fitness score over
    def _save(result):
        file = open('optimize_results.csv', 'a')
        file.write(f"{datetime.datetime.now()},{strategy_name},{pair},{interval},{result['fitness']},\"{result['config']}\"\n")
        file.close()
    # TODO: read above ^
    def _plot(result, data):
        data = strategy(data, result['config'])
        data = og_backtest(data)[0]
        get_strategy_plot(strategy_name)(data, pair, interval).show()
        print(result)

    def populate(size):
        get_val = lambda k,v: uniform(v[0], v[1]) if k in ['rsi_lb', 'rsi_ub'] else int(uniform(v[0], v[1]))
        return [{'fitness': None, 'config': {k: get_val(k,v) for k,v in config_bounds.items()}} for _ in tqdm(range(size), desc='populating', leave=False)]

    def fit(p):
        p['fitness'] = quick_backtest(strategy(data.copy(deep=False), p['config']))
        return p

    def select(pop):
        pop = list(p_map(fit, pop, desc='fitting', leave=False))
        pop = sorted(pop, reverse=True, key=lambda p: p['fitness'])
        return pop[:int(len(pop)/3)]

    def crossover(selected):
        return [{'fitness': None, 'config': {k: choice(selected)['config'][k] for k in selected[0]['config'].keys()}} for _ in tqdm(range(len(selected)), desc='mixing', leave=False)]

    def mutate(subpop):
        def mut_val(k,v):
            new_val = -1
            while new_val < config_bounds[k][0] or new_val > config_bounds[k][1]:
                new_val = v * uniform(1-max_mut_diff,1+max_mut_diff)
                if not k in ['rsi_lb', 'rsi_ub']: # TODO: make universal
                    new_val = int(new_val)
            return new_val
        return [{'fitness': None, 'config': {k: mut_val(k,v) for k,v in p['config'].items()}} for p in tqdm(subpop, desc='mutating', leave=False)]

    def prettyprint(p):
        print(f"{p['fitness']}\t{p['config']}")

    best_rep, curr_best, max_rep = 0, [None,None,None,None,None], 5
    pop = populate(pop_size)
    for i in range(n_iter):
        print(f'\n== GEN {i+1}/{n_iter} == ({best_rep}/{max_rep} repeated)')
        selected = select(pop)
        change = False
        for i in range(5):
            if selected[i]['fitness'] != curr_best[i]:
                for i in range(5):
                    curr_best[i] = selected[i]['fitness']
                best_rep = 0
        if not change:
            best_rep += 1
        for p in selected[:10]:
            prettyprint(p)
        if i == n_iter-1 or best_rep > max_rep:
            if save: _save(selected[0])
            if plot: _plot(selected[0], data)
            return selected[0]
        crossed = crossover(selected)
        mutated = mutate(selected)
        fill_count = pop_size - 5 - len(mutated) - len(crossed)
        pop = [*selected[:5], *mutated, *crossed, *populate(fill_count)]
        # GET NEW DATA EVERY GEN: data = [get_backdata(pair, interval, ticks, rand_end(interval)) for _ in range(100)]


def optimize_stop_loss(data, stop_loss_range=[0,.5], pop_size=100, n_iter=100, max_mut_diff=.2):

    def rand_end(interval):
        value, base = int(interval[:-1]), interval[-1]
        if base == 'm':
            value *= 60 * 10000
        elif base == 'h':
            value *= 3600 * 10000
        elif base == 'd':
            value *= 86400 * 10000
        curr_time: datetime = datetime.datetime.now(tz=reference.LocalTimezone())
        epoch: long = int(curr_time.timestamp())
        return (epoch - randint(0, value)) * 1000

    def populate(size):
        return [{'stop_loss': uniform(stop_loss_range[0],stop_loss_range[1]), 'fitness': None} for _ in range(pop_size)]

    def fit(p):
        return {'stop_loss': p['stop_loss'], 'fitness': og_backtest(data, p['stop_loss'])[1]['score']}

    def select(pop):
        pop = list(p_map(fit, pop, desc='fitting', leave=False))
        pop = sorted(pop, reverse=True, key=lambda p: p['fitness'])
        return pop[:int(len(pop)/3)]

    def mutate(pop):
        def mut_val(v):
            new_val = -1
            while new_val < stop_loss_range[0] or new_val > stop_loss_range[1]:
                new_val = v * uniform(1-max_mut_diff,1+max_mut_diff)
            return new_val
        return [{'fitness': None, 'stop_loss': mut_val(choice(pop)['stop_loss'])} for _ in tqdm(range(len(pop)), desc='mutating', leave=False)]

    pop = populate(pop_size)
    for i in range(n_iter):
        print(f'\n== GEN {i+1}/{n_iter} ==')
        selected = select(pop)
        mutated = mutate(selected)
        fill_count = pop_size - 5 - len(mutated)
        pop = [*selected[:5], *mutated, *populate(fill_count)]
        for p in pop[:5]: print('fitness:', p['fitness'], 'stop_loss:', p['stop_loss'])
    return pop[0]

if __name__ == '__main__':
    # BRUTE FORCE
    #configs = [{"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': l, 'rsi_lb': lb, 'rsi_ub': ub, 'stop_loss': sl} for l in [4,8,14,24] for lb in [25,30,35,40] for ub in [60,65,70,75] for sl in [.05,.1,.15,.2,.3,.35]]
    #print(brute_optimize('BTCUSDT', '1m', 'macdas_strat', configs).head(10))
    
    # GENETIC ALGORITHM
    strategy_name = 'macdas_strat'
    pair, interval = 'BTCUSDT', '1m'
    results = optimize(strategy_name, pair, interval)

    # OPTIMIZE STOP LOSS
    #pair, interval = 'BTCUSDT', '1m'
    #from strategies.macdas_strat import *
    #print(optimize_stop_loss(macdas_strat(get_backdata(pair, interval), best_config['1m'])))
