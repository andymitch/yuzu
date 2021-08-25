from datetime import datetime
from numpy import isnan

def colorprint(i, col, val, win=False):
    time_str = "%b %d, %Y [%H:%M]"
    if col == "buy":
        print(f'\033[96m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}       @ {val}\033[00m')
    elif col == "sell":
        if win:
            print(f'\033[42m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
        else:
            print(f'\033[41m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col}      @ {val}\033[00m')
    elif col == "stop_loss":
        print(f'\033[91m{datetime.strptime(i, "%Y-%m-%dT%H:%M:%S").strftime(time_str)} {col} @ {val}\033[00m')

def backtest(data, stop_loss=.35, stop_limit_buy=.1, stop_limit_sell=.1, trading_fee=0.001, verbose=False):
    starting_amount = 100.0
    data["trade_profit"] = [0] * len(data)
    data["hodl_profit"] = [0] * len(data)
    data["stop_loss"] = [None] * len(data)
    wallet = {"base": starting_amount / 2, "asset": starting_amount / (data.loc[data.index[0], "close"] * 2)}
    hodl_wallet = wallet.copy()
    data["bought"] = [None] * len(data)
    data["sold"] = [None] * len(data)
    data["stop_lossed"] = [None] * len(data)
    stop_loss_value = None
    tally = []
    for i, row in data.iterrows():
        if not isnan(row["buy"]) and wallet["base"] > 0:
            tally.append({"buy": data.loc[i, "close"], 'win': None})
            data.loc[i, "bought"] = data.loc[i, "close"]
            fee = wallet["base"] * trading_fee
            wallet["asset"] += (wallet["base"] - fee) / row["buy"]
            wallet["base"] = 0.0
            stop_loss_value = row["buy"] * (1 - stop_loss)
            if verbose:
                colorprint(i, "buy", row["buy"])
        elif not stop_loss_value is None and stop_loss_value > row["low"]:
            tally[-1]["sell"] = stop_loss_value
            tally[-1]["win"] = bool(False)
            data.loc[i, "stop_lossed"] = stop_loss_value
            fee = wallet["asset"] * trading_fee
            wallet["base"] += (wallet["asset"] - fee) * stop_loss_value
            wallet["asset"] = 0.0
            data.loc[i, "stop_loss"] = stop_loss_value
            if verbose:
                colorprint(i, "stop_loss", stop_loss_value)
            stop_loss_value = None
        elif not isnan(row["sell"]) and wallet["asset"] > 0:
            if wallet["base"] == 0:
                tally[-1]["sell"] = data.loc[i, "close"]
                tally[-1]["win"] = bool(tally[-1]["sell"] > tally[-1]["buy"])
            else:
                tally.append({"sell": data.loc[i, "close"], "win": None})
            data.loc[i, "sold"] = data.loc[i, "close"]
            fee = wallet["asset"] * trading_fee
            wallet["base"] += (wallet["asset"] - fee) * row["sell"]
            wallet["asset"] = 0.0
            stop_loss_value = None
            if verbose:
                colorprint(i, "sell", row["sell"], tally[-1]["win"])

        if not isnan(row["close"]):
            data.loc[i, "trade_profit"] = (wallet["base"] + (wallet["asset"] * row["close"])) - starting_amount
            data.loc[i, "hodl_profit"] = (hodl_wallet["base"] + (hodl_wallet["asset"] * row["close"])) - starting_amount

    data["profit_diff_change"] = (data["trade_profit"] - data["hodl_profit"]) - (data["trade_profit"].shift() - data["hodl_profit"].shift())
    score = data.profit_diff_change.sum()
    if verbose:
        print("score:", score)
    win_rate = None
    try:
        win_rate = len(list(filter(lambda t: t['win'], tally))) / len(list(filter(lambda t: not t['win'] is None, tally)))
    except: pass
    for t in tally:
        t['diff'] = t['sell'] - t['buy'] if 'sell' in t.keys() and 'buy' in t.keys() else None
    sorted_tally = list(sorted(list(filter(lambda t: not t['diff'] is None, tally)), key=lambda t: t['diff']))
    best_trade, worst_trade = [sorted_tally[-1], sorted_tally[0]] if len(sorted_tally) > 0 else [None, None]
    results = {
        'score': score,
        'win_rate': win_rate,
        'trade_freq': f'{len(tally)}/{len(data)}',
        'best_trade': best_trade,
        'worst_trade': worst_trade
    }
    return data
