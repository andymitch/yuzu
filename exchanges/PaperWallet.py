
from utils import get_exchange
import json

class PaperWallet:
    def __init__(self, exchange_name: str, init_balance: dict = {}):
        self.balance = init_balance
        self.exchange_name = exchange_name

    def fund(self, coin: str, amount: float):
        if coin in self.balance.keys():
            self.balance[coin] += amount
        else:
            self.balance[coin] = amount

    def buy(self, pair_left: str, pair_right: str, price: float, fee: float = .001) -> bool:
        if pair_right in self.balance.keys() and self.balance[pair_right] > 0:
            self.balance[pair_right] = 0.0
            self.fund(pair_left, self.balance[pair_right] * (1-fee) / price)
            return True
        return False

    def sell(self, pair_left: str, pair_right: str, price: float, fee: float = .001) -> bool:
        if pair_left in self.balance.keys() and self.balance[pair_left] > 0:
            self.fund(pair_right, self.balance[pair_left] * (1-fee) * price)
            self.balance[pair_left] = 0.0
            return True
        return False

    def get_balance(self, pair_left: str, pair_right: str, price: float) -> dict:
        return self.balance[pair_right] + (self.balance[pair_left] * price)
        '''
        coins = self.assets.keys() if coin == 'all' else [coin] if coin in self.assets.keys() else []
        values = get_exchange(self.exchange_name).quote_pairs([f'{coin}{base}' for coin in coins])
        balances = {c: {'amount': self.balance[c], 'value': values[c] * self.balance[c]} for c in coins}
        return {'total': sum([c['value'] for c in balances.values()]), 'balances': balances}
        '''