from pandas import read_csv
import os


class Kraken:  # KRAKEN EXCHANGE
    def __init__(self, key, secret):
        pass
        # TODO: setup a client with kraken like binance does

    @staticmethod
    def get_backdata(pair, interval, start, finish="now", update=False):
        file_path = f"./backdata/kraken/{pair}-{interval.upper()}.csv"
        if update or not os.path.exists(file_path):
            pass  # TODO: implement Kraken API data pull
        else:
            data = read_csv(file_path)
            data = data.set_index("time").sort_index()
            return data

    # TODO: live trading

    # TODO: get user account info
