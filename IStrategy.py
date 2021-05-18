class IStrategy:
    def __init__(self, params):
        self.params = params
        # TODO: be sure to validate config params else raise Exception

    def populate_indicators(self, dataframe):pass

    def populate_buys(self, dataframe):pass

    def populate_sells(self, dataframe):pass

    def get_signals(self, dataframe):
        self.populate_indicators(dataframe)
        self.populate_buys(dataframe)
        self.populate_sells(dataframe)