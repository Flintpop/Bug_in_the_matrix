
class Parameters:
    def __init__(self):

        # Data related
        self.interval_unit = '5T'
        self.data_range = 900  # Min is 600 cuz ema.
        self.study_range = self.data_range - 600

        # Trade related
        self.risk_ratio = 2
        self.risk_per_trade_brut = 6
        self.buffer = 0.0002
        self.fees = 0.00036
        self.risk_per_trade = 1 - self.risk_per_trade_brut / 100
        self.wait_after_trade = 0  # Number of candles skipped after a trade.
        self.wait_after_trade_seconds = self.wait_after_trade * 300
        self.threshold_risk_trade = 2
        self.delta_price_buffer = 0.0038

        self.market_symbol_list = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT')
        self.lowest_quantity = (0.001, 0.001, 0.01, 1.0)
        self.maximum_leverage = (125, 100, 75, 75)
        self.lowest_money_binance = 10.0

        # Detection related
        self.n_plot_macd = 5
        self.macd_line_mode = False

        # Miscellaneous
        self.debug_mode = True
        self.download_mode = True
