from ..websocket import WebSocket
from ..types import Pair
import requests
import traceback
import datetime
from pytz import reference
import math
from numpy import linspace
import json
from pandas import DataFrame, to_numeric
from urllib.parse import urlencode
import hmac
from ..paperwallet import PaperWallet
from ..utils import since
from time import time
import hashlib

def get_websocket():
    pass # TODO: get_websocket

ROOT_URL = 'https://api.binance.com/api/v3/'

def get_all_pairs(symbol_s: Optional[Union[str, List[str]]] = None) -> Union[Pair, List[Pair]]:
    try:
        endpoint = 'exchangeInfo'
        if symbol_s:
            if isinstance(symbol_s, str): endpoint += ('?symbol='+symbol_s)
            else: endpoint += ('?symbols=['+','.join(['\"'+a+'\"' for a in symbol_s])+']')
        exchange_info = requests.get(ROOT_URL + endpoint).json()
        prices = {p['symbol']: float(p['price']) for p in requests.get(ROOT_URL + 'ticker/price').json()}
        pair_list = [Pair(
            symbol=s['symbol'],
            left=s['baseAsset'],
            right=s['quoteAsset'],
            left_min=float(next((f for f in s['filters'] if f['filterType'] == 'LOT_SIZE'), None)['minQty']),
            right_min=float(next((f for f in s['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)['minNotional']),
            left_prec=f"{float(s['filters'][2]['stepSize']):g}"[::-1].find('.'),
            right_prec=int(s['quoteAssetPrecision']),
            curr_price=prices[s['symbol']]
        ) for s in exchange_info['symbols']]
        if symbol_s and isinstance(symbol_s, str):
            return pair_list[0]
        return pair_list
    except:
        print('** FAILED TO GET ALL PAIRS **')
        print(traceback.print_exc())

def get_pair(symbol: str):
    try: return get_all_pairs(symbol)
    except: print(symbol, 'is not a valid pair.')

def get_backdata(symbol: str, interval: str, ticks: int) -> DataFrame:
    klines = []
    MAX_TICK_REQUEST = 1000
    epoch_to_iso = lambda t: datetime.datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%d %H:%M:%S')
    cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    drop_cols = ["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    num_cols = ["open", "high", "low", "close", "volume"]
    data = DataFrame(columns=cols)
    if ticks > MAX_TICK_REQUEST:
        curr_epoch = int(datetime.datetime.now(tz=reference.LocalTimezone()).timestamp())
        since_epoch = since(interval, ticks, curr_epoch)
        epoch_count = math.ceil(ticks/MAX_TICK_REQUEST) + 1
        epochs = linspace(since_epoch*1000, curr_epoch*1000, epoch_count, dtype=int)[:-1]
        for epoch in epochs:
            params = {'symbol': symbol, 'interval': interval, 'startTime': epoch, 'limit': MAX_TICK_REQUEST}
            klines = json.loads(requests.get(ROOT_URL + 'klines', params=params).text)
            temp = DataFrame(klines, columns=cols)
            temp['time'] = temp['time'].apply(epoch_to_iso)
            temp = temp.set_index('time')
            temp = temp.drop_duplicates()
            data = data.append(temp.loc[temp.index.difference(data.index),:])
        data = data.drop(drop_cols, axis=1)
        data[num_cols] = data[num_cols].apply(to_numeric, axis=1)
    else:
        params = {'symbol': symbol, 'interval': interval, 'limit': ticks}
        klines = json.loads(requests.get(ROOT_URL + 'klines', params=params).text)
        data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
        data["time"] = data["time"].apply(epoch_to_iso)
        data = data.set_index("time")
    if 'time' in data.columns: data = data.drop('time', axis=1)
    return data.loc[~(data.index.duplicated(False))].sort_index()

def __authenticated_request(http_method, endpoint, key, secret, params={}):
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
    query_string = query_string + ('&' if query_string else '') + 'timestamp=' + str(int(1000*time()))
    hashed = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = ROOT_URL + endpoint + '?' + query_string + '&signature=' + hashed
    params = {'url': url, 'params': {}}
    return dispatch_request(http_method)(**params)

def get_available_pairs(tld: str):
    exchange_info = requests.get(ROOT_URL + 'exchangeInfo').json()
    prices = {p['symbol']: float(p['price']) for p in requests.get(ROOT_URL + 'ticker/price').json()}
    pair_list = [s['symbol'] for s in exchange_info['symbols']]
    return pair_list

def authenticated(key: str, secret: str) -> bool:
    return __authenticated_request('GET', 'account', key, secret).status_code == 200

class BinanceClient:
    def __init__(self, key=None, secret=None):
        self.paper_mode = not authenticated(key, secret)
        if self.paper_mode: self.paper_wallet = PaperWallet() # TODO: refactor so PaperWallet is okay with no params
        self.__key = key
        self.__secret = secret
    # TODO: BinanceClient
