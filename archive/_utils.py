from yuzu.types import Tuple
from dotenv import load_dotenv
from threading import Thread
import datetime
import math
import sys
import os

from importlib import import_module
import plotly.graph_objects as go
from numpy import full, nan

from pandas import Series

xup = lambda left, right=0: (left.shift() < (right.shift() if isinstance(right, Series) else right)) & (left > right)
xdn = lambda left, right=0: (left.shift() > (right.shift() if isinstance(right, Series) else right)) & (left < right)


from ta.trend import SMAIndicator, EMAIndicator

# SIMPLE MOVING AVERAGE
SMA = lambda close, len: SMAIndicator(close, len).sma_indicator()

# EXPONENTIAL MOVING AVERAGE
EMA = lambda close, len: EMAIndicator(close, len).ema_indicator()

# MOVING AVERAGE CONVERGENCE DIVERGENCE
class MACD:
    def __init__(self, close, slow_len, fast_len, sig_len):
        self.fast_ma = SMA(close, fast_len)
        self.slow_ma = SMA(close, slow_len)
        self.macd = self.fast_ma - self.slow_ma
        self.signal = SMA(self.macd, sig_len)
        self.hist = self.macd - self.signal


######################### SETUP

def get_avail_strats():
    try: return [f[:-3] for f in filter(lambda f: f not in ['__pycache__', 'utils'], os.listdir('./yuzu/strategies'))]
    except:pass

def get_avail_exchanges():
    try: return [f[:-3] for f in filter(lambda f: f != '__pycache__', os.listdir('./yuzu/exchanges'))]
    except:pass

def get_strategy(strategy_name):
    try: return getattr(import_module(f"yuzu.strategies.{strategy_name}"), strategy_name)
    except:pass

def get_config(strategy_name, interval):
    try: return getattr(import_module(f"yuzu.strategies.{strategy_name}"), "configs")[interval]
    except:pass

def get_config_range(strategy_name):
    try: return getattr(import_module(f"yuzu.strategies.{strategy_name}"), "config_range")
    except:pass

def get_plot(strategy_name):
    try: return getattr(import_module(f"yuzu.strategies.{strategy_name}"), "plot")
    except:pass

def get_min_ticks(strategy_name):
    try: return getattr(import_module(f"yuzu.strategies.{strategy_name}"), "min_ticks")
    except:pass

def get_exchange(exchange_name):
    try: return getattr(import_module(f"yuzu.exchanges.{exchange_name}"), exchange_name)
    except:pass

def get_backdata(exchange_name):
    try: return getattr(import_module(f"yuzu.exchanges.{exchange_name}"), "get_backdata")
    except:pass

def ask(question):
    answer = ''
    while not answer.lower() in ['y','yes','n','no']:
        answer = input(question)
    return answer.lower() in ['y','yes']


class KillableThread(Thread):
  def __init__(self, *args, **keywords):
    Thread.__init__(self, *args, **keywords)
    self.killed = False
 
  def start(self):
    self.__run_backup = self.run
    self.run = self.__run     
    Thread.start(self)
 
  def __run(self):
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup
 
  def globaltrace(self, frame, event, arg):
    if event == 'call':
      return self.localtrace
    else:
      return None
 
  def localtrace(self, frame, event, arg):
    if self.killed:
      if event == 'line':
        raise SystemExit()
    return self.localtrace
 
  def kill(self):
    self.killed = True

def update_url(url):
    from pymongo import MongoClient
    client = MongoClient("mongodb+srv://andrew:romafade@mangocluster0.8ncwj.mongodb.net/mango?retryWrites=true&w=majority")
    client.mango.urls.update_one({'service': 'ngrok'}, { "$set": { 'url': url } })
    print(url)

######################### PLOTTING

def trace_bar(data, name):
    marker_colors = full(data[name].shape, nan, dtype=object)
    marker_colors[(data[name] > data[name].shift()) & (data[name] > 0)] = "green"
    marker_colors[(data[name] > data[name].shift()) & (data[name] < 0)] = "RGBA(255, 0, 0, .25)"
    marker_colors[data[name] == data[name].shift()] = "grey"
    marker_colors[(data[name] < data[name].shift()) & (data[name] > 0)] = "RGBA(0, 255, 0, .25)"
    marker_colors[(data[name] < data[name].shift()) & (data[name] < 0)] = "red"
    return go.Bar(y=data[name], x=data.index, name=name, marker_color=marker_colors)

def trace_line(data, name, color):
    return go.Scatter(y=data[name], x=data.index, mode="lines", line_shape="spline", name=name, line=dict(color=color))

def add_common_plot_traces(fig, data, trade_mode=None):
    fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name='ADAUSD'), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.buy, x=data.index, name="buy", mode="markers", marker=dict(color="cyan", symbol="circle-open", size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(y=data.sell, x=data.index, name="sell", mode="markers", marker=dict(color="yellow", symbol="circle-open", size=10)), row=1, col=1)
    if trade_mode in ['backtest', 'live']:
        if trade_mode == 'backtest':
            fig.add_trace(trace_bar(data, 'profit_diff_change'), row=2, col=1)
            fig.add_trace(trace_line(data, 'hodl_profit', 'yellow'), row=2, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(y=data.bought, x=data.index, name="bought", mode="markers", marker=dict(color="cyan", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.sold, x=data.index, name="sold", mode="markers", marker=dict(color="yellow", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.stop_lossed, x=data.index, name="stop_lossed", mode="markers", marker=dict(color="magenta", symbol="circle", size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.stop_loss, x=data.index, name="stop_loss", mode="markers", marker=dict(color="magenta", symbol="circle-open", size=10)), row=1, col=1)
        fig.add_trace(trace_line(data, 'trade_profit', 'green'), row=2, col=1, secondary_y=trade_mode == 'backtest')
    fig.update_xaxes(rangeslider_visible=False, spikemode="across", spikesnap="cursor", spikedash="dot", spikecolor="grey", spikethickness=1)
    fig.update_layout(template="plotly_dark", hovermode="x", spikedistance=-1)
    fig.update_traces(xaxis="x")
    return fig


######################### EXCHANGE HELPERS

def keypair(exchange_name: str, key=None, secret=None) -> Tuple[str, str]:
    load_dotenv()
    key_k, secret_k = f'{exchange_name.upper()}_KEY', f'{exchange_name.upper()}_SECRET'
    if key and secret:
        os.environ[key_k] = key
        os.environ[secret_k] = secret
    else:
        try:
            key = os.environ[key_k]
            secret = os.environ[secret_k]
        except KeyError:
            print(f'Keypair not set: Either include keypair in request or set environmentals {key_k} and {secret_k}')
    return key, secret



######################### COLOR PRINT

