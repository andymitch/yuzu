from pandas import Series

xup = lambda left, right=0: (left.shift() < (right.shift() if isinstance(right, Series) else right)) & (left > right)
xdn = lambda left, right=0: (left.shift() > (right.shift() if isinstance(right, Series) else right)) & (left < right)