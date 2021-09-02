from .utils import CONFIG_PATH, STRATS_PATH
from importlib.util import spec_from_file_location, module_from_spec
from ..exchanges import binance, binanceus, coinbasepro, kraken
import json, os


def __get_module(module_name, module_path):
    spec = spec_from_file_location(module_name, module_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def __get_attr(attr_name, module_name, module_path):
    return getattr(__get_module(module_name, module_path), attr_name)


def get_config(strategy_name: str = '', interval: str = '', verbose: bool = True):
    # get config dict from root, strategy, or interval level
    config = None
    try:
        file = open(CONFIG_PATH, 'r')
        config = file.read()
        file.close()
        config = json.loads(config)
    except:
        if verbose: print('\033[91m\033[1mConfig file not found.\033[00m')
        return
    if strategy_name:
        try: config = config[strategy_name]
        except:
            if verbose: print(f'\033[91m\033[1mStrategy: {strategy_name} not configured.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name}\033[00m')
            return
    if interval:
        try: config = config[interval]
        except:
            if verbose: print(f'\033[91m\033[1mInterval: {interval} not configured for Strategy: {strategy_name}.\033[00m\033[91m Run: \033[00m\033[93myuzu optimize -s {strategy_name} -i {interval}\033[00m')
            return
    return config

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