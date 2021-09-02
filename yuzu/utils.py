from .exchanges import binance, binanceus, coinbasepro, kraken
from shutil import rmtree
from dotenv import load_dotenv
from pandas import DataFrame
from questionary import *
import importlib.util
import os, json


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


############################## GET HELPERS
def __get_module(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def __get_attr(attr_name, module_name, module_path):
    return getattr(__get_module(module_name, module_path), attr_name)


############################## GETTERS
def get_config(strategy_name: str = '', interval: str = ''):
    # get config dict from root, strategy, or interval level
    config = None
    try:
        file = open(CONFIG_PATH, 'r')
        config = file.read()
        file.close()
        config = json.loads(config)
    except:
        print('\033[91m\033[1mConfig file not found.\033[00m')
        return
    if strategy_name:
        try: config = config[strategy_name]
        except:
            print(f'\033[91m\033[1mStrategy: {strategy_name} not configured.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name}\033[00m')
            return
    if interval:
        try: config = config[interval]
        except:
            print(f'\033[91m\033[1mInterval: {interval} not configured for Strategy: {strategy_name}.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name} -i {interval}\033[00m')
            return
    return config

def set_config(update, strategy_name: str = '', interval: str = ''):
    pass # TODO: exact same as get_config but setting target to update then saving config

def get_strategy(strategy_name):
    strategy_path = STRATS_PATH + os.sep + strategy_name + '.py'
    return __get_attr('strategy', strategy_name, strategy_path)

def get_config_range(strategy_name):
    strategy_path = STRATS_PATH + os.sep + strategy_name + '.py'
    return __get_attr('config_range', strategy_name, strategy_path)

def get_exchange(exchange_name: str):
    if exchange_name == 'binance': return binance
    elif exchange_name == 'binanceus': return binanceus
    elif exchange_name == 'coinbasepro': return coinbasepro
    elif exchange_name == 'kraken': return kraken

def get_strategy_options():
    return [f.strip('.py') for f in os.listdir(STRATS_PATH)]


############################## STRING SELECTORS
def select_pair(exchange_name: str, pair: str = ''):
    all_pairs = get_exchange(exchange_name).get_available_pairs()
    if not all_pairs: raise f'Invalid exchange name: {exchange_name}'
    if not pair or not pair in all_pairs:
        pair = autocomplete(
            'Which pair?',
            choices=all_pairs,
            validate=lambda s: s in all_pairs
        ).ask()
    return pair

def select_exchange(exchange_name: str = ''):
    if exchange_name in EXCHANGES: return exchange_name
    return select(
        'Which exchange would you like to use:',
        choices=EXCHANGE_NAMES, style=style
    ).ask().lower().replace(' ', '')

def select_interval(interval: str = ''):
    if interval in INTERVALS: return interval
    return select(
        'Which interval would you like to use:',
        choices=INTERVALS, style=style
    ).ask()

def select_strategy(strategy_name: str = ''):
    all_strats = list(filter(lambda s: s != '__pycache__', get_strategy_options()))
    if not all_strats:
        print('there are no strategies.')
        return ''
    if not strategy_name in all_strats:
        strategy_name = select(
            'Which strategy?',
            choices=all_strats
        ).ask()
    return strategy_name

############################## OTHER UTILS
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
