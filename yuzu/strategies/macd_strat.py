from ta.trend import MACD
from ta.momentum import RSIIndicator
from pandas import DataFrame

def macd_strat(data: DataFrame):
    data['hist'] = MACD(data.close).macd_diff()
    data['rsi'] = RSIIndicator(data.close).rsi()
    data.loc[((data['hist'].shift() < 0) & (data['hist'] > 0) & (data['rsi'] < 50)), 'buy'] = data.close
    data.loc[((data['hist'].shift() > 0) & (data['hist'] < 0) & (data['rsi'] > 60)), 'sell'] = data.close
    return data