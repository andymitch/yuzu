import requests, datetime, json, pandas as pd, numpy as np
from websocket import WebSocketApp
from threading import Thread
from api import run_api
'''
class Trader:
    def __init__(self, callback_func, left_coin, right_coin='BUSD', paper_wallet_starting_balance=100.0, trading_fee=.001, short_tp=50, short_ma='tema', long_tp=200, long_ma='ema', rsi_tp=28, rsi_lower_outer_bound=30, rsi_lower_inner_bound=40, rsi_upper_outer_bound=70, rsi_upper_inner_bound=60):
        self.callback_func = callback_func
        self.left_coin = left_coin.lower()
        self.right_coin = right_coin.lower()
        self.trading_fee = float(trading_fee)
        self.short_ma = short_ma.lower()
        self.short_tp = int(short_tp)
        self.long_ma = long_ma.lower()
        self.long_tp = int(long_tp)
        self.rsi_tp = int(rsi_tp)
        self.rsi_lower_outer_bound = int(rsi_lower_outer_bound)
        self.rsi_lower_inner_bound = int(rsi_lower_inner_bound)
        self.rsi_upper_outer_bound = int(rsi_upper_outer_bound)
        self.rsi_upper_inner_bound = int(rsi_upper_inner_bound)
        self.side = self.right_coin

        self.klines = self.get_backdata()

        self.ws = WebSocketApp(
            f'wss://stream.binance.com:9443/ws/{self.left_coin}{self.right_coin}@kline_1m',
            on_message = lambda ws, msg: self.on_message(ws, msg),
            on_error = lambda ws, err: print(f"[{self.left_coin}{self.right_coin}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}"),
            on_close = lambda ws: print(f"[{self.left_coin}{self.right_coin}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed"),
            on_open = lambda ws: print(f"[{self.left_coin}{self.right_coin}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")
        )

        self.wallet = {
            self.left_coin: 0.0,
            self.right_coin: float(paper_wallet_starting_balance)
        }

    def get_backdata(self):
        data = json.loads(requests.get('https://api.binance.com/api/v3/klines', params={'symbol': f'{self.left_coin.upper()}{self.right_coin.upper()}', 'interval': '1m', 'limit': 720}).text)
        cols = ['time', 'price', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'trade_count', 'taker_bav', 'taker_qav', 'ignore']
        klines = pd.DataFrame(data, columns=cols).drop(['high', 'low', 'close', 'volume', 'close_time', 'qav', 'trade_count', 'taker_bav', 'taker_qav', 'ignore'], axis=1)
        klines['price'] = pd.to_numeric(klines['price'], downcast='float')
        klines['time'] = klines['time'].apply(lambda t: datetime.datetime.fromtimestamp(float(t/1000)).isoformat())
        klines['short'] = MA(klines['price'], self.short_tp, self.short_ma)
        klines['long'] = MA(klines['price'], self.long_tp, self.long_ma)
        klines['rsi'] = RSI(klines['price'], timeperiod=self.rsi_tp)
        #klines['bband_upper'], _, klines['bband_lower'] = BBANDS(klines['price'], timeperiod=self.short_tp)
        klines[f'{self.left_coin}_balance'] = [None] * len(klines)
        klines[f'{self.right_coin}_balance'] = [None] * len(klines)
        return klines.set_index('time').sort_index()

    def on_message(self, ws, msg):
        data = json.loads(msg)
        symbol = data['s'].lower()
        minute = datetime.datetime.fromtimestamp(float(data['k']['t']/1000)).isoformat()
        price = float(data['k']['o'])
        if not minute in self.klines.index.values:
            self.klines = self.klines.tail(719)
            self.klines = self.klines.append(pd.DataFrame([{'price': price}], index=[minute]))
            self.klines['short'] = MA(self.klines['price'], self.short_tp, self.short_ma)
            self.klines['long'] = MA(self.klines['price'], self.long_tp, self.long_ma)
            self.klines['rsi'] = RSI(self.klines['price'], timeperiod=self.rsi_tp)
            #self.klines['bband_upper'], _, self.klines['bband_lower'] = BBANDS(self.klines['price'], timeperiod=self.short_tp)
            if self.side == self.left_coin:
                if self.ma() == self.right_coin or self.rsi() == self.right_coin:
                    self.order()
            elif self.side == self.right_coin:
                if self.ma() == self.left_coin or self.rsi() == self.left_coin:
                    self.order()
            if self.wallet[self.left_coin] > 0:
                self.klines.at[self.klines.index[-1], f'{self.left_coin}_balance'] = self.wallet[self.left_coin] * self.klines['price'].iat[-1]
            if self.wallet[self.right_coin] > 0:
                self.klines.at[self.klines.index[-1], f'{self.right_coin}_balance'] = self.wallet[self.right_coin]
            print(f"[{self.left_coin}{self.right_coin}] ({datetime.datetime.fromisoformat(minute).isoformat(' ', 'seconds')}) ** minute complete **")

    def order(self):
        if self.side == self.left_coin:
            self.side = self.right_coin
            amount = self.wallet[self.left_coin] * self.klines['price'].iat[-1]
            fee = self.wallet[self.left_coin] * self.klines['price'].iat[-1] * self.trading_fee
            self.wallet[self.right_coin] = amount - fee
            self.wallet[self.left_coin] = 0.0
            self.callback_func(f'{self.left_coin}{self.right_coin}', 'sell')
        elif self.side == self.right_coin:
            self.side = self.left_coin
            amount = self.wallet[self.right_coin] / self.klines['price'].iat[-1]
            fee = self.wallet[self.right_coin] * self.trading_fee / self.klines['price'].iat[-1]
            self.wallet[self.left_coin] = amount - fee
            self.wallet[self.right_coin] = 0.0
            self.callback_func(f'{self.left_coin}{self.right_coin}', 'buy')
'''



from utils import get_exchange, get_keypair, get_backdata, get_strategy, get_strategy_min_ticks, get_strategy_config
from exchanges.PaperWallet import PaperWallet

class Trader:
    wallet = None
    data = None

    def __init__(self,
    pair: str,
    interval: str,
    strategy_name: str,
    exchange_name: str,
    stop_loss: float,
    paper_mode: bool,
    plot_mode: bool = False,
    exchange_key: str = None,
    exchange_secret: str = None):
        self.pair = pair
        self.interval = interval
        self.strategy = get_strategy(strategy_name)
        self.strategy_config = get_strategy_config(strategy_name)
        self.min_ticks = get_strategy_min_ticks(strategy_name)
        self.key, self.secret = get_keypair(exchange_name, exchange_key, exchange_secret)
        self.exchange = get_exchange(exchange_name, self.key, self.secret)
        self.paper_mode = paper_mode
        if self.paper_mode:
            self.wallet = PaperWallet(exchange_name, {self.exchange.left(self.pair): 0.0, self.exchange.right(self.pair): 100.0})
        self.plot_mode = plot_mode
        self.stop_loss = stop_loss
        self.ws = WebSocketApp(
            self.exchange.get_ws_endpoint(pair, interval),
            on_message = lambda ws, msg: self.on_message(ws, json.loads(msg)),
            on_error = lambda ws, err: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}"),
            on_close = lambda ws: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed"),
            on_open = lambda ws: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")
        )

        self.data: pd.DataFrame = self.exchange.get_backdata(pair, interval, max(self.min_ticks, 1000 if self.plot_mode else 0))
        self.data['bought'] = np.nan
        self.data['sold'] = np.nan
        self.data['trade_profit'] = np.nan
        self.update_profit(self.data)

    def toggle_paper_mode(self, carry_over_balance: bool = False):
        if not self.paper_mode:
            if carry_over_balance: self.wallet = PaperWallet({k: v['amount'] for k,v in self.exchange.get_balance().items()})
            else: self.wallet = PaperWallet({self.exchange.right(self.pair): 100.0})
        self.paper_mode = not self.paper_mode

    def set_keypair(self, key, secret):
        self.key, self.secret = get_keypair(self.exchange.name, key, secret)
        self.exchange.set_keypair(key, secret)

    def on_message(self, ws, msg):
        print('HERE')
        self.data, new_tick = self.exchange.condition_data(msg, self.data)
        print('THERE')
        if new_tick:
            self.data = self.data.tail(max(self.min_ticks, 1000 if self.plot_mode else 0))
            self.data = self.strategy(self.data, self.strategy_config)
            if not self.data['buy'].iat[-1] is None:
                if self.order('buy'):
                    data.loc[data.index[-1], 'bought'] = data.close.iat[-1]
            elif not self.data['sell'].iat[-1] is None:
                if self.order('sell'):
                    data.loc[data.index[-1], 'sold'] = data.close.iat[-1]
            self.update_profit()

    def update_profit(self, data):
        if self.paper_mode:
            left = self.exchange.left(self.pair)
            right = self.exchange.right(self.pair)
            price = data.loc[data.index[-1], 'close']
            data.loc[data.index[-1], 'trade_profit'] = self.wallet.get_balance(left, right, price)

    def order(self, side):
        if side == 'buy':
            if self.paper_mode:
                left, right, price = self.exchange.left(self.pair), self.exchange.right(self.pair), self.data.loc[data.index[-1], 'close']
                return self.wallet.buy(left, right, price)
            else:
                success, order = self.exchange.buy(self.pair)
                self.save_order(order)
                return success
        elif side == 'sell':
            if self.paper_mode:
                left, right, price = self.exchange.left(self.pair), self.exchange.right(self.pair), self.data.loc[data.index[-1], 'close']
                return self.wallet.sell(left, right, price)
            else:
                success, order = self.exchange.sell(self.pair)
                self.save_order(order)
                return success

    def save_order(self, order):
        pass # TODO: keep track of active and completed orders

    def run(self):
        while(True):
            self.ws.run_forever()

# TODO: SET STOP_LOSS ORDERS FOR BOTH EXCHANGE AND PAPER WALLET

def main(run_with_api: bool = True):
    trader = Trader('BTCUSDT', '1m', 'macdas_strat', 'BinanceUS', .35, True)
    if run_with_api:
        trader_run = Thread(target=trader.run)
        trader_run.start()
        run_api()
        trader_run.join()
    else: trader.run()

if __name__ == '__main__':
    main(False)