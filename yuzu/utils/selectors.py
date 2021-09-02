from .utils import EXCHANGES, EXCHANGE_NAMES, INTERVALS, style
from questionary import autocomplete, select
from .getters import get_exchange, get_strategy_options

def select_pair(exchange_name: str, pair: str = '') -> str:
    all_pairs = get_exchange(exchange_name).get_available_pairs()
    if not all_pairs: raise f'Invalid exchange name: {exchange_name}'
    if not pair or not pair in all_pairs:
        pair = autocomplete(
            'Which pair?',
            choices=all_pairs,
            validate=lambda s: s in all_pairs
        ).ask()
    return pair

def select_exchange(exchange_name: str = '') -> str:
    if exchange_name in EXCHANGES: return exchange_name
    return select(
        'Which exchange would you like to use:',
        choices=EXCHANGE_NAMES, style=style
    ).ask().lower().replace(' ', '')

def select_interval(interval: str = '') -> str:
    if interval in INTERVALS: return interval
    return select(
        'Which interval would you like to use:',
        choices=INTERVALS, style=style
    ).ask()

def select_strategy(strategy_name: str = '') -> str:
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