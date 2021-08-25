from yaza.binance import Exchange
from yuzu.strategies.macdas_strat import macdas_strat
from time import sleep
import json
import sys

#config_file = open('./config.json')
#config = json.loads(config_file.read())['strategies']['macdas_strat']['1m']
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
    "min_ticks": 42
}
trader = Exchange(macdas_strat, config)
trader.start_trading(sys.argv[1], sys.argv[2])
input('press [ENTER] to stop.\n')
trader.stop_trading(sys.argv[1])