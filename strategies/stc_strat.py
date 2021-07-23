from ta.trend import STCIndicator, EMAIndicator
from ta.momentum import StochasticOscillator
from pandas import DataFrame

def stc_strat(data: DataFrame, config: object = {'oversold': 25, 'overbought': 75}) -> DataFrame:
    data['ema'] = EMAIndicator(data.close, 100).ema_indicator()
    stoch = StochasticOscillator(data.high, data.low, data.close)
    data['so'] = stoch.stoch() - stoch.stoch_signal()
    data["stc"] = STCIndicator(data.close).stc()
    data.loc[(
        (data.ema > data.ema.shift()) &
        (data.stc > 10 & (
            ((data.so.shift() < 0) & (data.so > 0)) |
            ((data.so > 0) & (data.stc.shift() < 10))
        ))
    ), 'buy'] = data['close']
    data.loc[(((data.stc.shift() > 90) & (data.stc < 90))), "sell"] = data["close"]
    return data

# ema > ema.shift & (stc > 10 & (so.xup | (so.up & stc.shift < 10)))