from .PaperWallet import PaperWallet


class IExchange:  # EXCHANGE CLASS INTERFACE
    def __init__(self, key=None, secret=None):
        self.paper_trade = key is None or secret is None
        self.__API_KEY = key
        self.__API_SECRET = secret
        if self.paper_trade:
            self.wallet = PaperWallet()
