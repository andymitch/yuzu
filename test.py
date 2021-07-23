def get_bought_sold():
    from pandas import DataFrame
    from numpy import nan

    raw = {
        'a': [   1,    2,    3,  4,    5,   6],
        'b': [None,    0, None,  4,    5, None],
        'c': [None, None,   23, 34, None,   45]
    } # should be a = [2, 3, 4, 6] => 23 - 0 + 45 - 4 = 64

    data = DataFrame(raw)
    data = data.dropna(subset=['b','c'], how='all')
    print(data)
    data.loc[((data.b.notnull()) & (data.b.shift().isnull())), 'new_b'] = data.b
    data.loc[((data.c.notnull()) & (data.c.shift().isnull())), 'new_c'] = data.c
    print(data)
    data.dropna(subset=['new_b','new_c'], how='all', inplace=True)
    data.fillna(0, inplace=True)
    print(sum(data.new_c) - sum(data.new_b))

def compare_backtest():
    import math
    from backtest import backtest
    from utils import get_backdata, get_strategy, get_timeframe
    def backtest2(config) -> float:
        data = get_backdata(config["pair"], config["interval"], get_timeframe(config["interval"], 3000), update=False)
        strat_config = config.get("strategy_config", None)
        if strat_config is None:
            data = get_strategy(config["strategy"])(data)
        else:
            data = get_strategy(config["strategy"])(data, config.get("strategy_config", None))
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

    config = {'pair': 'BTCUSDT', 'interval': '1m', 'strategy': 'macdas_strat', 'stop_loss': .5, 'strategy_config': {"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': 8, 'rsi_lb': 35, 'rsi_ub': 65}}
    print(backtest(config, update=False))
    print(backtest2(config))
compare_backtest()