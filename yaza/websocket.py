from websocket import WebSocketApp
from threading import Thread
from typing import Callable
import datetime

class Client:
    def __init__(self, url: str, on_message: Callable):
        self.ws = WebSocketApp(
            url,
            on_message = lambda ws, msg: on_message(msg),
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
        self.join()


class BinanceWebsocket(Client):
    def __init__(self, pair: str, interval: str, callback: Callable, tld: str = 'us'):
        url = f"wss://stream.binance.{tld}:9443/ws/{pair.lower()}@kline_{interval}"
        super().__init__(url, callback)

class KrakenWebsocket(Client):
    def __init__(self, pair: str, interval: str, callback: Callable):
        self.pair, self.interval = pair, interval
        url = 'wss://ws.kraken.com/'
        super().__init__(url, callback)

    def async_start(self):
        self.ws.send({
            "event": "subscribe",
            "pair": [self.pair],
            "subscription": {"name": "ohlc", "interval": get_interval(self.interval)}
        })
        return super().async_start()

    def stop(self):
        self.ws.send({
            "event": "unsubscribe",
            "pair": [self.pair],
            "subscription": {"name": "ohlc", "interval": get_interval(self.interval)}
        })
        return super().stop()

    def get_interval(self, interval: str) -> int:
        value, base = interval[:-1], interval[-1]
        return value * (60 if base == 'h' else 1440 if base == 'd' else 1)


import asyncio
import websockets

def Server():
    async def hello(websocket, path):
        name = await websocket.recv()
        print(f"< {name}")

        greeting = f"Hello {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")

    start_server = websockets.serve(hello, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

def TestClient():
    async def hello():
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            name = ''
            while name != 'quit':
                name = input("What's your name? ")

                await websocket.send(name)
                print(f"> {name}")

                greeting = await websocket.recv()
                print(f"< {greeting}")

    asyncio.get_event_loop().run_until_complete(hello())