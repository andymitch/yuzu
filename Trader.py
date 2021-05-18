from utils import get_strategy_class, get_exchange_class
import pandas as pd
from multiprocessing import Pool
from functools import partial

class Trader:
    exchange, strategy = None, None
    def __init__(self, config):
        sucess, StrategyClass = get_strategy_class(config['strategy'])
        if not sucess:
            raise Exception(StrategyClass)
        self.strategy = StrategyClass(**config['strategy_args'])

        sucess, ExchangeClass = get_exchange_class(config['exchange'])
        if not sucess:
            raise Exception(ExchangeClass)
        self.exchange = ExchangeClass(config['exchange_key'], config['exchange_secret'])

        for pair in config['pair_whitelist']:
            if not pair.endswith(config['pair_base']):
                raise Exception(f'pair: {pair} not compatible with base: {config["pair_base"]}')
        self.base = config['pair_base']
        self.whitelist = config['pair_whitelist']

        if not config['interval'] in self.exchange.acceptable_intervals:
            raise Exception(f'interval: {config["interval"]} not accepted by exchange: {self.exchange.name}')
        self.interval = config['interval']

        self.pairs = {pair: pd.DataFrame() for pair in self.whitelist}

    def on_tick(self, pair):
        self.strategy.get_signals(self.pairs[pair])
        if self.pairs[pair].loc[-1].at['buy']:
            success, msg = self.exchange.buy(pair)
            if not success:
                print(msg)
        if self.pairs[pair].loc[-1].at['sell']:
            success, msg = self.exchange.sell(pair)
            if not success:
                print(msg)

    def run(self):
        with Pool() as p:
            p.map(partial(self.exchange.run, callback=on_tick), self.pairs.items())
