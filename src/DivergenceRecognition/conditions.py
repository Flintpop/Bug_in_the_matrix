import datetime

from src.Miscellaneous.warn_user import Warn
from src.Data.data_detection_algorithms import Core
from src.Miscellaneous.settings import Parameters


class MacdDivergenceConditions:
    def __init__(self, coin, debug_obj):
        self.coin = coin
        self.debug = debug_obj
        self.warn = Warn()
        self.divergence_spotted = False
        self.settings = Parameters()
        self.log = self.warn.logs.add_log

        self.current_trade_spec = {
            "delta_price": float,
            "delta_macd": float,
            "delta_ema": float,
            "raw_percentage_risked": float,
            "leverage": int
        }

        self.last_high_low_trade_divergence = [0, 0]

    def threshold_check(self):
        pass_test = False
        if self.settings.delta_price_buffer < self.current_trade_spec["delta_price"]:
            pass_test = True
        return pass_test

    def divergence_spotter(self):
        data = self.coin
        divergence = False

        self.coin.long = self.buy_sell(data.study_range - 2)

        if self.coin.long:
            local = data.low_local
            indexes = data.low_prices_indexes
            macd = data.low_macd
            word = "long"

            self.short_long_check(len(indexes) - 1, indexes)
        else:
            local = data.high_local
            indexes = data.high_prices_indexes
            macd = data.high_macd
            word = "short"

            self.short_long_check(len(indexes) - 1, indexes)

        if self.coin.long and word == 'long' or not self.coin.long and word == 'short':
            local_length = len(local) - 1
            macd_length = len(macd) - 1
            divergence = Core.comparator_numbers(self.coin.long, local[local_length - 1],
                                                 local[local_length]) \
                         and Core.comparator_numbers(self.coin.long, macd[macd_length],
                                                     macd[macd_length - 1])
            if divergence:
                if self.coin.long:
                    self.current_trade_spec["delta_price"] = 1 - local[local_length] / local[local_length - 1]
                else:
                    self.current_trade_spec["delta_price"] = 1 - local[local_length - 1] / local[local_length]

        return divergence

    def is_obsolete(self):
        if self.coin.long:
            index = self.coin.low_prices_indexes[len(self.coin.low_prices_indexes) - 1]
            r = Core.macd_cross_detection(self.coin.fake_bear_indexes, index, -5)  # Give True if not crossed; e.a if
            # the divergence is not obsolete.
        else:
            index = self.coin.high_prices_indexes[len(self.coin.high_prices_indexes) - 1]
            r = Core.macd_cross_detection(self.coin.fake_bull_indexes, index, -5)
        if r == -5:
            return False
        else:
            print("The divergence is obsolete")
            return True

    def check_not_same_trade(self):
        res = False
        if self.coin.long:
            if self.last_high_low_trade_divergence[0] == self.coin.low_local[len(self.coin.low_local) - 1]:
                res = True
        else:
            if self.last_high_low_trade_divergence[1] == self.coin.high_local[len(self.coin.high_local) - 1]:
                res = True
        return res

    def init_trade_final_checking(self):
        log = self.warn.logs.add_log
        log("\n\n" + str(datetime.datetime.now()) + " : Has entered trade_final_checking")
        log("\nFinal checking procedures, awaiting a macd cross !")
        self.last_high_low_trade_divergence[0] = self.coin.low_local[len(self.coin.low_local) - 1]
        self.last_high_low_trade_divergence[1] = self.coin.high_local[len(self.coin.high_local) - 1]

        self.warn.debug_file()

    # This function checks if there is a macd cross while the divergence remains true
    def trade_final_checking(self):
        last_30_hist = self.coin.data['Hist'].tail(5).values
        length = len(last_30_hist) - 2  # -2 to avoid the non closed last candle.
        macd_cross = False
        if self.coin.long:
            last_30_hist = self.coin.data['Hist'].tail(5).values
            divergence = self.divergence_spotter()
            if last_30_hist[length] > 0 > last_30_hist[length - 1] and divergence:
                macd_cross = True
                self.try_debug_macd_trend()

            elif last_30_hist[length] > 0 and divergence and last_30_hist[length - 1] > 0:
                divergence = False
                macd_cross = True
                self.check_too_late_divergence()
        else:
            last_30_hist = self.coin.data['Hist'].tail(5).values
            divergence = self.divergence_spotter()
            if last_30_hist[length] < 0 < last_30_hist[length - 1] and divergence:
                macd_cross = True
                self.try_debug_macd_trend()
            elif last_30_hist[length] < 0 and divergence and last_30_hist[length - 1] < 0:
                divergence = False
                macd_cross = True
                self.check_too_late_divergence()

        return macd_cross, divergence

    def try_debug_macd_trend(self):
        try:
            self.debug.debug_macd_trend_data(self.coin.bull_indexes, self.coin.bear_indexes,
                                             self.coin.fake_bear_indexes,
                                             self.coin.fake_bull_indexes)
        except Exception as e:
            print(e)
            print(self.debug)
            print(self.coin.data)

    def buy_sell(self, index):  # TODO: Put a delta_ema here
        ema_trend = self.coin.ema_trend.tail(self.coin.study_range).values
        ema_fast = self.coin.ema_fast.tail(self.coin.study_range).values
        res = False
        if ema_trend[index] < ema_fast[index]:
            res = True
        elif ema_trend[index] > ema_fast[index]:
            res = False
        return res

    def short_long_check(self, length_local, low_high_prices_indexes):  # Check if the bot should long or short
        last_self_long = self.buy_sell(low_high_prices_indexes[length_local - 1])
        new_self_long = self.buy_sell(low_high_prices_indexes[length_local])
        if last_self_long == new_self_long:
            self.coin.long = last_self_long
        else:
            self.coin.long = not self.coin.long

    def check_too_late_divergence(self):
        self.log("\n\nBug in detecting properly the macd cross.\n")

        self.log(f"\nIt was a long ? {self.coin.long}")
        self.log(f"\nDebug data['Hist'] : \n{self.coin.data['Hist']}\n")

        self.log(f'\nThe current coin data is : \n{self.coin.data.tail(30)}')

    def macd_line_checker(self):
        last_macd_data = self.coin.data['MACD'].values
        res = True

        if self.coin.long:
            index = self.coin.bull_indexes[len(self.coin.bull_indexes) - 1]
        else:
            index = self.coin.bear_indexes[len(self.coin.bear_indexes) - 1]

        if self.coin.long:
            while res and index < self.settings.study_range:
                if last_macd_data[index] > 0:
                    res = False
                index += 1
        elif not self.coin.long:
            while res and index < self.settings.study_range:
                if last_macd_data[index] < 0:
                    res = False
                index += 1

        return res

    def actualize_data(self, coin, debug_obj):
        self.coin = coin
        self.debug = debug_obj
