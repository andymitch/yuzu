from pytz import reference
import datetime
import math

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
