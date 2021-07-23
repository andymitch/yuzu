from random import uniform, choice, shuffle
from pandas import DataFrame
from utils import get_strategy, get_backdata, get_timeframe, get_strategy_plot
import math
from tqdm import tqdm
from numpy.random import rand
from p_tqdm import p_map

def optimize(data, backtest, strategy_name, param_ranges, pop_count=100, gen_count=100, select_count=10, max_diff=.1, r_cross=.8, r_mut=.8, verbose=True):
    
    def populate():
        return [{k: int(uniform(v[0], v[1])) for k,v in param_ranges.items()} for _ in range(pop_count)]

    def fitness(config):
        return backtest(data, strategy_name, config)
    
    def select(pop):
        return sorted([(fitness(config), config) for config in tqdm(pop, desc='calculating fitness', leave=False)], key=lambda p: p[0], reverse=True)[:select_count]

    def crossover(parents):
        parents = [p[1] for p in parents]
        new_gen = [parents[0]]
        for _ in range(pop_count-1):
            if rand() > r_cross:
                new_gen.append(choice(parents))
            else:
                child = choice(parents)
                keys = list(parents[0].keys())
                shuffle(keys)
                left_keys = keys[:int(len(keys)/2)]
                other_parent = choice(parents)
                for key in left_keys:
                    child[key] = other_parent[key]
                new_gen.append(child)
        return new_gen

    def mutate(pop):
        def mut_val(k,v):
            new_val = -1
            while new_val < param_ranges[k][0] or new_val > param_ranges[k][1]:
                new_val = int(v * uniform(1-max_diff,1+max_diff))
            return new_val
        return [{k: mut_val(k,v) for k,v in config.items()} for config in pop]

    pop = populate()
    for i in range(gen_count):
        fitest = select(pop)
        if verbose:
            print(f'== gen {i} ==')
            for f in fitest:
                print(f)
            print('\n')
        pop = mutate(crossover(fitest))
    return pop[0]

'''
- shallow copy df
- drop where buy and sell is None
- drop where buy not None and buy.shift not None
- drop where sell not None and sell.shift not None
- drop first if sell
- drop last if buy
This should leave a list of complete trades (ie. [buy,sell,buy,sell,…])
- score = sum(df.sell) - sum(df.buy)
'''

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

from backtest import backtest as og_backtest

def brute_optimize(pair, interval, strategy, configs, file_name=None):
    
    results = DataFrame(p_map(lambda config: og_backtest({"pair": pair, "interval": interval, "strategy": strategy, "strategy_config": config, "stop_loss": config.get('stop_loss', .35)}, verbose=False, update=False, plot=False)[1], configs)).drop(['best_trade_buy', 'best_trade_sell', 'best_trade_win', 'worst_trade_buy', 'worst_trade_sell', 'worst_trade_win'], axis=1)
    try:
        results = results.drop(['best_trade', 'worst_trade'])
    except: pass
    results.to_csv(f'./results/{strategy}-{pair}-{interval}')
    return results.sort_values('score', ascending=False)










from numpy import isnan
from random import choice, randint

def genalgo_backtest(data, stop_loss, trading_fee=0.001):
    starting_amount = 100.0
    data["trade_profit"] = [0] * len(data)
    data["hodl_profit"] = [0] * len(data)
    data["stop_loss"] = [None] * len(data)
    wallet = {"base": starting_amount / 2, "asset": starting_amount / (data.loc[data.index[0], "close"] * 2)}
    hodl_wallet = wallet.copy()
    data["bought"] = [None] * len(data)
    data["sold"] = [None] * len(data)
    data["stop_lossed"] = [None] * len(data)
    stop_loss_value = None
    tally = []
    for i, row in data.iterrows():
        if not isnan(row["buy"]) and wallet["base"] > 0:
            tally.append({"buy": data.loc[i, "close"], 'win': None})
            data.loc[i, "bought"] = data.loc[i, "close"]
            fee = wallet["base"] * trading_fee
            wallet["asset"] += (wallet["base"] - fee) / row["buy"]
            wallet["base"] = 0.0
            stop_loss_value = row["buy"] * (1 - stop_loss)
        elif not stop_loss_value is None and stop_loss_value > row["low"]:
            tally[-1]["sell"] = stop_loss_value
            tally[-1]["win"] = bool(False)
            data.loc[i, "stop_lossed"] = stop_loss_value
            fee = wallet["asset"] * trading_fee
            wallet["base"] += (wallet["asset"] - fee) * stop_loss_value
            wallet["asset"] = 0.0
            data.loc[i, "stop_loss"] = stop_loss_value
            stop_loss_value = None
        elif not isnan(row["sell"]) and wallet["asset"] > 0:
            if wallet["base"] == 0:
                tally[-1]["sell"] = data.loc[i, "close"]
                tally[-1]["win"] = bool(tally[-1]["sell"] > tally[-1]["buy"])
            else:
                tally.append({"sell": data.loc[i, "close"], "win": None})
            data.loc[i, "sold"] = data.loc[i, "close"]
            fee = wallet["asset"] * trading_fee
            wallet["base"] += (wallet["asset"] - fee) * row["sell"]
            wallet["asset"] = 0.0
            stop_loss_value = None

        if not isnan(row["close"]):
            data.loc[i, "trade_profit"] = (wallet["base"] + (wallet["asset"] * row["close"])) - starting_amount
            data.loc[i, "hodl_profit"] = (hodl_wallet["base"] + (hodl_wallet["asset"] * row["close"])) - starting_amount

    data["profit_diff_change"] = (data["trade_profit"] - data["hodl_profit"]) - (data["trade_profit"].shift() - data["hodl_profit"].shift())
    score = data.trade_profit.iat[-1]#data.profit_diff_change.sum()
    win_rate = None
    try:
        win_rate = len(list(filter(lambda t: t['win'], tally))) / len(list(filter(lambda t: not t['win'] is None, tally)))
    except: pass
    for t in tally:
        t['diff'] = t['sell'] - t['buy'] if 'sell' in t.keys() and 'buy' in t.keys() else None
    sorted_tally = list(sorted(list(filter(lambda t: not t['diff'] is None, tally)), key=lambda t: t['diff']))
    best_trade, worst_trade = [sorted_tally[-1], sorted_tally[0]] if len(sorted_tally) > 0 else [None, None]
    results = {
        'score': score,
        'win_rate': win_rate,
        'trade_freq': f'{len(tally)}/{len(data)}',
        'best_trade': best_trade,
        'worst_trade': worst_trade
    }
    return data, results

def genalg_optimize(pair, interval, strategy, config_bounds, pop_size, n_iter, max_mut_diff):
    minutes_in_a_month = 43830
    data = get_backdata(pair, interval, get_timeframe(interval, minutes_in_a_month))

    def populate(size):
        get_val = lambda k,v: uniform(v[0], v[1]) if k == 'stop_loss' else int(uniform(v[0], v[1]))
        return [{'fitness': None, 'config': {k: get_val(k,v) for k,v in config_bounds.items()}} for _ in tqdm(range(size), desc='populating', leave=False)]

    def fit(p):
        data_df = strategy(data.copy(deep=False), p['config'])
        p['fitness'] = genalgo_backtest(data_df, p['config']['stop_loss'])[1]
        return p

    def select(pop):
        pop = list(p_map(fit, pop, desc='fitting', leave=False))
        pop = sorted(pop, reverse=True, key=lambda p: p['fitness']['score'])
        return pop[:int(len(pop)/3)]

    def crossover(selected):
        return [{'fitness': None, 'config': {k: choice(selected)['config'][k] for k in selected[0]['config'].keys()}} for _ in tqdm(range(len(selected)), desc='mixing', leave=False)]

    def mutate(subpop):
        def mut_val(k,v):
            new_val = -1
            while new_val < config_bounds[k][0] or new_val > config_bounds[k][1]:
                new_val = v * uniform(1-max_mut_diff,1+max_mut_diff)
                if not k in ['stop_loss', 'rsi_lb', 'rsi_ub']:
                    new_val = int(new_val)
            return new_val
        return [{'fitness': None, 'config': {k: mut_val(k,v) for k,v in p['config'].items()}} for p in tqdm(subpop, desc='mutating', leave=False)]

    def prettyprint(p):
        print(p['fitness']['score'], p['config'])

    best_counter, curr_best = 0, None
    pop = populate(pop_size)
    for i in range(n_iter):
        print(f'\n== GEN {i+1}/{n_iter} ==')
        selected = select(pop)
        if selected[0]['fitness']['score'] == curr_best:
            best_counter += 1
        else: 
            curr_best = selected[0]['fitness']['score']
            best_counter = 0
        for p in selected[:10]:
            prettyprint(p)
        if i == n_iter-1 or best_counter >= 5:
            return selected
        crossed = crossover(selected)
        mutated = mutate(selected)
        fill_count = pop_size - 1 - len(mutated) - len(crossed)
        pop = [selected[0], *mutated, *crossed, *populate(fill_count)]

def main(opt_type):
    if opt_type == 'brute':
        configs = [{"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': l, 'rsi_lb': lb, 'rsi_ub': ub, 'stop_loss': sl} for l in [4,8,14,24] for lb in [25,30,35,40] for ub in [60,65,70,75] for sl in [.05,.1,.15,.2,.3,.35]]
        print(brute_optimize('BTCUSDT', '1m', 'macdas_strat', configs).head(10))
    elif opt_type == 'genalg':
        pair, interval = 'BTCUSDT', '1m'
        strategy = get_strategy('macdas_strat')
        config_bounds = {
            'slow_len': [25,50],
            'fast_len': [5,24],
            'sig_len': [1,12],
            'rsi_len': [5,50],
            'rsi_lb': [0,50],
            'rsi_ub': [50,100],
            'stop_loss': [0,.5]
        }
        pop_size, n_iter, max_mut_diff = 1000, 1000, .2
        print(genalg_optimize(pair, interval, strategy, config_bounds, pop_size, n_iter, max_mut_diff))
    elif opt_type == 'compare':
        data = get_backdata('BTCUSDT', '1m', '1 month ago', update=False)
        strategy = get_strategy('macdas_strat')
        '''
        default = strategy(data.copy(deep=False), {"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': 8, 'rsi_lb': 35, 'rsi_ub': 65})
        default, _ = genalgo_backtest(data=default, stop_loss=.35)

        brute = strategy(data.copy(deep=False), {'slow_len': 26, 'fast_len': 12, 'sig_len': 9, 'rsi_len': 24, 'rsi_lb': 35, 'rsi_ub': 65})
        brute, _ = genalgo_backtest(data=brute, stop_loss=.05)
        '''
        genalgo = strategy(data, {'slow_len': 45, 'fast_len': 8, 'sig_len': 7, 'rsi_len': 20, 'rsi_lb': 34.23, 'rsi_ub': 64.42})
        genalgo, _ = genalgo_backtest(data=genalgo, stop_loss=0.26)
        get_strategy_plot('macdas_strat')(genalgo, 'BTCUSDT', '1m').show()
        '''
        from plot import plot_compare
        index = default.index
        profit_lines = [default.hodl_profit, default.trade_profit, brute.trade_profit, genalgo.trade_profit]
        plot_compare(profit_lines, index)
        '''

if __name__ == '__main__':
    #main('brute')
    main('genalg')
    #main('compare')