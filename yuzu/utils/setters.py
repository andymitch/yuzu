from .utils import CONFIG_PATH
import json

def set_config(update, strategy_name: str = '', interval: str = '', verbose: bool = False):
    config = None
    try:
        file = open(CONFIG_PATH, 'r')
        config = json.loads(file.read())
        file.close()
    except:
        if verbose: print('\033[91m\033[1mConfig file not found.\033[00m')
        return
    if strategy_name:
        if not strategy_name in config:
            config[strategy_name] = {}
        if interval:
            config[strategy_name][interval] = update
        else: config[strategy_name] = update
    else:
        config = update
    try:
        file = open(CONFIG_PATH, 'w')
        file.write(json.dumps(config, indent=2))
        file.close()
    except:
        if verbose: print('\033[91m\033[1mConfig file not found.\033[00m')
        return