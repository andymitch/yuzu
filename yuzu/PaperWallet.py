from numpy import isnan
from .types import *
from datetime import datetime
from .utils import colorprint

NO_ORDER, BOUGHT, SOLD, STOP_LOSSED = 0, 1, 2, 3

class PaperWallet:

    stop_buy, stop_sell, stop_loss, open_trade = {}, {}, {}, {}

    def __init__(self, config: dict, trading_fee: float = .001, init_balance: Optional[dict] = None, init_pairs: Optional[List[str]] = None, verbose: bool = False, debug: bool = False):
        self.stop_limit_buy = config['stop_limit_buy']
        self.stop_limit_sell = config['stop_limit_sell']
        self.stop_limit_loss = config['stop_limit_loss']
        self.verbose = verbose
        self.debug = debug
        if not (init_balance and init_pairs):
            init_balance = {'left': 0.0, 'right': 100.0}
            init_pairs = ['leftright']
        self.balance = init_balance
        for pair in init_pairs:
            self.stop_buy[pair] = None
            self.stop_sell[pair] = None
            self.stop_loss[pair] = None
            self.open_trade[pair] = False
        self.fee = trading_fee

    def fund(self, coin: str, amount: float):
        if coin in self.balance.keys():
            self.balance[coin] += amount
        else:
            self.balance[coin] = amount
        print(self.balance)

    def add_pair(self, pair: str):
        self.stop_buy[pair] = None
        self.stop_sell[pair] = None
        self.stop_loss[pair] = None
        self.open_trade[pair] = False

    def buy(self, data, left='left', right='right'):
        symbol = left+right
        if self.debug: print(symbol, '[paper buy] checking...')
        if self.balance[right] > 0:
            if self.debug: print(symbol, '[paper buy] enough funds', self.balance)
            if self.debug: print(symbol, '[paper buy] checking stop_buy:', self.stop_buy[symbol])
            if self.stop_buy[symbol] and self.stop_buy[symbol] <= data['high'].iat[-1]:
                if self.debug: print(symbol, '[paper buy] stop limit buy triggered:', self.stop_buy[symbol], '<', data['high'].iat[-1])
                self.balance[left] += self.balance[right] * (1-self.fee) / self.stop_buy[symbol]
                self.balance[right] = 0.0
                data.at[data.index[-1], 'bought'] = self.stop_buy[symbol]
                if self.debug: print(symbol, '[paper buy] bought @', data.at[data.index[-1], 'bought'])
                stop_loss = self.stop_buy[symbol] - (self.stop_buy[symbol] * self.stop_limit_loss)
                if self.debug: print(symbol, '[paper buy] setting stop loss @', stop_loss)
                self.stop_loss[symbol] = stop_loss
                self.stop_buy[symbol] = None
                self.open_trade[symbol] = False
                return data, BOUGHT
            if self.debug: print(symbol, '[paper buy] stop limit buy not triggered:', self.stop_buy[symbol], '>', data['high'].iat[-1], '|| is None')
            if not isnan(data['buy'].iat[-1]): # TODO: check this first
                new_stop_buy = data['close'].iat[-1] + (data['close'].iat[-1] * self.stop_limit_buy)
                if self.debug: print(symbol, '[paper buy] checking to update stop_buy from ', self.stop_buy[symbol], 'to', new_stop_buy)
                if self.stop_buy[symbol] is None or new_stop_buy < self.stop_buy[symbol]:
                    if self.debug: print(symbol, '[paper buy] found new or lower price point')
                    self.stop_buy[symbol] = new_stop_buy
                    self.open_trade[symbol] = True
                    if self.debug or self.verbose: print(symbol, '[paper buy] updated stop_buy')
                elif self.debug: print(symbol, '[paper buy] best stop_buy already exists')
        elif self.debug: print(symbol, '[paper buy] not enough funds', self.balance)
        return data, NO_ORDER

    def sell(self, data, left='left', right='right'):
        symbol = left+right
        if self.debug: print(symbol, '[paper sell] checking...')
        if self.balance[left] > 0:
            if self.debug: print(symbol, '[paper sell] enough funds', self.balance)
            if self.debug: print(symbol, '[paper sell] checking stop_sell:', self.stop_sell[symbol])
            if self.stop_sell[symbol] and self.stop_sell[symbol] >= data['low'].iat[-1]:
                if self.debug: print(symbol, '[paper sell] stop limit sell triggered:', self.stop_sell[symbol], '<', data['low'].iat[-1])
                self.balance[right] += self.balance[left] * (1-self.fee) * self.stop_sell[symbol]
                self.balance[left] = 0.0
                data.at[data.index[-1], 'sold'] = self.stop_sell[symbol]
                if self.debug: print(symbol, '[paper sell] sold @', data.at[data.index[-1], 'sold'])
                self.stop_sell[symbol] = None
                self.stop_loss[symbol] = None
                self.open_trade[symbol] = False
                return data, SOLD
            if self.debug: print(symbol, '[paper sell] stop limit sell not triggered:', self.stop_sell[symbol], '<', data['low'].iat[-1], '|| is None')
            elif self.stop_loss[symbol] and self.stop_loss[symbol] > data['low'].iat[-1]:
                if self.debug: print(symbol, '[paper stop_loss] stop limit loss triggered:', self.stop_loss[symbol], '<', data['low'].iat[-1])
                self.balance[right] = self.balance[left] * (1-self.fee) * self.stop_loss[symbol]
                self.balance[left] = 0.0
                data.at[data.index[-1], 'stop_lossed'] = self.stop_loss[symbol]
                if self.debug: print(symbol, '[paper stop_loss] stop_lossed @', data.at[data.index[-1], 'stop_lossed'])
                self.stop_sell[symbol] = None
                self.stop_loss[symbol] = None
                self.open_trade[symbol] = False
                return data, STOP_LOSSED
            if not isnan(data['sell'].iat[-1]):
                new_stop_sell = data['close'].iat[-1] - (data['close'].iat[-1] * self.stop_limit_sell)
                if self.debug: print(symbol, '[paper sell] checking to update stop_sell from ', self.stop_sell[symbol], 'to', new_stop_sell)
                if self.stop_sell[symbol] is None or new_stop_sell > self.stop_sell[symbol]:
                    if self.debug: print(symbol, '[paper sell] found new or higher price point')
                    self.stop_sell[symbol] = new_stop_sell
                    self.open_trade[symbol] = True
                    if self.debug or self.verbose: print(symbol, '[paper sell] updated stop_sell')
                elif self.debug: print(symbol, '[paper sell] best stop_sell already exists')
        elif self.debug: print(symbol, '[paper sell] not enough funds', self.balance)
        return data, NO_ORDER

    def update(self, data: DataFrame, left='left', right='right') -> DataFrame:
        data, bought = self.buy(data, left, right)
        data, sold = self.sell(data, left, right)
        if self.verbose:
            time_str = "%b %d, %Y [%H:%M]"
            if bought == BOUGHT:     colorprint.cyan(f'{datetime.strptime(data.index[-1], "%Y-%m-%d %H:%M:%S").strftime(time_str)}       buy {left} @ {data["close"].iat[-1]} {right}')
            elif sold == SOLD:     colorprint.yellow(f'{datetime.strptime(data.index[-1], "%Y-%m-%d %H:%M:%S").strftime(time_str)}      sell {left} @ {data["close"].iat[-1]} {right}')
            elif sold == STOP_LOSSED: colorprint.red(f'{datetime.strptime(data.index[-1], "%Y-%m-%d %H:%M:%S").strftime(time_str)} stop loss {left} @ {data["close"].iat[-1]} {right}')
        return data

    def get_balance(self, left: str, right: str, price: float) -> float:
        return self.balance[right] + (self.balance[left] * price)