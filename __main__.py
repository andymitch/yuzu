from backtest import backtest
from plot import Plot
from tqdm import tqdm
from p_tqdm import p_map
import pandas as pd
from utils import get_backdata, get_strategy, get_strategy_plot, get_timeframe

#config = {"pair": "ADABTC", "interval": "1d", "strategy": "awesome_strat", "strategy_config": {"rsi_lookback": 8, "rsi_range": 70, "ao_fast_lookback": 5, "ao_slow_lookback": 34}, "stop_loss": 0.35}
#plot(backtest(config, verbose=True, update=True), [{"column": "ao", "type": "bar"}, {"column": "rsi", "type": "line", "color": "purple"}], "ADABTC").show()

'''
best = {'ob': None, 'os': None, 'score': 0}
for os in tqdm([15,20,25,30,35]):
    for ob in [65,70,75,80,85]:
        config = {"pair": "ADABTC", "interval": "1m", "strategy": "stc_strat", "strategy_config": {'oversold': os, 'overbought': ob}, "stop_loss": 0.35}
        _, score = backtest(config, verbose=False, update=False)
        if score > best['score']:
            best = {'ob': ob, 'os': os, 'score': score}
config = {"pair": "ADABTC", "interval": "1d", "strategy": "stc_strat", "strategy_config": {'oversold': best['os'], 'overbought': best['ob']}, "stop_loss": 0.35}
data, _ = backtest(config, verbose=True, update=True)
plot(data, [{"column": "stc", "type": "line", "color": "purple"}], "ADABTC").show()

config = {"pair": "ADABTC", "interval": "1d", "strategy": "stc_strat", "strategy_config": {'oversold': 10, 'overbought': 90}, "stop_loss": 0.35}
data, score = backtest(config, verbose=True, update=True)
print('score:', score)
plot(data, [{"column": "stc", "type": "line", "color": "purple"},{"column": "so", "type": "bar"},{"column": "ema", "type": "line", "color": "white", "inline": True}], "ADABTC").show()
'''

def test_macd_strat(pair='BTCUSDT', interval='1m', stop_loss=0.35):
    config = {"pair": pair, "interval": interval, "strategy": "macd_strat", "stop_loss": stop_loss}
    data, _ = backtest(config, verbose=True, update=False)
    plot = Plot(data, f'{config["strategy"]} ({config["pair"]} {config["interval"]})')
    plot.add_trace('sma200', 0, 'line', 'aqua')
    plot.add_trace('hist', 1, 'bar')
    plot.add_trace('macd', 1, 'line', 'yellow', True)
    plot.add_trace('fast_ma', 2, 'line', 'teal')
    plot.add_trace('slow_ma', 2, 'line', 'orange')
    plot.show()

def test_awesome_strat(pair='ADABTC', interval='1d', config={"rsi_lookback": 8, "rsi_range": 70, "ao_fast_lookback": 5, "ao_slow_lookback": 34}, stop_loss=0.35):
    config = {"pair": pair, "interval": interval, "strategy": "awesome_strat", "strategy_config": config, "stop_loss": stop_loss}
    data, _ = backtest(config, verbose=True, update=True)
    plot = Plot(data, f'{config["strategy"]} ({config["pair"]} {config["interval"]})')
    plot.add_trace('ao', 1, 'bar')
    plot.add_trace('rsi', 2, 'line', 'purple')
    plot.show()

def optimize(pair, interval, strategy, configs, file_name=None):
    results = pd.DataFrame(p_map(lambda config: backtest({"pair": pair, "interval": interval, "strategy": strategy, "strategy_config": config, "stop_loss": config.get('stop_loss', .35)}, verbose=False, update=False, plot=False)[1], configs)).drop(['slow_len', 'fast_len', 'sig_len'], axis=1)
    try:
        results = results.drop(['best_trade', 'worst_trade'])
    except: pass
    results.to_csv(f'./results/{strategy}-{pair}-{interval}')
    return results.sort_values('score', ascending=False)

def main(configs):
    from tqdm import tqdm
    pair = 'BTCUSDT'
    for i in tqdm(['1m','5m','15m','1h','2h','1d']):
        print(f'\n== {i} ==')
        print(optimize('BTCUSDT', i, 'macdas_strat', configs).head(10))
        #backtest({"pair": pair, "interval": i, "strategy": "macdas_strat", "strategy_config": results[0]['config'], "stop_loss": results[0]['config']['stop_loss']}, verbose=True, update=False, plot=True)

#configs = [{"slow_len": 26, "fast_len": 12, "sig_len": 9, 'rsi_len': l, 'rsi_lb': lb, 'rsi_ub': ub, 'stop_loss': sl} for l in [4,8,14,24] for lb in [25,30,35,40] for ub in [60,65,70,75] for sl in [.05,.1,.15,.2,.3,.35]]
#main(configs)
#print(optimize('BTCUSDT', '1d', 'macdas_strat', configs).head(10))
pair, interval, strategy_name = 'BTCUSDT', '1m', 'macdas_strat'
config = {'slow_len': 28, 'fast_len': 7, 'sig_len': 2, 'rsi_len': 11, 'rsi_lb': 46.4, 'rsi_ub': 56.4}
data = get_backdata(pair, interval, get_timeframe(interval, 40000))
data = get_strategy(strategy_name)(data, config)
data, _ = backtest(data, stop_loss=.35, verbose=True, update=True)
get_strategy_plot(strategy_name)(data, pair, interval).show()
