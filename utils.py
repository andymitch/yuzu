from exchanges import *
from strategies import *
import datetime
import os
from pandas import DataFrame, read_csv, to_numeric
from binance import Client
from importlib import import_module


def get_strategy(strategy_name: str):
    return getattr(import_module(f"strategies.{strategy_name}"), strategy_name)


def get_exchange(exchange_name: str, exchange_key: str, exchange_secret: str, min_ticks: str, stop_loss_percent: float) -> IExchange:
    if exchange_name == "BinanceUS":
        return BinanceUS(exchange_key, exchange_secret)
    elif exchange_name == "Kraken":
        return Kraken(exchange_key, exchange_secret)
    elif exchange_name == "CoinbasePro":
        return CoinbasePro(exchange_key, exchange_secret)


def get_backdata(pair, interval, start, finish="now", exchange="BinanceUS", update=False) -> DataFrame:
    if exchange == "BinanceUS":
        return BinanceUS.get_backdata(pair, interval, start, finish, update)
    elif exchange == "Kraken":
        return Kraken.get_backdata(pair, interval, start, finish, update)
    elif exchange == "CoinbasePro":
        return CoinbasePro.get_backdata(pair, interval, start, finish, update)


def get_timeframe(interval, max_ticks):
    interval_map = {"m": "minutes", "h": "hours", "d": "days"}
    num = int(interval[:-1]) * max_ticks
    return f"{num} {interval_map[interval[-1]]} ago"


if __name__ == "__main__":
    print(get_strategy("awesome_strat")(get_backdata("ADABTC", "1h", "1 month ago", exchange="BinanceUS", update=True)).to_markdown())
    ex = get_exchange("BinanceUS", "my_key", "my_secret", 200, 0.3)
    ex.show()
