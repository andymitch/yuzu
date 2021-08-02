import requests, datetime, json, pandas as pd, numpy as np
from websocket import WebSocketApp
from threading import Thread
from api import run_api
from utils import get_exchange, get_keypair, get_backdata, get_strategy, get_strategy_min_ticks, get_strategy_config
from exchanges.PaperWallet import PaperWallet

class Trader:
    wallet = None

    def __init__(self,
    pair: str,
    interval: str,
    strategy_name: str,
    exchange_name: str,
    stop_loss: float,
    paper_mode: bool = False,
    plot_mode: bool = False,
    exchange_key: str = None,
    exchange_secret: str = None):
        self.pair = pair
        self.interval = interval
        self.strategy = get_strategy(strategy_name)
        self.strategy_config = get_strategy_config(strategy_name)[interval]
        self.min_ticks = max(get_strategy_min_ticks(strategy_name), 500 if plot_mode else 0)
        self.key, self.secret = get_keypair(exchange_name, exchange_key, exchange_secret)
        self.exchange = get_exchange(exchange_name, self.key, self.secret)
        self.paper_mode = paper_mode
        self.stop_loss = None
        self.stop_loss_at = stop_loss
        if self.paper_mode:
            self.wallet = PaperWallet(exchange_name, {self.exchange.left(self.pair): 0.0, self.exchange.right(self.pair): 100.0})
        self.ws = WebSocketApp(
            self.exchange.get_ws_endpoint(pair, interval),
            on_message = lambda ws, msg: self.on_message(ws, json.loads(msg)),
            on_error = lambda ws, err: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}"),
            on_close = lambda ws: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed"),
            on_open = lambda ws: print(f"[{self.pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")
        )

        self.data: pd.DataFrame = self.exchange.get_backdata(pair, interval, self.min_ticks)
        self.data[['bought','sold','trade_profit','stop_loss','stop_lossed','buy','sell']] = np.nan
        self.data['trade_profit'] = self.wallet.balance[self.exchange.right(self.pair)]

    def toggle_paper_mode(self, carry_over_balance: bool = False):
        if not self.paper_mode:
            if carry_over_balance: self.wallet = PaperWallet({k: v['amount'] for k,v in self.exchange.get_balance().items()})
            else: self.wallet = PaperWallet({self.exchange.right(self.pair): 100.0})
        self.paper_mode = not self.paper_mode

    def set_keypair(self, key, secret):
        self.key, self.secret = get_keypair(self.exchange.name, key, secret)
        self.exchange.set_keypair(key, secret)

    def on_message(self, ws, msg):
        self.data, new_tick = self.exchange.condition_data(msg, self.data)
        if new_tick:
            print('NEW TICK')
            print(self.data.loc[self.data.index[-1], 'low'])
            if (not self.stop_loss is None) and self.data.loc[self.data.index[-1], 'low'] >= self.stop_loss:
                print('stop loss:', self.stop_loss)
                self.data.loc[self.data.index[-1], 'stop_lossed'] = self.stop_loss
                print(2)
                self.order('stop_loss')
                print(3)
            else: print('None stop loss')
            self.data = self.data.tail(self.min_ticks)
            self.data = self.strategy(self.data, self.strategy_config)
            if not np.isnan(self.data.loc[self.data.index[-1], 'buy']):
                if self.order('buy'):
                    self.data.loc[self.data.index[-1], 'bought'] = self.data.loc[self.data.index[-1], 'close']
            elif not np.isnan(self.data.loc[self.data.index[-1], 'sell']):
                if self.order('sell'):
                    self.data.loc[self.data.index[-1], 'sold'] = self.data.loc[self.data.index[-1], 'close']
            self.update_profit()
        else: print('UPDATE TICK')

    def update_profit(self):
        if self.paper_mode:
            left = self.exchange.left(self.pair)
            right = self.exchange.right(self.pair)
            price = self.data.loc[self.data.index[-1], 'close']
            balance = self.wallet.get_balance(left, right, price)
            print('buy',left,right,price,balance)
            self.data.loc[self.data.index[-1], 'trade_profit'] = balance

    def order(self, side):
        if side == 'buy':
            if self.paper_mode:
                left, right, price = self.exchange.left(self.pair), self.exchange.right(self.pair), self.data.loc[self.data.index[-1], 'close']
                self.stop_loss = price * (1-self.stop_loss_at)
                self.data.loc[self.data.index[-1], 'stop_loss'] = self.stop_loss
                return self.wallet.buy(left, right, price)
            else:
                success, order = self.exchange.buy(self.pair)
                self.save_order(order)
                # TODO: open a stop loss sell order once buy order is complete
                return success
        elif side == 'sell':
            if self.paper_mode:
                left, right, price = self.exchange.left(self.pair), self.exchange.right(self.pair), self.data.loc[self.index[-1], 'close']
                self.stop_loss = None
                return self.wallet.sell(left, right, price)
            else:
                success, order = self.exchange.sell(self.pair)
                self.save_order(order)
                return success
        elif side == 'stop_loss':
            if self.paper_mode:
                left, right, price = self.exchange.left(self.pair), self.exchange.right(self.pair), self.stop_loss
                self.stop_loss = None
                return self.wallet.sell(left, right, price)
            else: # TODO: may not be necessary
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
    trader = Trader('BTCUSDT', '1m', 'macdas_strat', 'BinanceUS', .015, paper_mode=True, plot_mode=run_with_api)
    if run_with_api:
        trader_run = Thread(target=trader.run)
        trader_run.start()
        run_api(trader)
        trader_run.join()
    else: trader.run()

if __name__ == '__main__':
    main(True)