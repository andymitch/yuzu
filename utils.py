import importlib

def _get_class(class_name, type):
    try:
        return True, getattr(importlib.import_module(f'{type}.{class_name}'), class_name)
    except:
        return False, f'strategy class: {class_name} not found.'

def get_strategy_class(class_name):
    return _get_class(class_name, 'strategies')

def get_exchange_class(class_name):
    return _get_class(class_name, 'exchanges')