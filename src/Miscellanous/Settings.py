
class Parameters:
    def __init__(self):

        # Data related
        self.symbol_trade = 'BTCUSDT'
        self.interval_unit = '5T'
        self.data_range = 950  # Min is 600 cuz ema.
        self.study_range = self.data_range - 600

        # Trade related
        self.risk_ratio = 2
        self.risk_per_trade_brut = 12
        self.buffer = 0.0002
        self.risk_per_trade = 1 - self.risk_per_trade_brut / 100
        self.wait_after_trade = 0  # Number of candles skipped after a trade.
        self.wait_after_trade_seconds = self.wait_after_trade * 300

        self.market_symbol_list = ['BTCUSDT', 'ETHUSDT']

        # Detection related
        self.n_plot_macd = 3

        # Miscellaneous
        self.debug_mode = True
        self.download_mode = True
