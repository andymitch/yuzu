from binance import Client
from ta.trend import EMAIndicator
import plotly.graph_objects as go
import datetime, pandas as pd

def get_data(pair='ADABTC', interval='1h', timeframe='2 months ago'):
    client = Client()
    klines = client.get_historical_klines(pair, interval, timeframe)
    cols = ['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'trade_count', 'taker_bav', 'taker_qav', 'ignore']
    data = pd.DataFrame(klines, columns=cols).drop(['close_time', 'qav', 'trade_count', 'taker_bav', 'taker_qav', 'ignore'], axis=1)
    data[['open', 'high', 'low', 'close', 'volume']] = data[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, axis=1)
    data['time'] = data['time'].apply(lambda t: datetime.datetime.fromtimestamp(float(t/1000)).isoformat())
    return data.set_index('time').sort_index()

def populate_indicators(data):
    data['ema_fast'] = EMAIndicator(data.close, 9).ema_indicator()
    data['ema_slow'] = EMAIndicator(data.close, 99).ema_indicator()

def populate_buys(data):
    data.loc[
            (
                (data['rsi'] < 30) &
                (data['slowk'] < 20) &
                (data['bb_lowerband'] > data['close']) &
                (data['CDLHAMMER'] == 100)
            ),
            'buy'] = 1

def populate_sells(data):
    pass

def plot(data):
    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name='ADABTC')])
    fig.update_layout(template='plotly_dark')
    fig.add_scatter(y=data.ema_fast, x=data.index, mode='lines', name='ema 9', line=dict(color="yellow"))
    fig.add_scatter(y=data.ema_slow, x=data.index, mode='lines', name='ema 99', line=dict(color="aqua"))
    #for buy in list(filter(lambda i: i, data.buy.to_list())): fig.add_vline(buy.index)
    #for sell in list(filter(lambda i: i, data.sell.to_list())): fig.add_vline(sell.index)
    fig.show()

data = get_data()
populate_indicators(data)
#populate_buys(data)
r = data.iloc[0]
print(r)
print(r.next())
print(r)
populate_sells(data)
plot(data)
