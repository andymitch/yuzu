from utils import get_strategy_class, get_exchange_class
import pandas as pd
from multiprocessing import Pool
from functools import partial
import json

class Trader:
    exchange, strategy = None, None
    def __init__(self, config_name):
        self.config = json.open(open(f'configs/{config_name}.json'))
        sucess, StrategyClass = get_strategy_class(self.config['strategy'])
        if not sucess:
            raise Exception(StrategyClass)
        self.strategy = StrategyClass(**self.config['strategy_args'])

        sucess, ExchangeClass = get_exchange_class(self.config['exchange'])
        if not sucess:
            raise Exception(ExchangeClass)
        self.exchange = ExchangeClass(self.config['exchange_key'], self.config['exchange_secret'])

        for pair in self.config['pair_whitelist']:
            if not pair.endswith(self.config['pair_base']):
                raise Exception(f'pair: {pair} not compatible with base: {self.config["pair_base"]}')
        self.base = self.config['pair_base']
        self.whitelist = self.config['pair_whitelist']

        if not self.config['interval'] in self.exchange.acceptable_intervals:
            raise Exception(f'interval: {self.config["interval"]} not accepted by exchange: {self.exchange.name}')
        self.interval = self.config['interval']

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
            p.map(partial(self.exchange.run, callback=self.on_tick), self.pairs.items())
