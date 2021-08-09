# How to Optimize a Custom Strategy

This method uses a genetic algorithm to quickly find optimal strategy parameters that will maximize trade returns. It is fully contained and only requires a working strategy and configuration bounds.

```python
optimize(
    strategy: Callable, # your strategy function
    config_bounds: dict # bounds to test within for each parameter
    pair: str, # trading pair code
    interval: str, # time interval within [1m, 5m, 15m, 1h, 1d]
    pop_size=1000, # number of configurations to test each round
    n_iter=100, # number of rounds (generations)
    max_mut_diff=.2, # max amount to randomly mutate population after each round
    ticks=43830, # number of ticks to backtest on
    update=False, # to pull new data or just use saved data
    save=True, # to record results in `optimize_results.csv`
    plot=True # to plot the best solution once complete
) -> object # {fitness score, optimal config}
```

use:

```python
from my_strat import my_strat, config_bounds
from yuzu import optimize

pair, interval = 'BTCUSDT', '1d'
results = optimize(my_strat, config_bounds, pair, interval, update=True)
```

results:

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
