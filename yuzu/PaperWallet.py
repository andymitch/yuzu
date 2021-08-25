from numpy import isnan
from yuzu.types import *
from datetime import datetime
from yuzu.utils import colorprint

NO_ORDER, BOUGHT, SOLD, STOP_LOSSED = 0, 1, 2, 3

class PaperWallet:

    stop_buy, stop_sell, stop_loss, open_trade = {}, {}, {}, {}

    def __init__(self, stop_limit_buy, stop_limit_sell, stop_limit_loss, trading_fee: float = .001, init_balance: Optional[dict] = None, init_pairs: Optional[List[str]] = None):
        self.stop_limit_buy = stop_limit_buy
        self.stop_limit_sell = stop_limit_sell
        self.stop_limit_loss = stop_limit_loss
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
        if self.stop_buy[left+right] and self.stop_buy[left+right] < data['high'].iat[-1]:
            self.balance[left] = self.balance[right] * (1-self.fee) / self.stop_buy[left+right]
            self.balance[right] = 0.0
            data.at[i, 'bought'] = self.stop_buy[left+right]
            self.stop_loss[left+right] = self.stop_buy[left+right] - (self.stop_buy[left+right] * self.stop_limit_loss)
            self.stop_buy[left+right] = None
            return data, BOUGHT
        if not isnan(data['buy'].iat[-1]) and (self.stop_buy is None or data['close'].iat[-1] + (data['close'].iat[-1] * self.stop_limit_sell) < self.stop_buy):
            self.stop_buy[left+right] = data['close'].iat[-1] + (data['close'].iat[-1] * self.stop_limit_buy)
        return data, NO_ORDER

    def sell(self, data, left='left', right='right'):
        if self.stop_sell[left+right] and self.stop_sell[left+right] > data['low'].iat[-1]:
            self.balance[right] = self.balance[left] * (1-self.fee) * self.stop_sell[left+right]
            self.balance[left] = 0.0
            data.at[data.index[-1], 'sold'] = self.stop_sell[left+right]
            self.stop_sell[left+right] = None
            self.stop_loss[left+right] = None
            return data, SOLD
        elif self.stop_loss[left+right] and self.stop_loss[left+right] > data['low'].iat[-1]:
            self.balance[right] = self.balance[left] * (1-self.fee) * self.stop_loss[left+right]
            self.balance[left] = 0.0
            data.at[data.index[-1], 'stop_lossed'] = self.stop_loss[left+right]
            self.stop_sell[left+right] = None
            self.stop_loss[left+right] = None
            return data, STOP_LOSSED
        if not isnan(data['sell'].iat[-1]) and (self.stop_sell is None or data['close'].iat[-1] + (data['close'].iat[-1] * self.stop_limit_sell) > self.stop_sell):
            self.stop_sell[left+right] = data['close'].iat[-1] - (data['close'].iat[-1] * self.stop_limit_sell)
        return data, NO_ORDER

    def update(self, data: DataFrame, left='left', right='right', verbose: bool = False) -> DataFrame:
        data, bought = self.buy(data, left, right)
        data, sold = self.sell(data, left, right)
        if verbose:
            time_str = "%b %d, %Y [%H:%M]"
            if bought == BOUGHT:     colorprint.cyan(f'{datetime.strptime(data.index[-1], "%Y-%m-%dT%H:%M:%S").strftime(time_str)}       buy {left} @ {data["close"].iat[-1]} {right}')
            elif sold == SOLD:     colorprint.yellow(f'{datetime.strptime(data.index[-1], "%Y-%m-%dT%H:%M:%S").strftime(time_str)}      sell {left} @ {data["close"].iat[-1]} {right}')
            elif sold == STOP_LOSSED: colorprint.red(f'{datetime.strptime(data.index[-1], "%Y-%m-%dT%H:%M:%S").strftime(time_str)} stop loss {left} @ {data["close"].iat[-1]} {right}')
        return data

    def get_balance(self, left: str, right: str, price: float) -> float:
        return self.balance[right] + (self.balance[left] * price)
