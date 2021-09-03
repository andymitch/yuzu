from questionary import *
from yuzu import backtest as yuzu_backtest
from yuzu import optimize as yuzu_optimize
from shutil import copyfile
import os, json
from pathlib import Path
from yuzu.utils.cli_helpers import *
from yuzu.utils.getters import *
from yuzu.utils.selectors import *
from yuzu.utils.setters import *
from yuzu.utils.utils import *
from yuzu.types import *
import requests
import click


cli = click.Group()


@cli.command()
@click.argument('exchange', type=click.Choice(EXCHANGES, case_sensitive=False), required=False)
def auth(exchange): authenticate(exchange)

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

@cli.command()
@click.option('-p', '--pair', required=False, type=str, help='Pair symbol to backtest on.')
@click.option('-i', '--interval', required=False, type=str, help='Interval to backtest on.')
@click.option('-s', '--strategy', required=False, type=str, help='Strategy to backtest with.')
@click.option('-e', '--exchange', required=False, type=click.Choice(EXCHANGES, case_sensitive=False), help='Exchange to pull backdata from.')
@click.option('--plot/--no-plot', default=False, help='Plot results if possible.')
@click.option('-c', '--config', required=False, type=str, help='Given strategy config to test (optional).')
def backtest(pair, interval, strategy, exchange, plot, config):
    exchange_name = select_exchange(exchange)
    strategy_name = select_strategy(strategy)
    symbol = select_pair(exchange_name, pair)
    interval = select_interval(interval)
    if not config:
        try: config = config or get_config(strategy_name, interval)
        except: click.echo('Couldn\'t find config.')
        if not config: return
    data = get_exchange(exchange_name).get_backdata(symbol, interval, 1000)
    data = get_strategy(strategy_name)(data, config)
    click.echo(yuzu_backtest(data, config, plot=plot))

@cli.command()
@click.option('-p', '--pair', required=False, type=str, help='Pair symbol to backtest on.')
@click.option('-i', '--interval', required=False, type=str, help='Interval to backtest on.')
@click.option('-s', '--strategy', required=False, type=str, help='Strategy to backtest with.')
@click.option('-e', '--exchange', required=False, type=click.Choice(EXCHANGES, case_sensitive=False), help='Exchange to pull backdata from.')
def optimize(pair=None, interval=None, strategy=None, exchange=None):
    strategy_name = select_strategy(strategy)
    config_range = get_config_range(strategy_name)

    exchange_name = select_exchange(exchange)
    symbol = select_pair(exchange_name, pair)
    interval = select_interval(interval)
    data = get_exchange(exchange_name).get_backdata(symbol, interval, 5000)

    new_config = yuzu_optimize(data, strategy_name, config_range)
    old_config = get_config(strategy_name, interval, verbose=False)
    if not old_config:
        set_config(new_config, strategy_name, interval)
        return

    data = get_exchange(exchange_name).get_backdata(symbol, interval, 1000)
    old_score = yuzu_backtest(get_strategy(strategy_name)(data, old_config), old_config, plot=False)
    new_score = yuzu_backtest(get_strategy(strategy_name)(data, new_config), new_config, plot=False)
    diff = (new_score - old_score) / abs(old_score)

    SIG = .2
    compare_str = \
        'much better than'     if diff > SIG else \
        'slightly better than' if diff > 0 else \
        'the same as'          if diff == 0 else \
        'slightly worse than'  if diff > -SIG else \
        'much worse than'
    click.echo('The newly optimized config is ' + compare_str + ' the existing config.')
    if confirm(
            message='Would you like to replace the existing config?',
            style=style
        ).ask(): set_config(new_config, strategy_name, interval)

@cli.command()
def delete(): delete_yuzu()

@cli.command()
def setup():
    if Path(ROOT_PATH).exists():
        if confirm(
            message='Yuzu appears to have been already set up, would you like to reset Yuzu?',
            style=style
        ).ask():
            delete_yuzu()
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
        ).ask(): authenticate()
    click.echo('Yuzu setup complete!')
