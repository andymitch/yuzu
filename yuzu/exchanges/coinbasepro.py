
from yuzu.exchanges import Exchange


class CoinbasePro(Exchange):

    def __condition_tick(self):pass
    def get_backdata(self):pass
    def get_websocket(self, data: DataFrame, pair: str, interval: str, on_tick: Callable) -> Websocket:
        url = 'wss://ws-feed.pro.coinbase.com'
        '''
        send_msg = {
            "event": "subscribe",
            "pair": [pair],
            "subscription": {"name": "ohlc", "interval": int(interval)}
        }
        return CreateWebsocket(data, url, pair, __kraken_interval(interval), __condition_tick, on_tick, send_msg)'''


    def get_balances(self):pass
    def get_pair_info(self):pass
    def get_account(self):pass

    def create_order(self):pass
    def get_orders(self):pass
    def cancel_order(self):pass