from inspect import signature
from questionary import Style
from pytz import reference
import math, os, datetime
from typing import Callable
from pandas import DataFrame


############################## CONSTANTS
ROOT_PATH = os.path.expanduser('~') + os.sep + '.yuzu'
STRATS_PATH = ROOT_PATH + os.sep + 'strategies'
ENV_PATH = ROOT_PATH + os.sep + '.env'
CONFIG_PATH = ROOT_PATH + os.sep + 'config.json'
EXCHANGES = ['binance', 'binanceus', 'coinbasepro', 'kraken']
EXCHANGE_NAMES = ['Binance', 'Binance US', 'Coinbase Pro', 'Kraken', 'cancel']
INTERVALS = ['1m','5m','15m','30m','1h','12h','1d']


############################## CLI STYLING
style = Style([
    ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
    ('question', 'bold'),               # question text
    ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),        # separator in lists
    ('instruction', ''),                # user instructions for select, rawselect, checkbox
    ('text', ''),                       # plain text
    ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
])

############################## UTILS
def since(interval: str, ticks: int, last_epoch: int = -1):
    if last_epoch == -1:
        last_epoch = int(datetime.datetime.now(tz=reference.LocalTimezone()).timestamp())
    return last_epoch - (int(interval[:-1]) * (3600 if interval[-1] == 'h' else 86400 if interval[-1] == 'd' else 60) * ticks)

def safe_round(amount, precision):
    return math.floor(amount * (10**precision))/(10**precision)

class colorprint:
    @staticmethod
    def red(skk): print("\033[91m {}\033[00m" .format(skk))
    @staticmethod
    def green(skk): print("\033[92m {}\033[00m" .format(skk))
    @staticmethod
    def yellow(skk): print("\033[93m {}\033[00m" .format(skk))
    @staticmethod
    def lightpurple(skk): print("\033[94m {}\033[00m" .format(skk))
    @staticmethod
    def purple(skk): print("\033[95m {}\033[00m" .format(skk))
    @staticmethod
    def cyan(skk): print("\033[96m {}\033[00m" .format(skk))
    @staticmethod
    def lightgrey(skk): print("\033[97m {}\033[00m" .format(skk))
    @staticmethod
    def black(skk): print("\033[98m {}\033[00m" .format(skk))

def validate_strategy(strategy_module):
    sig, params, ret_type = None, None, None
    try:
        sig = signature(strategy_module.strategy)
        params = sig.parameters
        ret_type = sig.return_annotation
    except: raise AttributeError(f"{strategy_module} has not attribute 'strategy'")
    assert type(params[0]) is DataFrame, "First strategy parameter must be of type <class 'pandas.core.frame.DataFrame'>."
    assert type(params[1]) is dict, "Second strategy parameter must be of type <class 'dict'>."
    assert ret_type is DataFrame, "Strategy return type must be of type <class 'pandas.core.frame.DataFrame'>."

    config_range = None
    try:
        config_range: dict = strategy_module.config_range
    except: raise AttributeError(f"{strategy_module} has not attribute 'config_range'")
    assert type(config_range) is dict, "Strategy config_range must be of type <class 'dict'>."
    for k in ['min_ticks', 'stop_limit_buy', ', stop_limit_sell', 'stop_limit_loss']:
        assert k in config_range, f"'{k}' must be included in strategy config_range."
        t, ts = (list, "<class 'list'>") if k=='min_ticks' else (float, "<class 'float'>")
        assert type(config_range[k]) is t, f"'{k}' must be of type {ts}."
    for m in config_range['min_ticks']:
        assert m in config_range.keys(), f"'{m}'' must be included in strategy config_range if to be considered for min_ticks key."

    config = None # TODO: create random config given config_range

    df = DataFrame({'open': [], 'high': [], 'low': [], 'close': [], 'volume': []})
    df = strategy_module.strategy(df, config)
    assert 'buy' in df.columns, "Buy column must exist in strategy's returned DataFrame."
    assert 'sell' in df.columns, "Sell column must exist in strategy's returned DataFrame."