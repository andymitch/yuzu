from yaza.binance import Exchange
from yuzu.strategies.macdas_strat import macdas_strat
from time import sleep
import json

config_file = open('./config.json')
config = json.loads(config_file.read())['strategies']['macdas_strat']['1m']
trader = Exchange(macdas_strat, config)
trader.start_trading('BTCUSD', '1m')
input('press [ENTER] to stop.\n')
trader.stop_trading('BTCUSD')