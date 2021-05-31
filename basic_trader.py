from binance import Client
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import pandas as pd, numpy as np


def get_data(pair="ADABTC", interval="1h", timeframe="2 months ago"):
    client = Client()
    klines = client.get_historical_klines(pair, interval, timeframe)
    cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"]
    data = pd.DataFrame(klines, columns=cols).drop(["close_time", "qav", "trade_count", "taker_bav", "taker_qav", "ignore"], axis=1)
    data[["open", "high", "low", "close", "volume"]] = data[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric, axis=1)
    data["time"] = data["time"].apply(lambda t: datetime.datetime.fromtimestamp(float(t / 1000)).isoformat())
    return data.set_index("time").sort_index()

class ema:
    @staticmethod
    def populate_indicators(data):
        data["ema_fast"] = EMAIndicator(data.close, 9).ema_indicator()
        data["ema_fast_prev"] = data["ema_fast"].shift(1)
        data["ema_slow"] = EMAIndicator(data.close, 99).ema_indicator()
        data["ema_slow_prev"] = data["ema_slow"].shift(1)

    @staticmethod
    def populate_buys(data):
        data.loc[((data["ema_fast_prev"] < data["ema_slow_prev"])
                & (data["ema_fast"] > data["ema_slow"])),
                "buy"] = data["close"]

    @staticmethod
    def populate_sells(data):
        data.loc[((data["ema_fast_prev"] > data["ema_slow_prev"])
                & (data["ema_fast"] < data["ema_slow"])),
                "sell"] = data["close"]

    @staticmethod
    def plot(data):
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name="ADABTC")])
        fig.update_layout(template="plotly_dark")
        fig.add_scatter(y=data.ema_fast, x=data.index, mode="lines", name="ema 9", line=dict(color="magenta"))
        fig.add_scatter(y=data.ema_slow, x=data.index, mode="lines", name="ema 99", line=dict(color="aqua"))
        fig.add_scatter(y=data.buy, x=data.index, name='buy', mode='markers', marker_color='blue')
        fig.add_scatter(y=data.sell, x=data.index, name='sell', mode='markers', marker_color='yellow')
        fig.update_layout(
            autosize=True,
            paper_bgcolor="black",
            xaxis=dict(
                rangeslider=dict(
                    visible=False
                )
            )
        )
        fig.show()

    @staticmethod
    def run(data):
        ema.populate_indicators(data)
        ema.populate_buys(data)
        ema.populate_sells(data)
        ema.plot(data)

class macd:
    @staticmethod
    def populate_indicators(data, tol=.00000002):
        bbands = BollingerBands(data.close)
        data['bband_low'] = bbands.bollinger_lband()
        data['bband_mid'] = bbands.bollinger_mavg()
        data['bband_hi'] = bbands.bollinger_hband()
        data['bband_perc'] = bbands.bollinger_wband()
        macds = MACD(data.close)
        data["macd"] = macds.macd()
        data['macd_sig'] = macds.macd_signal()
        data['macd_dif'] = macds.macd_diff()
        data['macd_dif_prev'] = data["macd_dif"].shift(1)

        data['tol_hi'] = [tol] * len(data)
        data['tol_lo'] = [-tol] * len(data)

    @staticmethod
    def populate_buys(data, tol=.00000002):
        data.loc[((data['macd_dif_prev'] < 0) & (data['macd_dif'] > 0) & (data['macd_sig'] < -tol)), "buy"] = data["close"]
        #data.loc[((data['macd_dif_prev'] < 0) & (data['macd_dif'] > 0)), "buy"] = data["close"]

    @staticmethod
    def populate_sells(data, tol=.00000002):
        data.loc[((data['macd_dif_prev'] > 0) & (data['macd_dif'] < 0) & (data['macd_sig'] > tol)), "sell"] = data["close"]
        #data.loc[((data['macd_dif_prev'] > 0) & (data['macd_dif'] < 0)), "sell"] = data["close"]

    @staticmethod
    def populate_profit(data, stop_loss=.1, starting_amount:float=100.0, verbose=False):
        data['trade_profit'] = [1] * len(data)
        data['hodl_profit'] = [1] * len(data)
        bought_in = None
        data['stop_loss'] = [None] * len(data)
        wallet = {
            'base': starting_amount,
            'asset': 0.0
        }
        stop_loss_value = None
        for i, row in data.iterrows():
            if not np.isnan(row['buy']) and wallet['base'] > 0:
                wallet['asset'] = wallet['base'] / row['buy']
                wallet['base'] = 0.0
                stop_loss_value = row['buy'] * (1-stop_loss)
                data.loc[i, 'stop_loss'] = stop_loss_value
                if bought_in is None:
                    bought_in = wallet['asset']
                if verbose: print('buy @', row['buy'])
            elif not stop_loss_value is None and stop_loss_value > row['close']:
                wallet['base'] = wallet['asset'] * stop_loss_value
                wallet['asset'] = 0.0
                if verbose: print('stop loss @', stop_loss_value)
                stop_loss_value = None
            elif not np.isnan(row['sell']) and wallet['asset'] > 0:
                wallet['base'] = wallet['asset'] * row['sell']
                wallet['asset'] = 0.0
                stop_loss_value = None
                if verbose: print('sell @', row['sell'])
            if not np.isnan(row['close']):
                data.loc[i, 'trade_profit'] = (wallet['base'] + (wallet['asset'] * row['close'])) / starting_amount
                if not bought_in is None:
                    data.loc[i, 'hodl_profit'] = (bought_in * row['close']) / starting_amount


    @staticmethod
    def plot(data, pair="BTCADA"):
        fig = make_subplots(rows=3, cols=1, specs=[[{"secondary_y": True}],[{"secondary_y": False}],[{"secondary_y": False}]], shared_xaxes=True, vertical_spacing=0.02)
        fig.add_trace(go.Candlestick(x=data.index, open=data.open, high=data.high, low=data.low, close=data.close, name=pair), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.buy, x=data.index, name='buy', mode='markers', marker=dict(color='blue', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.sell, x=data.index, name='sell', mode='markers', marker=dict(color='yellow', symbol='circle-open', size=10)), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.bband_hi, x=data.index, name='bband hi', mode='lines', line=dict(color="teal"), line_shape='spline'), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.bband_mid, x=data.index, name='bband mid', mode='lines', line=dict(color="orange"), line_shape='spline'), row=1, col=1)
        fig.add_trace(go.Scatter(y=data.bband_low, x=data.index, name='bband low', mode='lines', line=dict(color="teal"), line_shape='spline'), row=1, col=1)
        #fig.add_trace(go.Scatter(y=data.bband_perc, x=data.index, name='bband percentage', mode='lines', line=dict(color="orange")), row=1, col=1, secondary_y=True)
        marker_colors = np.full(data['macd_sig'].shape, np.nan, dtype=object)
        marker_colors[(data['macd_sig'] < 0) & (data['macd_dif'] > 0)] = 'green'
        marker_colors[(data['macd_sig'] > 0) & (data['macd_dif'] > 0)] = 'lightgreen'
        marker_colors[(data['macd_sig'] > 0) & (data['macd_dif'] < 0)] = 'red'
        marker_colors[(data['macd_sig'] < 0) & (data['macd_dif'] < 0)] = 'lightcoral'
        marker_colors[data['macd_dif'] == 0] = 'lightgrey'
        fig.add_trace(go.Bar(y=data.macd_dif, x=data.index, name="macd_dif", marker_color=marker_colors), row=2, col=1)
        fig.add_trace(go.Scatter(y=data.macd, x=data.index, mode="lines", line_shape='spline', name="macd", line=dict(color="magenta")), row=2, col=1)
        fig.add_trace(go.Scatter(y=data.macd_sig, x=data.index, mode="lines", line_shape='spline', name="macd_sig", line=dict(color="aqua")), row=2, col=1)
        fig.add_trace(go.Scatter(y=data.tol_hi, x=data.index, mode="lines", name="tolerance", line=dict(color="grey")), row=2, col=1)
        fig.add_trace(go.Scatter(y=data.tol_lo, x=data.index, mode="lines", name="tolerance", line=dict(color="grey")), row=2, col=1)
        fig.add_trace(go.Scatter(y=data.hodl_profit, x=data.index, mode='lines', line_shape='spline', name='hodl_profit', line=dict(color='yellow')), row=3, col=1)
        fig.add_trace(go.Scatter(y=data.trade_profit, x=data.index, mode='lines', line_shape='spline', name='trade_profit', line=dict(color='green')), row=3, col=1)
        fig.update_layout(
            template="plotly_dark",
            autosize=True,
            paper_bgcolor="black",
            xaxis=dict(
                rangeslider=dict(
                    visible=False
                )
            )
        )
        fig.show()

    @staticmethod
    def run(interval='1h', timeframe='2 months ago', stop_loss=.1, verbose=False, pair="ADABTC", tol=.00000002):
        data = get_data(interval=interval, timeframe=timeframe)
        macd.populate_indicators(data, tol=tol)
        macd.populate_buys(data, tol=tol)
        macd.populate_sells(data, tol=tol)
        macd.populate_profit(data, stop_loss=stop_loss, verbose=verbose)
        macd.plot(data, pair=pair)

macd.run(stop_loss=.1, verbose=True, pair="ADAUSD", tol=.00000005)
