# How to Optimize a Custom Strategy

This method uses a genetic algorithm to quickly find optimal strategy parameters that will maximize trade returns. It is fully contained and only requires a working strategy and configuration bounds.

```python
optimize(
    strategy_name: str, # name of strategy to use
    pair: str, # trading pair code
    interval: str, # time interval [1m, 5m, 15m, 1h, 1d]
    pop_size=1000, # number of configurations to test each round
    n_iter=100, # number of rounds (generations)
    max_mut_diff=.2, # maximum percentage to randomly mutate population after a round
    ticks=43830, # number of ticks to backtest on
    update=False, # to pull new data or just use saved data
    save=True, # to record results in `optimize_results.csv`
    plot=True # to plot the best solution once complete
) -> object # {fitness score, optimal config}
```

use:

```python
pair, interval = 'BTCUSDT', '1d'
strategy_name = 'macdas_strat'
results = optimize(strategy_name, pair, interval, update=True, ticks=10000)
```

response:

```python
results = {
    'fitness': 15.04279200137148,
    'config': {
        'slow_len': 26,
        'fast_len': 18,
        'sig_len': 5,
        'rsi_len': 33,
        'rsi_lb': 49.8262712932539,
        'rsi_ub': 77.22582235451794
    }
}
```

This response can be used to update your strategy's default configuration.
