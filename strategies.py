from pandas import DataFrame


def awesome_strat(data: DataFrame, config: object = {'rsi_lookback': 8, 'rsi_range': 70, 'ao_fast_lookback': 5, 'ao_slow_lookback': 34}) -> DataFrame:
    from ta.momentum import AwesomeOscillatorIndicator, RSIIndicator
    rsi_range = config['rsi_range']
    data['rsi'] = RSIIndicator(data.close, config['rsi_lookback']).rsi()
    data['ao'] = AwesomeOscillatorIndicator(data.high, data.low, config['ao_fast_lookback'], config['ao_slow_lookback']).awesome_oscillator()
    data.loc[((data['ao'].shift() < 0) & (data['ao'] > 0)), "buy"] = data["close"]
    data.loc[(((data.ao.shift() > 0) & (data.ao < 0))) | ((data.rsi > rsi_range) & (data.ao.shift() > data.ao)), "sell"] = data["close"]
    return data


def adx_strat(data: DataFrame, config: object = {'adx_lookback': 14, 'rsi_lookback': 14, 'adx_filter': 20, 'rsi_buy_range': 70, 'rsi_sell_range': 30}) -> DataFrame:
    from ta.trend import ADXIndicator
    from ta.momentum import RSIIndicator
    adx = ADXIndicator(data.high, data.low, data.close, config['adx_lookback'])
    data[['adx', 'adx_pos', 'adx_neg']] = adx.adx(), adx.adx_pos(), adx.adx_neg()
    data['rsi'] = RSIIndicator(data.close, config['rsi_lookback']).rsi()
    data.loc[(
        (data['adx'] > config['adx_filter']) & (data['adx_pos'] > data['adx_neg'])
        & (data['adx'].shift() < config['adx_filter']) | (data['adx_pos'].shift() < data['adx_neg'].shift())
        & (data.rsi < config['rsi_buy_range'])
    ), "buy"] = data["close"]
    data.loc[(
        (data['adx'] > config['adx_filter']) & (data['adx_pos'] < data['adx_neg'])
        & (data['adx'].shift() < config['adx_filter']) | (data['adx_pos'].shift() > data['adx_neg'].shift())
        & (data.rsi > config['rsi_sell_range'])
    ), "sell"] = data["close"]
    return data


def test_strat(data: DataFrame) -> None:
    print('this df has', len(data), 'rows')


if __name__ == "__main__":
    test_strat(DataFrame())
