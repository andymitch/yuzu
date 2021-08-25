if __name__ == "__main__":
    from pandas import DataFrame
    from flask import Flask
    from yuzu.types import *
    from yuzu.utils import *
    from sys import argv
    import argparse

    def read_config(*args):
        from json import loads
        config_file = open('./config.json', 'r')
        config = loads(config_file.read())
        config_file.close()
        inner = config.copy()
        for k in args:
            inner = inner[k]
        return inner

    def nested(inner, keys, c):
        if len(keys) == 0:
            return c
        k = keys.pop(0)
        inner[k] = nested(inner[k], keys, c)
        return inner

    def write_config(new_val, *args):
        from json import loads, dumps
        config_file = open('./config.json', 'w+')
        config = loads(config_file.read())
        config = nested(config, list(args), new_val)
        config_file.write(dumps(config, indent=2))
        config_file.close()

    parser = argparse.ArgumentParser()
    parser.add_argument('-b','--backtest', action='store_true', help='backtest using strategy')
    parser.add_argument('-o','--optimize', action='store_true', help='optimize strategy config')
    parser.add_argument('-t','--trade', help='live trade, use -t paper to run in paper mode')
    parser.add_argument('-p', '--pair', type=str, default='ADAUSD')
    parser.add_argument('-i', '--interval', type=str, choices=['1m','5m','15m','1h','1d'], default='1h')
    parser.add_argument('-s','--strategy', type=str, choices=get_avail_strats(), required=True)
    parser.add_argument('-e','--exchange', type=str, choices=get_avail_exchanges(), default='BinanceUS')
    args = parser.parse_args(argv[1:])

    pair = args.pair
    interval = args.interval
    paper_mode = args.trade and args.trade == 'paper'
    strategy = get_strategy(args.strategy)
    config = read_config('strategies', args.strategy, args.interval)
    config_range = get_config_range(args.strategy)
    plot = get_plot(args.strategy)
    min_ticks = get_min_ticks(args.strategy)
    Exchange = get_exchange(args.exchange)
    backdata = get_backdata(args.exchange)

    if args.optimize:
        from yuzu.optimize import optimize
        data = backdata(pair, interval, max(1000,min_ticks))
        config = optimize(strategy, config_range, data)
        print(config)
    if args.backtest:
        from yuzu.optimize import backtest
        data = backdata(pair, interval, max(1000,min_ticks))
        data = strategy(data, config)
        data = backtest(data, config)
        plot(data, trade_mode='backtest').show()
    if args.trade:
        data = backdata(pair, interval, max(100,min_ticks))
        (key, secret) = (None, None) if paper_mode else keypair(args.exchange)
        trader = Exchange(config, paper_mode, key=key, secret=secret)
        trader.async_start(pair, interval, strategy, config, plot=plot)
        input('press [ENTER] to stop')
        trader.async_stop()