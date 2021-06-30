class PaperWallet:
    balance = {}

    def fund(self, coin: str, amount: float):
        if coin in self.balance.keys():
            self.balance[coin] += amount
        else:
            self.balance[coin] = amount

    def buy(self, pair_left: str, pair_right: str, price: float, amount: float, fee: float = .001):
        if pair_right in self.balance.keys() and self.balance[pair_right] >= amount * price:
            if self.balance[pair_right] < price * (amount + (amount * fee)):
                self.balance[pair_right] -= price * amount
                self.fund(pair_left, amount - (amount * fee))
            else:
                self.balance[pair_right] -= price * (amount + (amount * fee))
                self.fund(pair_left, amount)

    def sell(self, pair_left: str, pair_right: str, price: float, amount: Union[float, str], fee: float = .001):
        if pair_left in self.balance.keys() and self.balance[pair_left] >= amount:
            if self.balance[pair_left] < amount + (amount * fee):
                self.balance[pair_left] -= amount
                self.fund(pair_right, price * (amount - (amount * fee)))
            else:
                self.balance[pair_left] -= amount + (amount * fee)
                self.fund(pair_right, price * amount)
