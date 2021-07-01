from utils import get_backdata, get_strategy, get_timeframe
from datetime import datetime
from numpy import isnan


def colorprint(i, col, val, include_time=True):
    time_str = "%b %d, %Y [%H:%M]" if include_time else "%b %d, %Y"
    if col == "buy":
        print(f'\033[96m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}       @ {val}\033[00m')
    elif col == "sell":
        print(f'\033[93m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
    elif col == "stop_loss":
        print(f'\033[91m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col} @ {val}\033[00m')


def backtest(config: object, trading_fee=0.001, verbose=False, respond=True):
    data = get_backdata(config["pair"], config["interval"], get_timeframe(config["interval"], 3000), update=True)
    data = get_strategy(config["strategy"])(data)
    starting_amount = 100.0
    data["trade_profit"] = [0] * len(data)
    data["hodl_profit"] = [0] * len(data)
    bought_in = None
    data["stop_loss"] = [None] * len(data)
    wallet = {"base": starting_amount, "asset": 0.0}
    data["bought"] = [None] * len(data)
    data["sold"] = [None] * len(data)
    data["stop_lossed"] = [None] * len(data)
    stop_loss_value = None
    tally = []
    for i, row in data.iterrows():
        if not isnan(row["buy"]) and wallet["base"] > 0:
            tally.append({"buy": data.loc[i, "close"]})
            data.loc[i, "bought"] = data.loc[i, "close"]
            fee = wallet["base"] * trading_fee
            wallet["asset"] = (wallet["base"] - fee) / row["buy"]
            wallet["base"] = 0.0
            stop_loss_value = row["buy"] * (1 - config["stop_loss"])
            if bought_in is None:
                bought_in = wallet["asset"]
            if verbose:
                colorprint(i, "buy", row["buy"], config["interval"][-1] != "d")
        elif not stop_loss_value is None and stop_loss_value > row["low"]:
            tally[-1]["sell"] = data.loc[i, "close"]
            tally[-1]["win"] = bool(tally[-1]["sell"] > tally[-1]["buy"])
            data.loc[i, "stop_lossed"] = data.loc[i, "close"]
            fee = wallet["asset"] * trading_fee
            wallet["base"] = (wallet["asset"] - fee) * stop_loss_value
            wallet["asset"] = 0.0
            data.loc[i, "stop_loss"] = stop_loss_value
            if verbose:
                colorprint(i, "stop_loss", stop_loss_value, config["interval"][-1] != "d")
            stop_loss_value = None
        elif not isnan(row["sell"]) and wallet["asset"] > 0:
            tally[-1]["sell"] = data.loc[i, "close"]
            tally[-1]["win"] = bool(tally[-1]["sell"] > tally[-1]["buy"])
            data.loc[i, "sold"] = data.loc[i, "close"]
            fee = wallet["asset"] * trading_fee
            wallet["base"] = (wallet["asset"] - fee) * row["sell"]
            wallet["asset"] = 0.0
            stop_loss_value = None
            if verbose:
                colorprint(i, "sell", row["sell"], config["interval"][-1] != "d")
        if not isnan(row["close"]):
            data.loc[i, "trade_profit"] = (((wallet["base"] + (wallet["asset"] * row["close"])) / starting_amount) - 1) * 100
            if not bought_in is None:
                data.loc[i, "hodl_profit"] = (((bought_in * row["close"]) / starting_amount) - 1) * 100

    data["profit_diff"] = (data["trade_profit"] - data["hodl_profit"]) - (data["trade_profit"].shift() - data["hodl_profit"].shift())
    score = data.profit_diff.sum()
    if verbose:
        print("score:", score)
    if respond:
        return data
