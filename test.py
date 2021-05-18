


def main():
    try:
        class_name = 'InnerClass'
        path = f'testdir.{class_name}'
        import importlib, inspect
        mod = importlib.import_module(path)
        InnerClass = getattr(mod, 'InnerClass')
        innerObj = InnerClass()
    except:
        return {'success': False, 'message': f'strategy class: {class_name} not found.'}

main()