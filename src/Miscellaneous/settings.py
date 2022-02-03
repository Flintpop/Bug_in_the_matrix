
class Parameters:
    def __init__(self):
        # Data related
        self.interval_unit = '1h'
        self.data_range = 200
        self.study_range = self.data_range

        # Trade related
        self.risk_ratio = 1
        self.risk_per_trade_brut = 18
        self.buffer = 0.0045
        self.risk_per_trade = 1 - self.risk_per_trade_brut / 100

        # EmaFractals trade related
        self.ema_fractals_ema = [9, 25, 100]
        self.candle_ema_range = 3

        self.long_rsi_max = 100  # Below this value 80 good 30 minutes
        self.long_rsi_min = 0  # Above this value
        self.rsi_period = 14
        self.short_rsi_min = 0  # Above this value

        # Divergence trade related
        self.wait_after_trade = 0  # Number of candles skipped after a trade.
        self.wait_after_trade_seconds = self.wait_after_trade * 300
        self.threshold_risk_trade = 2
        self.delta_price_buffer = (0.0038, 0)

        self.market_symbol_list = ['BTCUSDT']
        self.lowest_quantity = (0.001, 0.001, 0.01, 1.0)
        self.maximum_leverage = (125, 100, 75, 75)
        self.fees = 0.000_4
        self.lowest_money_binance = 10.0

        # Detection related
        self.n_plot_macd = (5, 4)
        self.macd_line_mode = False

        # Miscellaneous
        self.debug_mode = True
        self.download_mode = True
