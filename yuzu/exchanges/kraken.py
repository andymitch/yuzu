import urllib.parse, hashlib, hmac, base64, time
from yuzu.Websocket import CreateWebsocket, Websocket
from yuzu.utils import keypair, since, safe_round
from yuzu.types import *
from pandas import DataFrame, read_csv
from pytz import reference
import numpy as np
import requests
import datetime

TRADING_FEE = .0026

# Kraken API signature util
def __signature(url: str, params: Dict, secret: str) -> str:
    params['nonce'] = str(int(1000*time.time()))
    postparams = urllib.parse.urlencode(params)
    encoded = (params['nonce'] + postparams).encode()
    message = url.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

# Kraken API request util
def __authenticated_request(endpoint: str, params: Dict = {}, key=None, secret=None) -> Union[Dict, bool]:
    key, secret = keypair('kraken', key, secret)
    if not key or not secret: return False
    headers = {'API-Key': key, 'API-Sign': __signature(endpoint, params, secret)}
    res = requests.post(('https://api.kraken.com' + endpoint), headers=headers, data=params).json()
    if len(res['error']) > 0:
        print(res['error'])
        return False
    return res['result']

# interval: str -> minute_based_interval: int
def __kraken_interval(interval: str) -> int:
    value, base = interval[:-1], interval[-1]
    return value * (60 if base == 'h' else 1440 if base == 'd' else 1)

# interpret websocket tick for current candle
def __condition_tick(msg) -> Callable[Any, Tuple[Optional[str], Optional[Row]]]:
    if isinstance(msg, list):
        raw = msg[1]
        time = datetime.datetime.fromtimestamp(int(float(raw[1]))).isoformat()
        raw = {'open': float(raw[2]), 'high': float(raw[3]), 'low': float(raw[4]), 'close': float(raw[5]), 'volume': float(raw[7])}
        return time, raw
    return None, None

# create Kraken websocket connection
def get_websocket(data: DataFrame, pair: str, interval: str, on_tick: Callable) -> Websocket:
    send_msg = {
        "event": "subscribe",
        "pair": [pair],
        "subscription": {"name": "ohlc", "interval": int(interval)}
    }
    return CreateWebsocket(data, 'wss://ws.kraken.com/', pair, __kraken_interval(interval), __condition_tick, on_tick, send_msg)

# get historical OHLCV candles
def get_backdata(pair: str, interval: str, ticks: int = 1000) -> DataFrame:
    req_str = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={__kraken_interval(interval)}&since={since(interval, ticks)}'
    raw = list(requests.get(req_str).json()['result'].values())[0]
    cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    data = DataFrame(raw, columns=cols).drop(["vwap", "count"], axis=1)
    data = data.astype({'open': np.float, 'high': np.float, 'low': np.float, 'close': np.float, 'volume': np.float})
    data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(t,tz=reference.LocalTimezone()).strftime('%Y-%m-%dT%H:%M:%S'))
    return data.set_index("time").sort_index()

def get_tradable_pairs() -> DataFrame:
    try: return read_csv('./exchanges/info/kraken_tradable_pairs.csv')
    except:
        tradable_pairs = requests.get('https://api.kraken.com/0/public/AssetPairs').json()['result']
        raw = []
        for k,v in tradable_pairs.items():
            try:
                raw.append({'pair': k, 'pair_alt': v['altname'], 'pair_ws': v['wsname'], 'left': v['base'], 'right': v['quote'], 'decimal': v['lot_decimals']})
            except:pass
        tradable_pairs = DataFrame(raw)
        tradable_pairs.to_csv('./yuzu/exchanges/info/kraken_tradable_pairs.csv', index=False)
        return tradable_pairs

def get_pair_info(pair: str) -> Dict:
    pairs = get_tradable_pairs()
    ret_pair = pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)].to_dict(orient='records')
    try:
        return ret_pair[0]
    except: print(pair, 'is not a valid pair.')

def validate_pair(pair: str) -> bool:
    pairs = get_tradable_pairs()
    return pair in pairs['pair'].values or pair in pairs['pair_alt'].values

def get_ws_symbol(pair: str) -> str:
    pairs = get_tradable_pairs()
    return pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)]['pair_ws'].iat[0]

def get_left_right(pair: str) -> str:
    pairs = get_tradable_pairs()
    pair_row = pairs[(pairs['pair']==pair)|(pairs['pair_alt']==pair)]
    return pair_row['left'].iat[0], pair_row['right'].iat[0]

# get user balances
def get_balances(include_fiat_values: bool = False, key: str = None, secret: str = None) -> Dict:
    res = __authenticated_request('/0/private/Balance', key=key, secret=secret)
    if include_fiat_values:
        balances = {k: {'amount': float(v), 'value': get_current_value(k, amount=float(v))} for k,v in res.items()}
        total = sum([s['value'] for s in balances.values()])
        return {
            'balances': balances,
            'total': total
        }
    return {k: float(v) for k,v in res.items()}

# get ticker value of asset (safely multiplied by amount if given) (quoted by base, default USD)
def get_current_value(symbol: Optional[str] = None, base: str = 'ZUSD', pair: Optional[str] = None, amount: float = 1):
    if not pair:
        if symbol in ['ETH2.S','ETH2']: # since ETH 2.0 is not tradable
            symbol = 'XETH'
        pair = get_pair_info(symbol+base)["pair_alt"]
    req_str = f'https://api.kraken.com/0/public/Ticker?pair={pair}'
    res = requests.get(req_str).json()
    if res['error']: print(req_str['error'])
    else: return float(res['result'][pair]['c'][0]) * amount

# place buy/sell order
def create_order(side: OrderType, pair: str, amount: Optional[float] = None, test: bool = False, key=None, secret=None) -> bool:
    pair = get_pair_info(pair)
    if not amount: amount = get_balances()[pair['right']] if side == 'buy' else get_balances()[pair['left']]
    if side == 'buy': amount /= get_current_value(pair=pair['pair_alt'])
    amount *= (1-TRADING_FEE)
    amount = safe_round(amount, pair['decimal'])
    print(amount)
    params = {
        "ordertype": "market",
        "type": side,
        "volume": amount,
        "pair": pair['pair_alt'],
        "validate": test
    }
    return __authenticated_request('/0/private/AddOrder', params=params, key=key, secret=secret)

# get open/closed user orders
def get_orders(key: str = None, secret: str = None):
    open = __authenticated_request('/0/private/OpenOrders', params={'trades': True})['open']
    closed = __authenticated_request('/0/private/ClosedOrders', params={'trades': True})['closed']
    return {'open': open, 'closed': closed}

# cancel open order by id
def cancel_order(order_id: str, key: str = None, secret: str = None):
    if order_id == 'all':
        __authenticated_request('/0/private/CancelAll')
    else:
        __authenticated_request('/0/private/CancelOrder', params={'txid': order_id})
