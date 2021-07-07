from binance.streams import BinanceSocketManager
from binance.client import AsyncClient
from binance import Client
from pandas import DataFrame, to_numeric, read_csv
from .IExchange import IExchange
import datetime
import os


class BinanceUS(IExchange):
    def __init__(self, key=None, secret=None, paper_trade=True):
        super().__init__(key=key, secret=secret, paper_trade=paper_trade)
        self.client = AsyncClient(self._IExchange__API_KEY, self._IExchange__API_SECRET, tld="us")
        if not None in [self._IExchange__API_KEY, self._IExchange__API_SECRET]:
            try:
                if not self.client.get_account_status()["data"] == "Normal":  # TODO: possibly need to wrap in json.loads()
                    print(f"\033[91m** BinanceUS API key and/or secret may be incorrect! **\033[00m")
            except:
                print(f"\033[91m** BinanceUS API key and/or secret may be incorrect! **\033[00m")

    @staticmethod
    def get_backdata(pair, interval, start, finish="now", update=False):
        root_path = "../backdata"
        if not os.path.exists(root_path):
            os.mkdir(root_path)
        root_path = "./backdata/binanceus"
        if not os.path.exists(root_path):
            os.mkdir(root_path)
        file_path = f"{root_path}/{pair}-{interval.upper()}.csv"
        if update or not os.path.exists(file_path):
            klines = Client().get_historical_klines(pair, interval, start, finish)
            cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
            data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
            data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
            data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(float(t / 1000)).isoformat())
            data = data.set_index("time").sort_index()
            data.to_csv(file_path)
            return data
        else:
            data = read_csv(file_path)
            data = data.set_index("time").sort_index()
            return data

    # TODO: live trading
    def run(self):
        socket = BinanceSocketManager(self.client)
        # ...

    # TODO: get user account info
    def get_account(self):
        # TODO: maybe decide on a uniform format across all exchanges to condition response before returning
        return self.client.get_account()
