import importlib
from strategies import AwesomeOscillatorStrategy


def _get_class(class_name, type):
    try:
        path = f'{type}.{class_name}'
        print('got path')
        _module = importlib.import_module(path)
        print('got module')
        _class = getattr(_module, class_name)
        print('got class')
        return True, _class
    except:
        return False, f'class {class_name} not found.'

def get_strategy_class(class_name):
    print(f'getting class: {class_name}\tfrom: strategies.{class_name}')
    return AwesomeOscillatorStrategy
    return _get_class(class_name, 'strategies')


def get_exchange_class(class_name):
    return _get_class(class_name, 'exchanges')

myClass = get_strategy_class('AwesomeOscillatorStrategy')
print(myClass)