from backtest import backtest
from plot import plot


config = {"pair": "ADAUSDT", "interval": "1d", "strategy": "awesome_strat", "stop_loss": 0.35}
plot(backtest(config, verbose=True), [{"column": "ao", "type": "bar"}, {"column": "rsi", "type": "line", "color": "purple"}], "ADABTC").show()


def main():
    try:
        class_name = "InnerClass"
        path = f"testdir.{class_name}"
        import importlib
        import inspect

        mod = importlib.import_module(path)
        InnerClass = getattr(mod, "InnerClass")
        innerObj = InnerClass()
    except:
        return {"success": False, "message": f"class {class_name} not found."}
