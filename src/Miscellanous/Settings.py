
class Parameters:
    def __init__(self):

        # Data related
        self.symbol_trade = 'BTCUSDT'
        self.interval_unit = '5T'
        self.data_range = 950  # Min is 600 cuz ema.
        self.study_range = self.data_range - 600

        # Trade related
        self.risk_ratio = 2.2
        self.risk_per_trade_brut = 16
        self.buffer = 0.0002
        self.risk_per_trade = 1 - self.risk_per_trade_brut / 100

        # Detection related
        self.n_plot_macd = 10

        # Miscellaneous
        self.debug_mode = True
        self.download_mode = True
