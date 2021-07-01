from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator
from pandas import DataFrame


def adx_strat(data: DataFrame, config: object = {"adx_lookback": 14, "rsi_lookback": 14, "adx_filter": 20, "rsi_buy_range": 70, "rsi_sell_range": 30}) -> DataFrame:
    adx = ADXIndicator(data.high, data.low, data.close, config["adx_lookback"])
    data[["adx", "adx_pos", "adx_neg"]] = adx.adx(), adx.adx_pos(), adx.adx_neg()
    data["rsi"] = RSIIndicator(data.close, config["rsi_lookback"]).rsi()
    data.loc[
        (
            (data["adx"] > config["adx_filter"]) & (data["adx_pos"] > data["adx_neg"]) & (data["adx"].shift() < config["adx_filter"])
            | (data["adx_pos"].shift() < data["adx_neg"].shift()) & (data.rsi < config["rsi_buy_range"])
        ),
        "buy",
    ] = data["close"]
    data.loc[
        (
            (data["adx"] > config["adx_filter"]) & (data["adx_pos"] < data["adx_neg"]) & (data["adx"].shift() < config["adx_filter"])
            | (data["adx_pos"].shift() > data["adx_neg"].shift()) & (data.rsi > config["rsi_sell_range"])
        ),
        "sell",
    ] = data["close"]
    return data
