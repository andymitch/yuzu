from ta.trend import SMAIndicator
from pandas import DataFrame
from strategies.utils.utils import xup, xdn
from strategies.utils.indicators import MACD, SMA

def macd_strat(
    data: DataFrame,
    config: object = {"slow_len": 26, "fast_len": 12, "sig_len": 9}
) -> DataFrame:

    macd = MACD(data.close, **config)
    data["macd"] = macd.macd
    data["hist"] = macd.hist
    data["slow_ma"] = macd.slow_ma
    data["fast_ma"] = macd.fast_ma
    data["sma200"] = SMA(data.close, 200)

    # BUY: hist > 0 & macd > 0 & slow_ma > slow_ma & close > veryslow_ma
    data.loc[(
        (xup(data["hist"])) &
        (data.macd > 0) &
        (data.fast_ma > data.slow_ma) &
        (data.close > data.sma200)
    ), "buy"] = data.close

    # SELL: hist < 0 & macd < 0 & fast_ma < fast_ma & close < veryslow_ma
    data.loc[(
        (xdn(data["hist"])) &
        (data.macd < 0) &
        (data.fast_ma < data.slow_ma) &
        (data.close < data.sma200)
    ), "sell"] = data.close

    return data