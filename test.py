from backtest import backtest
from plot import plot


config = {"pair": "ADABTC", "interval": "1d", "strategy": "awesome_strat", "strategy_config": {"rsi_lookback": 8, "rsi_range": 70, "ao_fast_lookback": 5, "ao_slow_lookback": 34}, "stop_loss": 0.35}
plot(backtest(config, verbose=True, update=True), [{"column": "ao", "type": "bar"}, {"column": "rsi", "type": "line", "color": "purple"}], "ADABTC").show()
