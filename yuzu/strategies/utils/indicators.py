from ta.trend import SMAIndicator, EMAIndicator

# SIMPLE MOVING AVERAGE
SMA = lambda close, len: SMAIndicator(close, len).sma_indicator()

# EXPONENTIAL MOVING AVERAGE
EMA = lambda close, len: EMAIndicator(close, len).ema_indicator()

# MOVING AVERAGE CONVERGENCE DIVERGENCE
class MACD:
    def __init__(self, close, slow_len, fast_len, sig_len):
        self.fast_ma = SMA(close, fast_len)
        self.slow_ma = SMA(close, slow_len)
        self.macd = self.fast_ma - self.slow_ma
        self.signal = SMA(self.macd, sig_len)
        self.hist = self.macd - self.signal