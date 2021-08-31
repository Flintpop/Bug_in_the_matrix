import datetime

from src.Data.data_detection_algorithms import Core
from src.Data.High_Low_Data import HighLowHistory


class StrategyConditions:
    def __init__(self, coin: HighLowHistory, debug_obj):
        self.coin = coin
        self.debug = debug_obj
        self.divergence_spotted = False

        self.last_high_low_trade_divergence = [0, 0]

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
            divergence = Core.comparator_numbers(self.coin.long, local[len(local) - 2], local[len(local) - 1]) \
                     and Core.comparator_numbers(self.coin.long, macd[len(macd) - 1], macd[len(macd) - 2])
            # if divergence:
            #     if self.debug_mode and not self.divergence_spotted:
            #         self.debug.debug_divergence_finder(indexes, len(local) - 2, word)
            #         log("\n\n\nDebug; self.data, local and macd lists.")
            #         log(self.coin.data)
            #         log(local)
            #         log(macd)
            #         self.divergence_spotted = True

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
        res = False  # Potentials bugs here, i dunno.
        if self.coin.long:
            if self.last_high_low_trade_divergence[0] == self.coin.low_local[len(self.coin.low_local) - 1]:
                res = True
        else:
            if self.last_high_low_trade_divergence[1] == self.coin.high_local[len(self.coin.high_local) - 1]:
                res = True
        return res

    def init_trade_final_checking(self):
        log = self.debug.logs.add_log
        log("\n\n" + str(datetime.datetime.now()) + " : Has entered trade_final_checking")
        log("\n\nFinal checking procedures, awaiting a macd cross !")
        self.last_high_low_trade_divergence[0] = self.coin.low_local[len(self.coin.low_local) - 1]
        self.last_high_low_trade_divergence[1] = self.coin.high_local[len(self.coin.high_local) - 1]

        self.debug.debug_file()

    def trade_final_checking(self):
        # TODO: trade_final_checking function could be overhauled to reduce the number of lines.
        last_30_hist = self.coin.data['Hist'].tail(5).values
        length = len(last_30_hist) - 2  # -2 to avoid the non closed last candle.
        macd_cross = False
        if self.coin.long:
            last_30_hist = self.coin.data['Hist'].tail(5).values
            divergence = self.divergence_spotter()
            if last_30_hist[length] > 0 and divergence and last_30_hist[length-1] < 0:
                macd_cross = True
                self.debug.debug_macd_trend_data(self.coin.bull_indexes, self.coin.bear_indexes,
                                                 self.coin.fake_bear_indexes,
                                                 self.coin.fake_bull_indexes)
            elif last_30_hist[length] > 0 and divergence and last_30_hist[length-1] > 0:
                divergence = False
                macd_cross = True
                self.raise_value_error_msg()
        else:
            last_30_hist = self.coin.data['Hist'].tail(5).values
            divergence = self.divergence_spotter()
            if last_30_hist[length] < 0 and divergence and last_30_hist[length-1] > 0:
                macd_cross = True
                self.debug.debug_macd_trend_data(self.coin.bull_indexes, self.coin.bear_indexes,
                                                 self.coin.fake_bear_indexes,
                                                 self.coin.fake_bull_indexes)
            elif last_30_hist[length] < 0 and divergence and last_30_hist[length-1] < 0:
                divergence = False
                macd_cross = True
                self.raise_value_error_msg()

        return macd_cross, divergence

    def buy_sell(self, index):
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

    def raise_value_error_msg(self):
        print("Bug in detecting properly the macd cross.\n")

        print(f"It was a long ? {self.coin.long}")
        print(f"Debug data['Hist'] : \n{self.coin.data['Hist']}\n")

        print(f'The current coin data is : \n{self.coin.data.tail(30)}')

        # raise ValueError

    def actualize_data(self, coin, debug_obj):
        self.coin = coin
        self.debug = debug_obj
