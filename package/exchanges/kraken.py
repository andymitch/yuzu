from pandas import DataFrame
import numpy as np
import requests
import datetime
from pytz import reference
import urllib
import time
import hmac
import hashlib
import base64
from ..utils import since, safe_round


def get_websocket(pair, interval, on_message):
    send_msg = {
        "event": "subscribe",
        "pair": [pair],
        "subscription": {"name": "ohlc", "interval": int(interval)}
    }
    uri = 'wss://ws.kraken.com/'
    pass # TODO: get_websocket

# interval: str -> minute_based_interval: int
def kraken_interval(interval: str) -> int:
    value, base = interval[:-1], interval[-1]
    return value * (60 if base == 'h' else 1440 if base == 'd' else 1)

# get historical OHLCV candles
def get_backdata(pair: str, interval: str, ticks: int = 1000) -> DataFrame:
    req_str = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={__kraken_interval(interval)}&since={since(interval, ticks)}'
    raw = list(requests.get(req_str).json()['result'].values())[0]
    cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    data = DataFrame(raw, columns=cols).drop(["vwap", "count"], axis=1)
    data = data.astype({'open': np.float, 'high': np.float, 'low': np.float, 'close': np.float, 'volume': np.float})
    data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(t,tz=reference.LocalTimezone()).strftime('%Y-%m-%dT%H:%M:%S'))
    return data.set_index("time").sort_index()

class KrakenClient:

    TRADING_FEE = .0026

    # Kraken API signature util
    def __signature(self, url: str, params: Dict, secret: str) -> str:
        params['nonce'] = str(int(1000*time.time()))
        postparams = urllib.parse.urlencode(params)
        encoded = (params['nonce'] + postparams).encode()
        message = url.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    # Kraken API request util
    def __authenticated_request(self, endpoint: str, params: Dict = {}, key=None, secret=None) -> Union[Dict, bool]:
        key, secret = keypair('kraken', key, secret)
        if not key or not secret: return False
        headers = {'API-Key': key, 'API-Sign': self.__signature(endpoint, params, secret)}
        res = requests.post(('https://api.kraken.com' + endpoint), headers=headers, data=params).json()
        if len(res['error']) > 0:
            print(res['error'])
            return False
        return res['result']

    # interpret websocket tick for current candle
    def __condition_tick(self, msg) -> Callable[Any, Tuple[Optional[str], Optional[Row]]]:
        if isinstance(msg, list):
            raw = msg[1]
            time = datetime.datetime.fromtimestamp(int(float(raw[1]))).isoformat()
            raw = {'open': float(raw[2]), 'high': float(raw[3]), 'low': float(raw[4]), 'close': float(raw[5]), 'volume': float(raw[7])}
            return time, raw
        return None, None

    def get_tradable_pairs(self) -> DataFrame:
        tradable_pairs = requests.get('https://api.kraken.com/0/public/AssetPairs').json()['result']
        raw = []
        for k,v in tradable_pairs.items():
            try:
                raw.append({'pair': k, 'pair_alt': v['altname'], 'pair_ws': v['wsname'], 'left': v['base'], 'right': v['quote'], 'decimal': v['lot_decimals']})
            except:pass
        return DataFrame(raw)

    def get_pair_info(self, pair: str) -> Dict:
        pairs = self.get_tradable_pairs()
        ret_pair = pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)].to_dict(orient='records')
        try:
            return ret_pair[0]
        except: print(pair, 'is not a valid pair.')

    def validate_pair(self, pair: str) -> bool:
        pairs = self.get_tradable_pairs()
        return pair in pairs['pair'].values or pair in pairs['pair_alt'].values

    def get_ws_symbol(self, pair: str) -> str:
        pairs = self.get_tradable_pairs()
        return pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)]['pair_ws'].iat[0]

    def get_left_right(self, pair: str) -> str:
        pairs = self.get_tradable_pairs()
        pair_row = pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)]
        return pair_row['left'].iat[0], pair_row['right'].iat[0]

    # get user balances
    def get_balances(self, include_fiat_values: bool = False, key: str = None, secret: str = None) -> Dict:
        res = self.__authenticated_request('/0/private/Balance', key=key, secret=secret)
        if include_fiat_values:
            balances = {k: {'amount': float(v), 'value': self.get_current_value(k, amount=float(v))} for k,v in res.items()}
            total = sum([s['value'] for s in balances.values()])
            return {
                'balances': balances,
                'total': total
            }
        return {k: float(v) for k,v in res.items()}

    # get ticker value of asset (safely multiplied by amount if given) (quoted by base, default USD)
    def get_current_value(self, symbol: Optional[str] = None, base: str = 'ZUSD', pair: Optional[str] = None, amount: float = 1):
        if not pair:
            if symbol in ['ETH2.S','ETH2']: # since ETH 2.0 is not tradable
                symbol = 'XETH'
            pair = self.get_pair_info(symbol+base)["pair_alt"]
        req_str = f'https://api.kraken.com/0/public/Ticker?pair={pair}'
        res = requests.get(req_str).json()
        if res['error']: print(req_str['error'])
        else: return float(res['result'][pair]['c'][0]) * amount

    # place buy/sell order
    def create_order(self, side: OrderType, pair: str, amount: Optional[float] = None, test: bool = False, key=None, secret=None) -> bool:
        pair = self.get_pair_info(pair)
        if not amount: amount = self.get_balances()[pair['right']] if side == 'buy' else self.get_balances()[pair['left']]
        if side == 'buy': amount /= self.get_current_value(pair=pair['pair_alt'])
        amount *= (1-self.TRADING_FEE)
        amount = safe_round(amount, pair['decimal'])
        print(amount)
        params = {
            "ordertype": "market",
            "type": side,
            "volume": amount,
            "pair": pair['pair_alt'],
            "validate": test
        }
        return self.__authenticated_request('/0/private/AddOrder', params=params, key=key, secret=secret)

    # get open/closed user orders
    def get_orders(self, key: str = None, secret: str = None):
        open = self.__authenticated_request('/0/private/OpenOrders', params={'trades': True})['open']
        closed = self.__authenticated_request('/0/private/ClosedOrders', params={'trades': True})['closed']
        return {'open': open, 'closed': closed}

    # cancel open order by id
    def cancel_order(self, order_id: str, key: str = None, secret: str = None):
        if order_id == 'all':
            self.__authenticated_request('/0/private/CancelAll')
        else:
            self.__authenticated_request('/0/private/CancelOrder', params={'txid': order_id})

# TODO: take everything out of class