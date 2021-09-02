from yaza.binance import Exchange, get_backdata
from yuzu.strategies.macdas_strat import macdas_strat
from yaza.optimize import optimize, backtest
from yaza.plot import plot
from time import sleep
import json
import sys

# config_file = open('./config.json')
# config = json.loads(config_file.read())['strategies']['macdas_strat']['1m']
config = {
    "buy_slow_len": 34,
    "buy_fast_len": 22,
    "buy_sig_len": 6,
    "buy_rsi_len": 5,
    "sell_slow_len": 42,
    "sell_fast_len": 7,
    "sell_sig_len": 4,
    "sell_rsi_len": 20,
    "rsi_lb": 24.1,
    "rsi_ub": 53.3,
    "stop_limit_buy": 0.0035,
    "stop_limit_sell": 0.0082,
    "stop_limit_loss": 0.0054,
    "min_ticks": 42,
}
ranges = {
    "buy_slow_len": [25, 50],
    "buy_fast_len": [5, 24],
    "buy_sig_len": [1, 12],
    "buy_rsi_len": [5, 50],
    "sell_slow_len": [25, 50],
    "sell_fast_len": [5, 24],
    "sell_sig_len": [1, 12],
    "sell_rsi_len": [5, 50],
    "rsi_lb": [0.0, 70.0],
    "rsi_ub": [30.0, 100.0],
    "stop_limit_buy": [0.001, 0.01],
    "stop_limit_sell": [0.001, 0.01],
    "stop_limit_loss": [0.001, 0.01],
}

option, pair, interval = sys.argv[1:4]
if option == 'trade':
    trader = Exchange(macdas_strat, config)
    trader.start_trading(pair, interval)
    input("press [ENTER] to stop.\n")
    trader.stop_trading(pair)
elif option == 'optimize':
    new_config = optimize(get_backdata(pair, interval, 500000), macdas_strat, ranges)
    print(f'** RESULTS FOR macdas_strat ON {interval} {pair} **')
    print(json.dumps(new_config, indent=2))
elif option == 'backtest':
    data = get_backdata(pair, interval, 1000)
    data = macdas_strat(data, config)
    data = backtest(data, config, plot=True)
else:
    print('** Invalid Usage **')
    print('try: python yaza_main.py [trade|optimize|backtest] [PAIR] [INTERVAL]')
