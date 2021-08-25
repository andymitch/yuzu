from typing import *

from pandas import DataFrame
class Row(TypedDict):
    open: float
    high: float
    low: float
    close: float
    volume: float

OrderType = Union[Literal['buy'], Literal['sell']]
ExchangeName = Union[Literal['kraken'], Literal['binanceus'], Literal['coinbasepro']]

class Pair:
    def __init__(self,
        symbol: str,
        left: str,
        right: str,
        left_min: float,
        right_min: float,
        left_prec: int,
        right_prec: int,
        curr_price: float
    ):
        self.symbol = symbol
        self.left = left
        self.right = right
        self.left_min = left_min
        self.right_min = right_min
        self.left_prec = left_prec
        self.right_prec = right_prec
        self.curr_price = curr_price
        

class BinanceEnum:
    pass