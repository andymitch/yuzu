from .IExchange import IExchange
from pandas import read_csv
import os


class CoinbasePro(IExchange):  # COINBASE PRO EXCHANGE
    def __init__(self, key, secret):
        super().__init__(key=key, secret=secret)
        print(self._IExchange__API_KEY, self._IExchange__API_SECRET)
        # TODO: setup a client with coinbase like binance does

    @staticmethod
    def get_backdata(pair, interval, start, finish="now", update=False):
        file_path = f"./backdata/coinbasepro/{pair}-{interval.upper()}.csv"
        if update or not os.path.exists(file_path):
            pass  # TODO: implement Coinbase Pro API data pull
        else:
            data = read_csv(file_path)
            data = data.set_index("time").sort_index()
            return data

    # TODO: live trading

    # TODO: get user account info
