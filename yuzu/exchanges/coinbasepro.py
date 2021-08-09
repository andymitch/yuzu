def __condition_tick():pass
def get_backdata():pass
def get_websocket(data: DataFrame, pair: str, interval: str, on_tick: Callable) -> Websocket:
    url = 'wss://ws-feed.pro.coinbase.com'
    '''
    send_msg = {
        "event": "subscribe",
        "pair": [pair],
        "subscription": {"name": "ohlc", "interval": int(interval)}
    }
    return CreateWebsocket(data, url, pair, __kraken_interval(interval), __condition_tick, on_tick, send_msg)'''


def get_balances():pass
def get_pair_info():pass
def get_account():pass

def create_order():pass
def get_orders():pass
def cancel_order():pass