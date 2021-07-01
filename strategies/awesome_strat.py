from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator
from pandas import DataFrame


def awesome_strat(data: DataFrame, config: object = {"rsi_lookback": 8, "rsi_range": 70, "ao_fast_lookback": 5, "ao_slow_lookback": 34}) -> DataFrame:
    rsi_range = config["rsi_range"]
    data["rsi"] = RSIIndicator(data.close, config["rsi_lookback"]).rsi()
    data["ao"] = AwesomeOscillatorIndicator(data.high, data.low, config["ao_fast_lookback"], config["ao_slow_lookback"]).awesome_oscillator()
    data.loc[((data["ao"].shift() < 0) & (data["ao"] > 0)), "buy"] = data["close"]
    data.loc[(((data.ao.shift() > 0) & (data.ao < 0))) | ((data.rsi > rsi_range) & (data.ao.shift() > data.ao)), "sell"] = data["close"]
    return data
