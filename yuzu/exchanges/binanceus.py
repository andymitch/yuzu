import requests
from urllib.parse import urlencode
import hmac, hashlib, datetime, math, json
import traceback
from numpy import linspace
from pandas import to_numeric
from time import time
from pytz import reference
from ..utils.utils import since
from ..utils.types import *

ROOT_URL = 'https://api.binance.us/api/v3/'

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
    max_tick_request = 1000
    epoch_to_iso = lambda t: datetime.datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%d %H:%M:%S')
    cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    drop_cols = ["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    num_cols = ["open", "high", "low", "close", "volume"]
    data = DataFrame(columns=cols)
    if ticks > max_tick_request:
        curr_epoch = int(datetime.datetime.now(tz=reference.LocalTimezone()).timestamp())
        since_epoch = since(interval, ticks, curr_epoch)
        epoch_count = math.ceil(ticks/max_tick_request) + 1
        epochs = linspace(since_epoch*1000, curr_epoch*1000, epoch_count, dtype=int)[:-1]
        for epoch in epochs:
            params = {'symbol': symbol, 'interval': interval, 'startTime': epoch, 'limit': max_tick_request}
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

def get_available_pairs():
    exchange_info = requests.get(ROOT_URL + 'exchangeInfo').json()
    prices = {p['symbol']: float(p['price']) for p in requests.get(ROOT_URL + 'ticker/price').json()}
    pair_list = [s['symbol'] for s in exchange_info['symbols']]
    return pair_list

def authenticate(key: str, secret: str) -> bool:
    return __authenticated_request('GET', 'account', key, secret).status_code == 200

# TODO: create_order

# TODO: get_orders

# TODO: cancel_order

# TODO: buy

# TODO: sell


'''
from websocket import WebSocketApp
from urllib.parse import urlencode
from flask import Flask, request
from pandas import to_numeric
from time import sleep, time
import numpy as np
import traceback
import datetime
import requests
import hashlib
import hmac
import json
import sys

from yaza.client import client_app, page_not_found
from yaza.optimize import optimize, backtest
from yaza.paperwallet import PaperWallet
from yaza.plot import plot
from yaza.utils.types import *
from yaza.utils import *


BASE_URL = 'https://api.binance.us/api/v3/'
TRADING_FEE = 0.001

# Binance.US Specific Websocket
class Websocket:
    def __init__(self, pair: str, interval: str, callback: Callable, tld: str = 'us'):
        self.ws = WebSocketApp(
            f"wss://stream.binance.{tld}:9443/ws/{pair.lower()}@kline_{interval}",
            on_message = lambda ws, msg: self.on_message(msg, callback),
            on_error = lambda ws, err: print(f"[{datetime.datetime.now().isoformat(' ', 'seconds')}] {err}"),
            on_close = lambda ws: print(f"[{datetime.datetime.now().isoformat(' ', 'seconds')}] websocket closed"),
            on_open = lambda ws: print(f"[{datetime.datetime.now().isoformat(' ', 'seconds')}] websocket opened")
        )

    thread = None
    keep_running = False

    def run(self):
        self.keep_running = True
        while(self.keep_running):
            self.ws.run_forever()

    def async_start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.keep_running = False
        self.ws.close()

    def on_message(self, msg, callback):
        try:
            msg = json.loads(msg)
            time = datetime.datetime.fromtimestamp(float(msg['k']['t']/1000)).strftime('%Y-%m-%d %H:%M:%S')
            row = {'time': time, 'open': float(msg['k']['o']), 'high': float(msg['k']['h']), 'low': float(msg['k']['l']), 'close': float(msg['k']['c']), 'volume': float(msg['k']['v'])}
            callback(row)
        except:
            print('** something went wrong **')
            print(traceback.print_exc())


# get historical OHLCV candles
def get_backdata(pair: Pair, interval: str, ticks: int) -> DataFrame:
    klines = []
    max_tick_request = 1000
    epoch_to_iso = lambda t: datetime.datetime.fromtimestamp(float(t / 1000),tz=reference.LocalTimezone()).strftime('%Y-%m-%d %H:%M:%S')
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
            klines = json.loads(requests.get('https://api.binance.us/api/v3/' + 'klines', params=params).text)
            temp = DataFrame(klines, columns=cols)
            temp['time'] = temp['time'].apply(epoch_to_iso)
            temp = temp.set_index('time')
            temp = temp.drop_duplicates()
            data = data.append(temp.loc[temp.index.difference(data.index),:])
        data = data.drop(drop_cols, axis=1)
        data[num_cols] = data[num_cols].apply(to_numeric, axis=1)
    else:
        params = {'symbol': pair, 'interval': interval, 'limit': ticks}
        klines = json.loads(requests.get(BASE_URL + 'klines', params=params).text)
        data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
        data["time"] = data["time"].apply(epoch_to_iso)
        data = data.set_index("time")
    return data.loc[~(data.index.duplicated(False))].sort_index()


# get all pairs info
def get_all_pairs(symbol_s: Optional[Union[str, List[str]]] = None) -> Union[Pair, List[Pair]]:
    try:
        endpoint = 'exchangeInfo'
        if symbol_s:
            if isinstance(symbol_s, str): endpoint += ('?symbol='+symbol_s)
            else: endpoint += ('?symbols=['+','.join(['\"'+a+'\"' for a in symbol_s])+']')
        exchange_info = requests.get(BASE_URL + endpoint).json()
        prices = {p['symbol']: float(p['price']) for p in requests.get(BASE_URL + 'ticker/price').json()}
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

# get Pair object given symbol
def get_pair(symbol: str) -> Pair:
    try: return get_all_pairs(symbol)
    except: print(symbol, 'is not a valid pair.')


class Exchange:
    __key, __secret = None, None
    def __init__(self, strategy: Callable[[DataFrame,dict],DataFrame], config: dict, key: Optional[str] = None, secret: Optional[str] = None):
        self.strategy = strategy
        self.config = config
        if key and secret:
            self.__key = key,
            self.__secret = secret

    ws = None
    data = {}
    CURR_ORDER_ID = None

    # optimize strategy config using data from Binance
    def optimize(self,
        symbol: str,
        interval: str,
        strategy: Callable[[DataFrame, dict], DataFrame],
        config_range: dict,
    ) -> dict:
        data = get_backdata(symbol, interval, min_ticks=5000)
        return optimize(data, strategy, config_range)

    # backtest strategy+config using data from Binance
    def backtest(self,
        symbol: str,
        interval: str,
        strategy: Callable[[DataFrame, dict], DataFrame],
        config: dict,
        plot: bool = False
    ) -> DataFrame:
        data = get_backdata(symbol, interval, min_ticks=1000)
        return backtest(data, config, 0.001, plot)

    # make private api request
    def __authenticated_request(self, http_method, endpoint, params={}):
        def dispatch_request(http_method):
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json;charset=utf-8',
                'X-MBX-APIKEY': self.__key
            })
            return {
                'GET': session.get,
                'DELETE': session.delete,
                'PUT': session.put,
                'POST': session.post,
            }.get(http_method, 'GET')
        query_string = urlencode(params, True)
        query_string = query_string + ('&' if query_string else '') + 'timestamp=' + str(int(1000*time()))
        hashed = hmac.new(self.__secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        url = BASE_URL + endpoint + '?' + query_string + '&signature=' + hashed
        params = {'url': url, 'params': {}}
        response = dispatch_request(http_method)(**params)
        return response.json()

    # create any possible type of order
    def create_order(self,
        symbol: str,
        side: str,
        type: str,
        quantity: Optional[float] = None,
        quoteOrderQty: Optional[float] = None,
        price: Optional[float] = None,
        stopPrice: Optional[float] = None,
        test: bool = False
    ):
        pair = get_pair(symbol)
        endpoint = 'order/test' if test else 'order'
        params = {
            'symbol': pair['pair'],
            'side': side.upper(),
            'type': type
        }
        if quantity: params['quantity'] = safe_round(quantity * (1-TRADING_FEE), pair['left_precision'])
        if quoteOrderQty: params['quoteOrderQty'] = safe_round(quoteOrderQty * (1-TRADING_FEE), pair['right_precision'])
        self.CURR_ORDER_ID = self.__authenticated_request('POST', endpoint, params)['orderId']
        print(f'** PLACED ORDER ({params}) **')

    # get order by self.CURR_ORDER_ID
    def get_curr_order(self, data: DataFrame) -> Optional[dict]:
        if not self.CURR_ORDER_ID: return None
        try:
            order = self.__authenticated_request('GET', 'allOrders', {'orderId': self.CURR_ORDER_ID})[0]
            if order['status'] == 'FILLED':
                if order['side'] == 'BUY':
                    data.loc[data.index[-1], "bought"] = float(order['price'])
                else:
                    data.loc[data.index[-1], "sold"] = float(order['price'])
            elif not order['status'] in ['NEW','PARTIALLY_FILLED']:
                self.CURR_ORDER_ID = None # order failed
                return None
            return order
        except:
            self.CURR_ORDER_ID = None # order diesn't exist
            return None

    # cancel order by self.CURR_ORDER_ID
    def cancel_curr_order(self):
        self.__authenticated_request('DELETE', 'order', {'orderId': self.CURR_ORDER_ID})
        self.CURR_ORDER_ID = None

    # async thread for buying
    def __buy_thread(self, data, symbol):
        pair = get_pair(symbol)
        balances = self.get_curr_balance()
        price = pair.curr_price * (1+self.config['stop_limit_buy'])
        qty = balances[pair.right] / price
        if qty < pair['left_min']: return
        self.create_order(symbol, 'BUY', 'STOP_LOSS', quantity=qty, price=price)
        while(True):
            order = self.get_curr_order(data)
            if (not order) or order['side']=='SELL': return # buy order was cancelled
            if order['status'] in ['NEW','PARTIALLY_FILLED']: sleep(10)
            elif order['status'] == 'FILLED':
                data.loc[data.index[-1], "bought"] = float(order['price'])
                pair = get_pair(symbol)
                balances = self.get_curr_balance()
                price = pair.curr_price * (1-self.config['stop_limit_loss'])
                qty = balances[pair.left]
                if qty < pair['left_min']: return
                self.create_order(symbol, 'SELL', 'STOP_LOSS', quantity=qty, price=price)
                return

    # buy, then stop_loss after fill
    def async_buy(self, data, symbol):
        order = self.get_curr_order(data)
        pair = get_pair(symbol)
        if order:
            if order['side']=='SELL' or pair.curr_price < order['price']:
                self.cancel_curr_order()
            else: return # better buy order exists
        thread = Thread(target=self.__buy_thread, args=[data, symbol])
        thread.start()

    # sell
    def sell(self, data, symbol):
        order = self.get_curr_order(data)
        pair = get_pair(symbol)
        if order:
            if order['side']=='BUY' or pair.curr_price > order['price']:
                self.cancel_curr_order()
            else: return # better sell order exists
        balances = self.get_curr_balance()
        price = pair.curr_price * (1-self.config['stop_limit_sell'])
        qty = balances[pair.left]
        if qty < pair['left_min']: return
        self.create_order(symbol, 'SELL', 'STOP_LOSS', quantity=qty, price=price)

    # get current balance of all assets as dict
    def get_curr_balance(self) -> Dict[str,float]:
        return {b['asset']: float(b['free']) for b in self.__authenticated_request('GET', 'account')['balances'] if float(b['free']) > 0}

    # get total balance of all assets in USD as float
    def quote_curr_balance(self, symbol: Optional[str] = None):
        balances = self.get_curr_balance()
        if symbol:
            pair = get_pair(symbol)
            return balances[pair.right] + (balances[pair.left] * pair.curr_price)
        usd = balances.pop('USD')
        others = [get_pair(k+'USD').curr_price * v for k,v in balances.items()]
        return usd + sum(others)

    # for each websocket ping, update on new tick
    def on_message(self, symbol, row):
        try:
            pair = get_pair(symbol)
            time = row.pop('time')
            if time in self.data.index.values:
                self.data.loc[time, row.keys()] = row.values()
            else:
                print(f'[{time}] {row}')
                self.data = self.data.append(DataFrame(row, index=[time])).tail(max(500,self.config['min_ticks']))
                self.data = self.strategy(self.data, self.config)
                if self.paper_wallet:
                    self.data = self.paper_wallet.update(self.data, pair.left, pair.right)
                    self.data.loc[self.data.index[-1], "balance"] = self.paper_wallet.get_balance(pair.left, pair.right, pair.curr_price)
                else:
                    if self.data['buy'].iat[-1]:
                        self.async_buy(self.data, symbol)
                    elif self.data['sell'].iat[-1]:
                        self.sell(self.data, symbol)
                    self.data.loc[self.data.index[-1], "balance"] = self.quote_curr_balance(symbol)
        except:
            print('** BAD TICK **')
            print(traceback.print_exc())

    # async run api function
    def api(self):
        app = Flask(__name__)

        @app.route("/balance", methods=['GET'])
        def get_balance():
            if self.paper_wallet: return self.paper_wallet.balance
            return self.get_balances()

        @app.route("/data", methods=['GET'])
        def get_data():
            return self.data.to_json()

        @app.route("/curr_order", methods=['GET'])
        def get_curr_order():
            if self.paper_wallet:
                return 'TODO: get current paper order'
            return self.get_curr_order(self.data)

        @app.route("/paper_wallet", methods=['GET', 'POST'])
        def get_set_paper_wallet():
            if request.method == 'POST':
                for k,v in request.form:
                    if k == 'verbose': self.paper_wallet.verbose = bool(v)
                    elif k == 'debug': self.paper_wallet.debug = bool(v)
                    elif k == 'balance': self.paper_wallet.balance = json.loads(v)
                    return
            elif request.method == 'GET':
                return {
                    'balance': self.paper_wallet.balance,
                    'stop_buy': self.paper_wallet.stop_buy,
                    'stop_sell': self.paper_wallet.stop_sell,
                    'stop_loss': self.paper_wallet.stop_loss,
                    'open_trade': self.paper_wallet.open_trade
                }

        @app.route("/config", methods=['GET', 'POST'])
        def get_set_config():
            if request.method == 'GET':
                return self.config
            elif request.method == 'POST':
                self.config = json.loads(request.form['config'])
                self.paper_wallet.stop_limit_buy = self.config['stop_limit_buy']
                self.paper_wallet.stop_limit_sell = self.config['stop_limit_sell']
                self.paper_wallet.stop_limit_loss = self.config['stop_limit_loss']
                return

        @app.route("/plot", methods=['GET'])
        def get_plot():
            return plot(self.data, as_html=True)

        @app.route("/", methods=['GET'])
        def get_app():
            plot_html = plot(self.data, as_html=True, embed=True)
            balance = self.paper_wallet.balance if self.paper_wallet else self.get_curr_balance()
            return client_app(balance, plot_html)

        @app.errorhandler(404)
        def page_not_found(error):
            return page_not_found()

        if sys.platform in ['linux','linux2']: app.run(host='0.0.0.0', port=5000)
        elif sys.platform == 'darwin': app.run(port=8000)

    api_thread = None
    # start websocket, api, and live trading
    def start_trading(self, symbol: str, interval: str):
        pair = get_pair(symbol)
        if not (self.__key or self.__secret):
            self.paper_wallet = PaperWallet(self.config, init_balance={pair.left: 0.0, pair.right: 100.0}, init_pairs=[pair.left+pair.right], verbose=True, debug=True)
        self.data = get_backdata(symbol, interval, max(100, self.config['min_ticks']))
        self.data = self.strategy(self.data, self.config)
        balance = self.quote_curr_balance(symbol) if self.__key and self.__secret else self.paper_wallet.get_balance(pair.left, pair.right, pair.curr_price)
        self.data[['bought','sold','stop_lossed','balance']] = [None, None, None, balance]
        self.ws = Websocket(symbol, interval, lambda row: self.on_message(symbol, row))
        self.ws.async_start()
        self.api_thread = KillableThread(target=self.api)
        self.api_thread.start()

    # stop websocket, api, and live trading
    def stop_trading(self, symbol: str, selloff: bool = False):
        self.api_thread.kill()
        self.api_thread.join()
        self.ws.stop()
        order = self.get_curr_order(self.data)
        if order:
            self.cancel_curr_order()
            if selloff and order['side']=='SELL':
                pair = get_pair(order['symbol'])
                self.create_order(pair.symbol, 'SELL', 'MARKET', self.get_curr_balance()[pair.left])

'''