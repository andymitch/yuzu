from websocket import WebSocketApp
from pandas import DataFrame, to_numeric, read_csv
from yuzu.utils import *
from yuzu.exchanges import Exchange
from urllib.parse import urlencode
from threading import Thread
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
from flask import Flask
from yuzu.PaperWallet import PaperWallet
from plotly.io import to_html

from pyngrok import ngrok
from yuzu.utils import update_url


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
        klines = json.loads(requests.get('https://api.binance.us/api/v3/' + 'klines', params=params).text)
        data = DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
        data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(to_numeric, axis=1)
        data["time"] = data["time"].apply(epoch_to_iso)
        data = data.set_index("time")
    return data.loc[~(data.index.duplicated(False))].sort_index()


class BinanceUS():
    BASE_URL = 'https://api.binance.us/api/v3/'
    TRADING_FEE = 0.001

    def __init__(self,
        config: dict,
        paper_mode: bool = True,
        key: Optional[str] = None,
        secret: Optional[str] = None
    ):
        if paper_mode:
            self.paper_wallet = PaperWallet(config['stop_limit_buy'], config['stop_limit_sell'], config['stop_limit_loss'], self.TRADING_FEE, {}, [])
        else:
            self.stop_limit_buy = config['stop_limit_buy']
            self.stop_limit_sell = config['stop_limit_sell']
            self.stop_limit_loss = config['stop_limit_loss']
        self.__key = key
        self.__secret = secret
        self.ws = None
        self.keep_running_ws = None
        self.ws_tread = None
        self.api_thread = None
        self.strategy = None
        self.strategy_config = None
        self.strategy_plot = None
        self.min_ticks = None


    ############################ WEBSOCKET

    # on new interval, condition data and check for a signal
    def on_tick(self, pair: dict):
        self.data = self.strategy(self.data, self.strategy_config)
        if self.paper_wallet:
            self.paper_wallet.update(self.data, pair['left'], pair['right'], verbose=True)
        elif self.data['buy'].iat[-1]:
            if self.create_order('buy', pair):
                self.data.loc[self.data.index[-1], "bought"] = self.data.loc[self.data.index[-1], "close"]
        elif self.data['sell'].iat[-1]:
            if self.create_order('sell', pair):
                self.data.loc[self.data.index[-1], "sold"] = self.data.loc[self.data.index[-1], "close"]
        self.data.loc[self.data.index[-1], "trade_profit"] = self.get_curr_balance(pair)

    # on every ping
    def on_message(self, msg: str, pair: dict) -> None:
        msg = json.loads(msg)
        time = datetime.datetime.fromtimestamp(float(msg['k']['t']/1000)).isoformat()
        row = {'open': float(msg['k']['o']), 'high': float(msg['k']['h']), 'low': float(msg['k']['l']), 'close': float(msg['k']['c']), 'volume': float(msg['k']['v'])}
        if time and row:
            if time in self.data.index.values:
                self.data.loc[time, row.keys()] = row.values()
            else:
                print(time, row)
                self.data = self.data.append(DataFrame(row, index=[time]))
                self.data = self.data.tail(max(500, self.min_ticks))
                self.on_tick(pair)

    # async run and keep ws alive function
    def run_ws(self):
        self.keep_running_ws = True
        while(self.keep_running_ws):
            self.ws.run_forever()

    # async run api function
    def run_api(self):
        url = ngrok.connect(8000).public_url
        update_url(url)

        app = Flask('yuzu')
        @app.route("/balance")
        def get_balance():
            if self.paper_wallet: return self.paper_wallet.balance
            return self.get_balances()
        @app.route("/data")
        def get_data():
            return self.data.to_json()
        @app.route("/plot")
        def get_plot():
            return to_html(self.strategy_plot(self.data, trade_mode='live')) if self.strategy_plot else {}
        app.run(port=8000)

    # start trader including ws (input) and api (output)
    def async_start(self, pair, interval, strategy, config, min_ticks=100, plot=None):
        pair = self.get_pair(pair)
        if self.paper_wallet:
            self.paper_wallet.fund(pair['left'], 0.0)
            self.paper_wallet.fund(pair['right'], 100.0)
            self.paper_wallet.add_pair(pair['pair'])
        self.min_ticks = min_ticks
        self.strategy = strategy
        self.strategy_config = config
        self.strategy_plot = plot
        self.data = self.strategy(get_backdata(pair['pair'], interval, max(100, self.min_ticks)), self.strategy_config)
        self.data['bought'] = None
        self.data['sold'] = None
        self.data['stop_loss'] = None
        self.data['stop_lossed'] = None
        self.data['trade_profit'] = self.get_curr_balance(pair)
        self.ws = WebSocketApp(
            f"wss://stream.binance.us:9443/ws/{pair['pair'].lower()}@kline_{interval}",
            on_message = lambda ws, msg: self.on_message(msg, pair),
            on_error = lambda ws, err: print(f"[{pair['pair']}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}"),
            on_close = lambda ws: print(f"[{pair['pair']}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed"),
            on_open = lambda ws: print(f"[{pair['pair']}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")
        )
        self.ws_thread = Thread(target=self.run_ws)
        self.ws_thread.start()
        self.api_thread = KillableThread(target=self.run_api)
        self.api_thread.start()

    # stop trader
    def async_stop(self):
        self.keep_running_ws = False
        self.ws.close()
        self.api_thread.kill()
        self.api_thread.join()
        self.ws_thread.join()


    ############################ GET USER AND EXCHANGE INFO

    # make private api request
    def __authenticated_request(self, http_method, endpoint, params={}):
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
        url = self.BASE_URL + endpoint + '?' + query_string + '&signature=' + hashed
        params = {'url': url, 'params': {}}
        response = dispatch_request(http_method)(**params)
        return response.json()

    # get user account info
    def get_account(self):
        return self.__authenticated_request('GET', 'account')

    # ???
    def get_value(self, asset: str, amount: float, pairs, precision: Optional[int] = None):
        c = pairs.loc[pairs['left']==asset, 'curr_price'].values
        if not c:
            return amount
        if not precision:
            precision = pairs.loc[pairs['left']==asset, 'right_precision'].values[0]
        return round(amount * pairs.loc[pairs['left']==asset, 'curr_price'].values[0], precision)

    # get available account balances for all assets and their total value quoted in USD
    def get_balances(self) -> Dict[str,Dict[str,float]]:
        balances: Dict[str,float] = {b['asset']: float(b['free']) for b in self.get_account()['balances'] if float(b['free']) > 0}
        pairs = self.get_pair_info([k+'USD' for k in balances.keys() if k != 'USD'])
        balances = {k: {'amount': v, 'value': self.get_value(k, v, pairs)} for k,v in balances.items() if v > 0}
        return {'balances': balances, 'total': sum([v['value'] for v in balances.values()])}

    # get current quoted balance value
    def get_curr_balance(self, pair):
        pair = self.get_pair(pair)
        if not self.paper_wallet:
            balances = self.get_balances()['balances']
            left, right = balances[pair['left']]['amount'], balances[pair['right']]['amount']
            return (left * pair['curr_price']) + right
        print(pair)
        return self.paper_wallet.get_balance(pair['left'], pair['right'], pair['curr_price'])

    # get info for given pair string
    def get_pair(self, pair: str) -> Dict:
        print(pair)
        pairs = self.get_pair_info()
        try:
            return pairs[pairs['pair']==pair].to_dict(orient='records')[0]
        except: print(pair, 'is not a valid pair.')

    # get info for all pairs as a DataFrame
    def get_pair_info(self, pair_or_pairs: Optional[Union[str, List[str]]] = None) -> DataFrame:
        endpoint = 'exchangeInfo'
        if pair_or_pairs:
            if isinstance(pair_or_pairs, str): endpoint += ('?symbol='+pair_or_pairs)
            else: endpoint += ('?symbols=['+','.join(['\"'+a+'\"' for a in pair_or_pairs])+']')
        exchange_info = requests.get(self.BASE_URL + endpoint).json()
        f = open('./pair_stuff.json', 'w')
        f.write(json.dumps(exchange_info, indent=2))
        f.close()
        prices = {p['symbol']: float(p['price']) for p in requests.get(self.BASE_URL + 'ticker/price').json()}
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


    ############################ ORDERS

    # place market order
    def create_order(self, side: OrderType, pair: str, amount: Optional[float] = None, test: bool = False) -> Optional[Dict]:
        pair = self.get_pair(pair)
        endpoint = 'order/test' if test else 'order'
        params = {
            'symbol': pair['pair'],
            'side': side.upper(),
            'type': 'MARKET'
        }
        balances = self.get_balances()['balances']
        if side == 'buy':
            if not amount:
                amount = safe_round(balances[pair['right']]['amount'] * (1-self.TRADING_FEE), pair['right_precision'])
            if amount < pair['right_min']:
                print(amount, '<' ,pair['right_min'])
                return False
            params['quoteOrderQty'] = safe_round(amount, pair['right_precision'])
        else: # sell
            if not amount:
                amount = safe_round(balances[pair['left']]['amount'] * (1-self.TRADING_FEE), pair['left_precision'])
            if amount < pair['left_min']:
                print(amount, '<' ,pair['left_min'])
                return False
            params['quantity'] = safe_round(amount, pair['left_precision'])
        print('params:', params)
        try:
            return self.__authenticated_request('POST', endpoint, params)['status'] == 'FILLED'
        except: return False

    # get all current open orders
    def get_orders(self):
        return self.__authenticated_request('GET', 'openOrders')

    # cancel order by id
    def cancel_order(self, order_id: Optional[str] = None, symbol: Optional[str] = None):
        if not order_id:
            return self.__authenticated_request('DELETE', 'openOrders')
        else:
            return self.__authenticated_request('DELETE', 'order', {'symbol': symbol, 'orderId': order_id})

# TODO update BinanceUS.create_order
'''
reference PaperWallet.
each buy and sell should be a stop limit order.

if a new buy/sell signal comes in,
check for existing buy/sell order:

if buy signal and existing buy order,
if signal lower than order, cancel order and order signal.
if sell signal and existing sell order,
if signal higher than order, cancel order and order signal.

if buy signal and existing sell order,
cancel sell order.
if sell signal and existing buy order,
cancel buy order.
'''