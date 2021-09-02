from questionary import *
from yuzu.exchanges import binance, coinbase, kraken
from yuzu import backtest as yuzu_backtest
from yuzu import optimize as yuzu_optimize
from pandas import DataFrame
from shutil import rmtree, copyfile
import os, json
from pathlib import Path
from dotenv import load_dotenv
from yuzu.utils import get_strategy as _get_strategy
from yuzu.types import *
import requests
import click


ROOT_PATH = os.path.expanduser('~') + os.sep + '.yuzu'
STRATS_PATH = ROOT_PATH + os.sep + 'strategies'
ENV_PATH = ROOT_PATH + os.sep + '.env'
CONFIG_PATH = ROOT_PATH + os.sep + 'config.json'

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

def get_exchange(exchange_name: str):
    if exchange_name in ['binance', 'binanceus']: return binance
    elif exchange_name == 'coinbase': return coinbase
    elif exchange_name == 'kraken': return kraken

def get_strategy(strategy_name: str):
    return _get_strategy(strategy_name, STRATS_PATH + os.sep + strategy_name + '.py')

def get_strategy_options():
    return [f.strip('.py') for f in os.listdir(STRATS_PATH)]

def get_pair_options(exchange):
    if exchange == 'binance': return binance.get_available_pairs('com')
    elif exchange == 'binanceus': return binance.get_available_pairs('us')
    elif exchange == 'coinbase': return coinbase.get_available_pairs()
    elif exchange == 'kraken': return kraken.get_available_pairs()
    else: return []

def get_configs(strategy_name: str = '', interval: str = ''):
    config = None
    try:
        file = open(CONFIG_PATH, 'r')
        config = file.read()
        file.close()
        config = json.loads(config)
    except:
        click.echo('\033[91m\033[1mConfig file not found.\033[00m')
        return
    if strategy_name:
        try: config = config[strategy_name]
        except:
            click.echo(f'\033[91m\033[1mStrategy: {strategy_name} not configured.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name}\033[00m')
            return
    if interval:
        try: config = config[interval]
        except:
            click.echo(f'\033[91m\033[1mInterval: {interval} not configured for Strategy: {strategy_name}.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name} -i {interval}\033[00m')
            return
    return config

def store_config(config: dict):
    config_file = open(CONFIG_PATH, 'w')
    config = {
        'a': 1,
        'b': 2
    }
    config_file.write(json.dumps(config, indent=2))
    config_file.close()

# TODO: FIX
def validate_strategy(strategy_path):
    strat_name = strategy_path.split(os.sep)[-1][:-3]
    strat_mod, strat_func = None, None
    strat_func = get_strategy(STRATS_PATH + os.sep + strat_name + '.py', strat_name)
    data = strat_func(DataFrame({'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}))
    cols = data.columns.values.tolist()
    if not ('buy' in cols and 'sell' in cols): raise 'Strategy invalid. Reference example for help.'

def authenticate(exchange, key, secret):
    if exchange == 'binance': return binance.authenticate(key, secret, 'com')
    elif exchange == 'binanceus': return binance.authenticate(key, secret, 'us')
    elif exchange == 'coinbasepro': return coinbase.authenticate(key, secret)
    elif exchange == 'kraken': return kraken.authenticate(key, secret)
    else: return False

exchanges = ['binance', 'binanceus', 'coinbasepro', 'kraken']
exchange_names = ['Binance', 'Binance US', 'Coinbase Pro', 'Kraken', 'cancel']
intervals = ['1m','5m','15m','30m','1h','12h','1d']

def select_pair(exchange_name: str, pair: str = '', tld: str = ''):
    all_pairs = get_pair_options(exchange_name)
    if not all_pairs: raise f'Invalid exchange name: {exchange_name}'
    if not pair or not pair in all_pairs:
        pair = autocomplete(
            'Which pair?',
            choices=all_pairs,
            validate=lambda s: s in all_pairs
        ).ask()
    return pair

def select_strategy(strategy_name: str = ''):
    all_strats = list(filter(lambda s: s != '__pycache__', get_strategy_options()))
    if not all_strats:
        click.echo('there are no strategies.')
        return ''
    if not strategy_name in all_strats:
        strategy_name = select(
            'Which strategy?',
            choices=all_strats
        ).ask()
    return strategy_name

def select_exchange(exchange: str = ''):
    if exchange in exchanges: return exchange
    return select(
        'Which exchange would you like to use:',
        choices=exchange_names, style=style
    ).ask().lower().replace(' ', '')

def select_interval(interval: str = ''):
    if interval in intervals: return interval
    return select(
        'Which interval would you like to use:',
        choices=intervals, style=style
    ).ask()

def _auth(exchange):
    exchange = select_exchange(exchange)
    if exchange == 'cancel': return
    while True:
        key = password("API key:", style=style).ask()
        secret = password("API secret:", style=style).ask()
        if key and secret and authenticate(exchange, key, secret):
            click.echo(f'{exchange} API authentication authd!')
            load_dotenv(ENV_PATH)
            os.environ[f'{safe_exchange.upper()}_KEY'] = key
            os.environ[f'{safe_exchange.upper()}_SECRET'] = secret
            click.echo(f'{exchange} added to Yuzu!')
            return
        if not confirm(
            message='Authentication unsucessful, would you like to try again?',
            style=style
        ).ask(): return

def _delete():
    if confirm(
            message='Are you sure you would like to delete Yuzu?',
            style=style
        ).ask():
        rmtree(ROOT_PATH)
        click.echo(f'deleted \033[93m{ROOT_PATH}\033[00m')

cli = click.Group()

@cli.command()
def echo():
    exchange = select_exchange()
    strategy = select_strategy()
    pair = select_pair(exchange)
    click.echo(f'{exchange} {strategy} {pair}')

@cli.command()
@click.argument('exchange', type=click.Choice(exchanges, case_sensitive=False), required=False)
def auth(exchange): _auth(exchange=exchange)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def upload(path):
    if not path[-3:] == '.py': raise 'Strategy must be written in Python.'
    file_name = path.split('/')[-1] if path[:4] == 'http' else path.split(os.sep)[-1]
    new_path = STRATS_PATH + os.sep + file_name
    if os.path.exists(new_path):
        if confirm(
            message='Strategy already exists, overwrite?',
            style=style
        ).ask(): os.remove(new_path)
        else: return
    strat_name = file_name[:-3]
    if path[:4] == 'http':
        try:
            py_str = requests.get(path).text
            py_file = open(new_path, 'w')
            py_file.write(py_str)
            py_file.close()
        except: raise 'Unable to download strategy.'
    else:
        try: copyfile(path, new_path)
        except: raise 'Unable to copy strategy.'
    click.echo('Strategy upload successful!')

def _backtest(pair, interval, strategy, exchange, plot, config):
    exchange_name = select_exchange(exchange)
    exchange = get_exchange(exchange_name)
    tld = 'us' if exchange_name[-2:]=='us' else 'com'

    pair_symbol = select_pair(exchange_name, pair)
    pair = exchange.get_pair(pair_symbol, tld)

    strategy_name = select_strategy(strategy)
    strategy = get_strategy(strategy_name)

    interval = select_interval(interval)

    try:
        config = config or get_configs(strategy_name, interval)
        if not config: return
    except: return

    data = exchange.get_backdata(pair, interval, 1000, tld)
    data = strategy(data, config)
    return yuzu_backtest(data, config, plot=plot)

@cli.command()
@click.option('-p', '--pair', required=False, type=str, help='Pair symbol to backtest on.')
@click.option('-i', '--interval', required=False, type=str, help='Interval to backtest on.')
@click.option('-s', '--strategy', required=False, type=str, help='Strategy to backtest with.')
@click.option('-e', '--exchange', required=False, type=click.Choice(exchanges, case_sensitive=False), help='Exchange to pull backdata from.')
@click.option('--plot/--no-plot', default=False, help='Plot results if possible.')
@click.option('-c', '--config', required=False, type=str, help='Given strategy config to test (optional).')
def backtest(pair=None, interval=None, strategy=None, exchange=None, plot=False, config=None):
    result = _backtest(pair, interval, strategy, exchange, plot, config)
    if not plot: click.echo(result)

@cli.command()
@click.option('-p', '--pair', required=False, type=str, help='Pair symbol to backtest on.')
@click.option('-i', '--interval', required=False, type=str, help='Interval to backtest on.')
@click.option('-s', '--strategy', required=False, type=str, help='Strategy to backtest with.')
@click.option('-e', '--exchange', required=False, type=click.Choice(exchanges, case_sensitive=False), help='Exchange to pull backdata from.')
@click.option('--plot/--no-plot', default=False, help='Plot results if possible.')
def optimize(pair=None, interval=None, strategy=None, exchange=None, plot=None):
    # TODO: get all parameters
    # TODO: read strategy config_bounds
    # TODO: run optimize
    # TODO: backtest/compare top result and existing config, ask if want to replace
    # new config is (much better / only slightly better / the same / only slightly worse / much worse) than existing config, would you like to replace it?
    # diff = (new - old) / old
    # [>.2, <=.2, 0, >=-.2, > -.2] 20%
    pass

@cli.command()
def delete(): _delete()

@cli.command()
def setup():
    if Path(ROOT_PATH).exists():
        if confirm(
            message='Yuzu appears to have been already set up, would you like to reset Yuzu?',
            style=style
        ).ask():
            _delete()
        else: return
    os.mkdir(ROOT_PATH)
    os.mkdir(STRATS_PATH)
    Path(ENV_PATH).touch()
    Path(CONFIG_PATH).touch()
    config_file = open(CONFIG_PATH, 'w')
    config_file.write('{}')
    config_file.close()
    click.echo(f'\nYuzu root is now at: \033[93m{ROOT_PATH}\033[00m\n')
    click.echo('To add a custom strategy:')
    click.echo('\t- upload it to Yuzu by running: \033[1m\033[93myuzu upload <URL_OR_LOCAL_FILE_PATH_TO_UPLOAD_FROM>\033[00m')
    click.echo(f'\t- or manually add the file to \033[93m{STRATS_PATH}\033[00m\n')
    if confirm(
            message='Would you like to authenticate an exchange?',
            style=style
        ).ask(): _auth('')
    click.echo('Yuzu setup complete!')
