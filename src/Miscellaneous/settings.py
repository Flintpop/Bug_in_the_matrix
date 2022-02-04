
class Parameters:
    def __init__(self):
        # Data related
        self.interval_unit = '1m'
        self.data_range = 200
        self.study_range = self.data_range
        self.waiting_time = self.get_waiting_time()
        self.fast_wait_time = int(self.waiting_time / 2)

        # Trade related
        self.limit_order_mode = True
        self.price_entry_coefficient = 12  # price reduction in the range between sl and raw entry price in %
        self.limit_wait_price_order = 4  # number of candles the bot waits before giving up on the trade
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
        if self.limit_order_mode:
            self.fees = 0.000_2
        else:
            self.fees = 0.000_4
        self.lowest_money_binance = 10.0

        # Detection related
        self.n_plot_macd = (5, 4)
        self.macd_line_mode = False

        # Miscellaneous
        self.debug_mode = True
        self.download_mode = True

    def get_waiting_time(self):
        waiting_time = 0
        if self.interval_unit == '1m':
            waiting_time = 55
        elif self.interval_unit == '5m':
            waiting_time = 270
        elif self.interval_unit == '15m':
            waiting_time = 870
        elif self.interval_unit == '30m':
            waiting_time = 1_770
        elif self.interval_unit == '1h':
            waiting_time = 3_570
        elif self.interval_unit == '4h':
            waiting_time = 14_350
        return waiting_time

    def check_parameters_exception(self):
        if self.data_range - self.ema_fractals_ema[len(self.ema_fractals_ema) - 1] / 2 < \
                self.ema_fractals_ema[len(self.ema_fractals_ema) - 1]:
            print("Error, data_range too small so that ema calculations car occur.")
            raise ValueError
