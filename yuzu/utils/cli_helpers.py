from .utils import style, STRATS_PATH, ENV_PATH, ROOT_PATH
from .selectors import select_exchange
from .getters import get_exchange, get_strategy
from questionary import password, confirm
from dotenv import load_dotenv
from shutil import rmtree
import os
from pandas import DataFrame


def authenticate(exchange_name: str = ''):
    exchange_name = select_exchange(exchange_name)
    if exchange_name == 'cancel': return
    while True:
        key = password("API key:", style=style).ask()
        secret = password("API secret:", style=style).ask()
        if key and secret and get_exchange(exchange_name).authenticate(key, secret):
            print(f'{exchange_name} API authentication authd!')
            load_dotenv(ENV_PATH)
            os.environ[f'{exchange_name.upper()}_KEY'] = key
            os.environ[f'{exchange_name.upper()}_SECRET'] = secret
            print(f'{exchange_name} added to Yuzu!')
            return
        if not confirm(
            message='Authentication unsucessful, would you like to try again?',
            style=style
        ).ask(): return 

def validate_strategy(strategy_path):
    # TODO validate_strategy should verify:
    '''
        - module contains strategy: Callable
        - module contains config_range: dict
        - config_range['min_ticks'] exists
        - config_range['min_ticks']: List[str]
        - c in list(filter(lambda i: i != 'min_ticks', config_range.keys)) for c in config_range['min_ticks']
        - data: DataFrame = strategy(data: DataFrame)
        - 'buy', 'sell' in data.columns
    '''
    strat_name = strategy_path.split(os.sep)[-1][:-3]
    strat_mod, strat_func = None, None
    strat_func = get_strategy(STRATS_PATH + os.sep + strat_name + '.py', strat_name)
    data = strat_func(DataFrame({'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}))
    cols = data.columns.values.tolist()
    if not ('buy' in cols and 'sell' in cols): raise 'Strategy invalid. Reference example for help.'

def delete_yuzu():
    if confirm(
            message='Are you sure you would like to delete Yuzu?',
            style=style
        ).ask():
        rmtree(ROOT_PATH)
        print(f'deleted \033[93m{ROOT_PATH}\033[00m')