from typing import *


class Row(TypedDict):
    open: float
    high: float
    low: float
    close: float
    volume: float

OrderType = Union[Literal['buy'], Literal['sell']]
ExchangeName = Union[Literal['kraken'], Literal['binanceus'], Literal['coinbasepro']]