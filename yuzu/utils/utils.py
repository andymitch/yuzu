from questionary import Style
from pytz import reference
import math, os, datetime


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