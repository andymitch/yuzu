# How to Create a Custom Strategy

This method of custom strategy making was influenced by [freqtrade](https://github.com/freqtrade/freqtrade) but was intentionally designed with low-code readability in mind.

1. In `/strategies/` create a new file. eg. `my_strat.py`

2. **Create a function of the same name as the file.** *In this example, we are creating the common crossed ema with rsi support strategy.*

parameters:

- `data`: OHLCV DataFrame
- `config`: object of values corresponding to required custom parameters for indicators and strategy rules.

```python
from pandas import DataFrame

def my_strat(
    data: DataFrame,
    config: object = {'ema_fast': 5, 'ema_slow': 200, "rsi": 14, 'rsi_lower': 30, 'rsi_upper': 70}
) -> DataFrame:
    ...
```

3. **Populate necessary indicators:** *`data[<INDICATOR>] = <INDICATOR_FUNC>`. Any TA library such as `ta` can be used to supply indicators.*

```python
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

...
    data['ema_fast'] = EMAIndicator(data.close, config['ema_fast']).ema_indicator()
    data['ema_slow'] = EMAIndicator(data.close, config['ema_slow']).ema_indicator()
    data['rsi'] = RSIIndicator(data.close, config['rsi']).rsi()
...
```

4. **Populate BUY, SELL signals and return DataFrame.** *Insert custom rules: `data.loc[((<RULE_1>) & (<RULE_2>) | ...(<RULE_N>)), <ACTION>] = data.close`. In this instance, when ema_fast crosses up over ema_slow and rsi is below `rsi_lower`, signal a buy. NOTE: be mindful of using parenthesis as used in the example.*

```python
from strategies.utils.utils import xup, xdn

...
    data.loc[((xup(data.ema_fast, data.ema_slow)) & (data.rsi < config['rsi_lower'])), 'buy'] = data.close
    data.loc[((xdn(data.ema_fast, data.ema_slow)) & (data.rsi > config['rsi_upper'])), 'sell'] = data.close
    return data
```

5. **Include custom `plot` function.** *Add traces of relevant indicators used: `plot.add_trace(<INDICATOR>, <ROW>, <TYPE>, <COLOR (if 'line')>, <IS_SECONDARY_TRACE>)`.*

```python
from plot import Plot

def plot(data: DataFrame, pair: str, interval: str):
    # use template plot function.
    plot = Plot(data, f"macdas_strat ({pair} {interval})")

    # add additional custom traces 
    plot.add_trace('hist', 1, 'bar')
    plot.add_trace('rsi', 1, 'line', 'purple', True)

    # return figure
    return plot
```

6. **Include custom parameter bounds to be used by `optimize.optimize`.** *The more narrow you make these bounds, the quicker you'll be able to optimize but you run the risk of cropping out the optimal solution.*

```python
config_bounds = {
    'ema_fast': [2,50],
    'ema_slow': [50,200],
    'rsi': [4,30],
    'rsi_lower': [0,50],
    'rsi_upper': [50,100]
}
```

## Full example

```python
"""/strategies/my_strat.py"""

from strategies.utils.utils import xup, xdn
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from pandas import DataFrame
from plot import Plot


def my_strat(
    data: DataFrame,
    config: object = {'ema_fast': 5, 'ema_slow': 200, "rsi": 14, 'rsi_lower': 30, 'rsi_upper': 70}
) -> DataFrame:
    data['ema_fast'] = EMAIndicator(data.close, config['ema_fast']).ema_indicator()
    data['ema_slow'] = EMAIndicator(data.close, config['ema_slow']).ema_indicator()
    data['rsi'] = RSIIndicator(data.close, config['rsi']).rsi()
    data.loc[((xup(data.ema_fast, data.ema_slow)) & (data.rsi < config['rsi_lower'])), 'buy'] = data.close
    data.loc[((xdn(data.ema_fast, data.ema_slow)) & (data.rsi > config['rsi_upper'])), 'sell'] = data.close
    return data

def plot(data, pair, interval):
    plot = Plot(data, f"macdas_strat ({pair} {interval})")
    plot.add_trace('ema_slow', 1, 'line', 'yellow')
    plot.add_trace('ema_fast', 1, 'line', 'orange')
    plot.add_trace('rsi', 2, 'line', 'purple', True)
    return plot

config_bounds = {
    'ema_fast': [2,50],
    'ema_slow': [50,200],
    'rsi': [4,30],
    'rsi_lower': [0,50],
    'rsi_upper': [50,100]
}
```
