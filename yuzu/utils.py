from yuzu.types import ExchangeName, Tuple
from dotenv import load_dotenv
from pytz import reference
import datetime
import math
import os


def keypair(exchange_name: ExchangeName, key=None, secret=None) -> Tuple[str, str]:
    load_dotenv()
    key_k, secret_k = f'{exchange_name.upper()}_KEY', f'{exchange_name.upper()}_SECRET'
    if key and secret:
        os.environ[key_k] = key
        os.environ[secret_k] = secret
    else:
        try:
            key = os.environ[key_k]
            secret = os.environ[secret_k]
        except KeyError:
            print(f'Keypair not set: Either include keypair in request or set environmentals {key_k} and {secret_k}')
    return key, secret

def since(interval: str, ticks: int, last_epoch: int = -1):
    if last_epoch == -1:
        last_epoch = int(datetime.datetime.now(tz=reference.LocalTimezone()).timestamp())
    return last_epoch - (int(interval[:-1]) * (3600 if interval[-1] == 'h' else 86400 if interval[-1] == 'd' else 60) * ticks)

def safe_round(amount, precision):
    return math.floor(amount * (10**precision))/(10**precision)