# EX
'''
def optimize(pair, interval, configs, update_data=False):
    best = None
    pairs = pair if isinstance(pair, list) else [pair]
    intervals = interval if isinstance(interval, list) else [interval]

    pairs_and_intervals = [{'pair': p, 'interval': i} for p in pairs for i in intervals]
    if update_data:
        p_map(lambda x: populate_backdata(x['pair'], x['interval'], get_timeframe(x['interval'], 3000), update=True), pairs_and_intervals)

    def run(config, _strategy):
        strategy = copy(_strategy)
        strategy.populate_indicators(config)
        strategy.populate_buys(config)
        strategy.populate_sells(config)
        strategy.backtest(verbose=False, stop_loss=.3, trading_fee=.005, respond=False)
        score = EMAIndicator((strategy.data.trade_profit - strategy.data.hodl_profit) - (strategy.data.trade_profit.shift() - strategy.data.hodl_profit.shift()), 8).ema_indicator().sum()
        return {'pair': strategy.pair, 'interval': strategy.interval, 'config': config, 'score': score, 'tally': strategy.tally}

    results = []
    tic = time.perf_counter()
    for pi in tqdm(pairs_and_intervals, colour='yellow'):
        strat = AwesomeOscillatorStrategy(pair=pi['pair'], interval=pi['interval'], max_ticks=3000, update=False, config={
                                          'rsi_lookback': configs[0]['rsi_lookback'], 'rsi_range': configs[0]['rsi_range']})
        results += list(p_map(partial(run, _strategy=strat), configs))
    toc = time.perf_counter()
    print(f"Optimizer completed in {toc - tic:0.4f} seconds")
    results.sort(key=lambda result: result['score'])
    for r in results:
        r.pop('tally')
        print(json.dumps(r, indent=2))
    best = results[-1]
    _, plot = AwesomeOscillatorStrategy(pair=best['pair'], interval=best['interval'], max_ticks=3000, update=False, config=best['config']).backtest(verbose=False, stop_loss=.3, trading_fee=.005)
    plot.show()


if __name__ == "__main__":
    #optimize(['ADABTC', 'ETHBTC', 'ADAUSDT', 'ETHUSDT', 'BTCUSDT'], ['1m', '15m', '1h', '1d'], configs=[{'rsi_lookback': lb, 'rsi_range': r} for lb in [8, 14, 20, 26, 32, 38] for r in [60, 62, 65, 68, 70, 72]], update_data=False)
    _, adabtc = AwesomeOscillatorStrategy(pair='ADABTC', interval='1d', max_ticks=1000, update=True, config={'rsi_lookback': 8, 'rsi_range': 70}).backtest(verbose=True, stop_loss=.3, trading_fee=.005)
    _, ethbtc = AwesomeOscillatorStrategy(pair='ETHBTC', interval='1d', max_ticks=1000, update=True, config={
                                          'rsi_lookback': 38, 'rsi_range': 72}).backtest(verbose=True, stop_loss=.3, trading_fee=.005)
    adabtc.show()
    ethbtc.show()
'''
