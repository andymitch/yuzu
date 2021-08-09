from yuzu.Websocket import CreateWebsocket, Websocket
from pandas import DataFrame, to_numeric, read_csv
from yuzu.utils import since, keypair, safe_round
from urllib.parse import urlencode
from yuzu.types import *
from pytz import reference
import numpy as np
import datetime
import requests
import hashlib
import hmac
import json
import math
import time

# interpret websocket tick for current candle
def __condition_tick(msg: Dict) -> Tuple[str,Row]:
    time = datetime.datetime.fromtimestamp(float(msg['k']['t']/1000)).isoformat()
    return time, {'open': float(msg['k']['o']), 'high': float(msg['k']['h']), 'low': float(msg['k']['l']), 'close': float(msg['k']['c']), 'volume': float(msg['k']['v'])}

def get_websocket(data: DataFrame, pair: str, interval: str, on_tick: Callable) -> Websocket:
    return CreateWebsocket(data, f'wss://stream.binance.us:9443/ws/{pair.lower()}@kline_{interval}', pair, interval, __condition_tick, on_tick)

BASE_URL = 'https://api.binance.us/api/v3/'
TRADING_FEE = 0.001

# get historical OHLCV candles
def get_backdata(pair, interval, ticks) -> DataFrame:
    klines = []
    max_tick_request = 1000
    epoch_to_iso = lambda t: datetime.datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%dT%H:%M:%S')
    cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    drop_cols = ["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    num_cols = ["open", "high", "low", "close", "volume"]
    data = DataFrame(columns=cols)
    if ticks > max_tick_request:
        curr_epoch = int(datetime.datetime.now(tz=reference.LocalTimezone()).timestamp())
        since_epoch = since(interval, ticks, curr_epoch)
        epoch_count = math.ceil(ticks/max_tick_request) + 1
        epochs = np.linspace(since_epoch*1000, curr_epoch*1000, epoch_count, dtype=int)[:-1]
        for epoch in epochs:
            params = {'symbol': pair, 'interval': interval, 'startTime': epoch, 'limit': max_tick_request}
            klines = json.loads(requests.get(BASE_URL + 'klines', params=params).text)
            temp = DataFrame(klines, columns=cols)
            temp['time'] = temp['time'].apply(epoch_to_iso)
            temp = temp.set_index('time')
            data = data.append(temp.loc[temp.index.difference(data.index),:])
        data = data.drop(drop_cols, axis=1)
        data[num_cols] = data[num_cols].apply(to_numeric, axis=1)
    else:
        params = {'symbol': pair, 'interval': interval, 'limit': ticks}
        klines = json.loads(requests.get(BASE_URL + 'klines', params=params).text)
        data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
        data["time"] = data["time"].apply(epoch_to_iso)
        data.set_index("time")
    return data.sort_index()

def __authenticated_request(http_method, endpoint, params={}):
    key, secret = keypair('binanceus')
    def dispatch_request(http_method):
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json;charset=utf-8',
            'X-MBX-APIKEY': key
        })
        return {
            'GET': session.get,
            'DELETE': session.delete,
            'PUT': session.put,
            'POST': session.post,
        }.get(http_method, 'GET')
    query_string = urlencode(params, True)
    query_string = query_string + ('&' if query_string else '') + 'timestamp=' + str(int(1000*time.time()))
    hashed = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = BASE_URL + endpoint + '?' + query_string + '&signature=' + hashed
    params = {'url': url, 'params': {}}
    response = dispatch_request(http_method)(**params)
    return response.json()

# get user account info
def get_account():
    return __authenticated_request('GET', 'account')

def get_value(asset: str, amount: float, pairs, precision: Optional[int] = None):
    c = pairs.loc[pairs['left']==asset, 'curr_price'].values
    if not c:
        return amount
    if not precision:
        precision = pairs.loc[pairs['left']==asset, 'right_precision'].values[0]
    return round(amount * pairs.loc[pairs['left']==asset, 'curr_price'].values[0], precision)

# get available account balance for specified asset
def get_balances() -> Dict[str,Dict[str,float]]:
    balances: Dict[str,float] = {b['asset']: float(b['free']) for b in get_account()['balances'] if float(b['free']) > 0}
    pairs = get_pair_info([k+'USD' for k in balances.keys() if k != 'USD'])
    balances = {k: {'amount': v, 'value': get_value(k, v, pairs)} for k,v in balances.items() if v > 0}
    return {'balances': balances, 'total': sum([v['value'] for v in balances.values()])}


def get_pair(pair: str) -> Dict:
    pairs = get_pair_info()
    try:
        return pairs[pairs['pair']==pair].to_dict(orient='records')[0]
    except: print(pair, 'is not a valid pair.')

def get_pair_info(pair_or_pairs: Optional[Union[str, List[str]]] = None):
    endpoint = 'exchangeInfo'
    if pair_or_pairs:
        if isinstance(pair_or_pairs, str): endpoint += ('?symbol='+pair_or_pairs)
        else: endpoint += ('?symbols=['+','.join(['\"'+a+'\"' for a in pair_or_pairs])+']')
    #print(endpoint)
    exchange_info = requests.get(BASE_URL + endpoint).json()
    #print(exchange_info)
    f = open('./pair_stuff.json', 'w')
    f.write(json.dumps(exchange_info, indent=2))
    f.close()
    prices = {p['symbol']: float(p['price']) for p in requests.get(BASE_URL + 'ticker/price').json()}
    return DataFrame([{
        'pair': s['symbol'],
        'left': s['baseAsset'],
        'right': s['quoteAsset'],
        'left_min': float(next((f for f in s['filters'] if f['filterType'] == 'LOT_SIZE'), None)['minQty']),
        'right_min': float(next((f for f in s['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)['minNotional']),
        'left_precision': f"{float(s['filters'][2]['stepSize']):g}"[::-1].find('.'),
        'right_precision': int(s['quoteAssetPrecision']),
        'curr_price': prices[s['symbol']]
    } for s in exchange_info['symbols']])

# place market order
def create_order(side: OrderType, pair: str, amount: Optional[float] = None, test: bool = False) -> Optional[Dict]:
    endpoint = 'order/test' if test else 'order'
    pair = get_pair(pair)
    params = {
        'symbol': pair['pair'],
        'side': side.upper(),
        'type': 'MARKET'
    }
    balances = get_balances()['balances']
    print(pair)
    if side == 'buy':
        if not amount:
            amount = safe_round(balances[pair['right']]['amount'] * (1-TRADING_FEE), pair['right_precision'])
        if amount < pair['right_min']:
            print(amount, '<' ,pair['right_min'])
            return
        params['quoteOrderQty'] = safe_round(amount, pair['right_precision'])
    else: # sell
        if not amount:
            amount = safe_round(balances[pair['left']]['amount'] * (1-TRADING_FEE), pair['left_precision'])
        if amount < pair['left_min']:
            print(amount, '<' ,pair['left_min'])
            return
        params['quantity'] = safe_round(amount, pair['left_precision'])
    print(params)
    return __authenticated_request('POST', endpoint, params)

def get_orders():
    return __authenticated_request('GET', 'openOrders')

def cancel_order(order_id: Optional[str] = None, symbol: Optional[str] = None):
    if not order_id:
        return __authenticated_request('DELETE', 'openOrders')
    else:
        return __authenticated_request('DELETE', 'order', {'symbol': symbol, 'orderId': order_id})
 