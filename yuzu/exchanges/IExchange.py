class IExchange:
    def __init__(self, key, secret):
        self.name = ""
        self.key = key
        self.secret = secret
        self.open_trades = {{}}
        self.closed_trades = [{}]

    def buy(self, pair, type='stop-limit'):
        if pair in self.open_trades.keys:
            return False, 'A trade for this pair is already open.'
        else:
            if type == 'market':
                pass
            elif type == 'limit':
                pass
            elif type == 'stop-limit':
                pass
            else:
                return False, f'Buy type: {type} not found. Use one of [\'market\', \'limit\', \'stop-limit\']'

    def sell(self, pair, type='stop-limit'):
        if not pair in self.open_trades.keys:
            return False, 'This pair cannot be sold because it hasn\'t been bought yet.'
        else:
            if type == 'market':
                pass
            elif type == 'limit':
                pass
            elif type == 'stop-limit':
                pass
            else:
                return False, f'Sell type: {type} not found. Use one of [\'market\', \'limit\', \'stop-limit\']'

    @staticmethod
    def run(self, dataframe, callback):
        pass # TODO: run webhook to populate dataframe, call callback on new tick