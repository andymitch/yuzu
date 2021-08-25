from websocket import WebSocketApp
from yuzu.types import *
from pandas import DataFrame
from threading import Thread
import datetime
import json
import time

class Websocket:
    def __init__(self,
        data: DataFrame,
        url: str,
        pair: str,
        interval: str,
        condition_tick: Callable[any, Tuple[Optional[str], Optional[Row]]],
        on_tick: Callable,
        send_msg: Optional[dict] = None
    ):
        self.data = data
        self.url = url
        self.pair = pair
        self.interval = interval
        self.on_tick = on_tick
        self.condition_tick = condition_tick
        self.send_msg = send_msg
        self.ws = WebSocketApp(
            url,
            on_message = lambda ws, msg: self.on_message(msg),
            on_error = lambda ws, err: print(f"[{pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}"),
            on_close = lambda ws: print(f"[{pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed"),
            on_open = lambda ws: print(f"[{pair}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")
        )
        self.keep_running = None

    def on_message(self, msg) -> None:
        time, row = self.condition_tick(json.loads(msg))
        if time and row:
            if time in self.data.index.values:
                print('update tick')
                self.data.loc[time, row.keys()] = row.values()
            else:
                print('new tick')
                self.data = self.data.append(DataFrame(row, index=[time]))
                self.data = self.on_tick(self.data)
                print(self.data.columns)

    run_thread = None

    def __run(self):
        self.keep_running = True
        while(self.keep_running):
            self.ws.run_forever()

    def start(self, send_msg: dict = None):
        if self.send_msg:
            self.run_thread = Thread(target=self.__run)
            self.run_thread.start()
            if self.exchange in ['kraken', 'coinbasepro']:
                time.sleep(1)
                self.ws.send(json.dumps(send_msg))
        else:
            self.__run()

    def stop(self):
        if self.exchange == 'kraken':
            self.ws.send({
                "event": "unsubscribe",
                "pair": [self.pair],
                "subscription": {"name": "ohlc", "interval": self.interval}
            })
        self.keep_running = False
        self.ws.close()
        self.run_thread.join()

def CreateWebsocket(data: DataFrame, url: str, pair: str, interval: str, condition_tick: Callable[any, Tuple[Optional[str], Optional[Row]]], on_tick: Callable, send_msg: Optional[dict] = None) -> Websocket:
    return Websocket(data, url, pair, interval, condition_tick, on_tick, send_msg)
