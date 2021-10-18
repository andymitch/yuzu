from .utils.getters import get_exchange
from .utils.types import *

# TODO: handle ws and manage trading (exchanges can be stateful but shouldn't contain any driver code)
class Trader:

    def __init__(self, exchange_name: str, key: str = None, secret: str = None, paper_mode: bool = False):
        self.exchange = get_exchange(exchange_name)
        if key and secret:
            assert self.exchange.authenticate(key, secret), 'Exchange authentication unsuccessful, please review your API keypair.'
        else: key, secret = None, None
        self.__key = key,
        self.__secret = secret
        self.paper_mode = paper_mode

    # TODO: start websocket

    # TODO: stop websocket

    # TODO: start api

    # TODO: stop api

    # TODO: start trading
    def start_trading(self, symbol: str, interval: str, strategy: Callable[[DataFrame, dict], DataFrame], config: dict):
        self.config = config
        self.data = self.exchange.get_backdata(symbol, interval, self.config['min_ticks'])
        self.strategy = strategy


    # TODO: stop trading