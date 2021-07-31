from binance.streams import BinanceSocketManager
from binance.client import AsyncClient
from binance import Client
from pandas import DataFrame, to_numeric, read_csv
from typing import Union, List
from pytz import reference
import pandas as pd
import datetime
import os


LEFT, RIGHT = 0, 1

def get_available_pairs():
    return {pair['symbol']: (pair['baseAsset'], pair['quoteAsset']) for pair in Client().get_exchange_info()['symbols']}

def get_start(interval, ticks=1000):
    interval_map = {"m": "minutes", "h": "hours", "d": "days"}
    num = int(interval[:-1]) * ticks
    return f"{num} {interval_map[interval[-1]]} ago"

class BinanceUS():
    pairs = get_available_pairs()

    def __init__(self, key, secret):
        self.__client = Client(key, secret, tld='us')

    def set_keypair(self, key, secret):
        self.__client = Client(key, secret, tld='us')

    def buy(self, pair: str) -> bool:
        amount = self.get_balance(self.pairs[pair][LEFT])['amount']
        # TODO: round and reduce (make room for fee) amount
        try:
            order = self.__client.order_market_buy(symbol=pair, quoteOrderQty=amount)
            return True, order
        except: return False, None

    def sell(self, pair: str) -> bool:
        amount = self.get_balance(self.pairs[pair][RIGHT])['amount']
        # TODO: round and reduce (make room for fee) amount
        try:
            order = self.__client.order_market_sell(symbol=pair, quantity=amount)
            return True, order
        except: return False, None

    def get_balance(self, asset: str = None):
        if asset is None:
            return {b['asset']: {'amount': b['free'], 'value': self.__client.get_symbol_ticker(symbol=b['asset'])['price'] * b['free']} for b in self.__client.get_account()['balances']}
        b = self.__client.get_asset_balance(asset)
        return {asset: {'amount': b['free'], 'value': self.quote_assets(b['free']) * b['free']}}

    @staticmethod
    def get_backdata(pair, interval, min_ticks):
        klines = Client().get_historical_klines(pair, interval, get_start(interval, min_ticks))
        cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
        data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
        data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%dT%H:%M:%S'))
        return data.set_index("time").sort_index()

    def condition_data(self, msg: dict, data: pd.DataFrame) -> bool:
        time = datetime.datetime.fromtimestamp(float(msg['k']['t']/1000)).isoformat()
        open, high, low, close, volume = float(msg['k']['o']), float(msg['k']['h']), float(msg['k']['l']), float(msg['k']['c']), float(msg['k']['v'])
        row = {'open': open, 'high': high, 'low': low, 'close': close, 'volume': volume}

        print('CONDITIONING DATA')
        if time in data.index.values:
            print('UPDATING TICK')
            data.loc[time, row.keys()] = row.values()
            return data, False
        else:
            print('ADDING TICK')
            data = data.append(DataFrame(row, index=[time]))
            return data, True

    def left(self, pair: str):
        return self.pairs[pair][LEFT]
    def right(self, pair: str):
        return self.pairs[pair][RIGHT]

    @staticmethod
    def quote_pairs(pair_or_pairs: Union[str, List[str]]) -> Union[float, List[float]]:
        print(pair_or_pairs)
        return float(Client().get_symbol_ticker(symbol=pair_or_pairs)['price']) # TODO: remove
        if isinstance(pair_or_pairs, str):
            return float(Client().get_symbol_ticker(symbol=pair_or_pairs)['price'])
        else:
            return [float(Client().get_symbol_ticker(symbol=pair)['price']) for pair in pair_or_pairs]

    @staticmethod
    def get_ws_endpoint(pair, interval): return f'wss://stream.binance.us:9443/ws/{pair.lower()}@kline_{interval}'


key = 'INUndRooqLHySH6k5dRUA44AH8HG7AjXi3pqZeigQ2VH9yfzAVUjKwtB7ErQFo3X'
secret = 'RE9h6EXkw9y0JmxEUTC4SZgRWrr166QM0AskpXen22H13SqW7OgaJQC4ZcCxKTWG'

'''
create order response:
{
    "symbol": "BTCUSDT",
    "orderId": 28,
    "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
    "transactTime": 1507725176595,
    "price": "0.00000000",
    "origQty": "10.00000000",
    "executedQty": "10.00000000",
    "status": "FILLED",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "SELL"
}
'''