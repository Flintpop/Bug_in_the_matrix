import time

import datetime as dt
from binance.client import Client

from Trade_initiator import Trade, BinanceOrders
from print_and_debug import PrintUser, LogMaster
from data import Indicators
from security import GetData

#####################################################################################
"""
Version : 0.9.1b
Date : 30 / 06 / 2021
"""
#####################################################################################


class Program:
    def __init__(self):
        key = self.login()
        successful_login = False
        while not successful_login:
            try:
                self.client = Client(key[0], key[1])
                successful_login = True
            except Exception as e:
                print(e)
                print("Please try again.")
        key = ""
        print(key)

        self.long = False
        self.download_mode = True

        self.debug_mode = True

        self.list_risk_ratio = [2, 4, 6, 7, 8, 9, 10]
        self.buffer = 0.001
        # self.ema_buffer = 0.004  # Only looked to lower win rate, not activated
        # self.macd_hist_buffer = 0.5  # This one need testing. Not activated

        self.coin = Indicators(self.client)
        self.debug = PrintUser(self.coin)

        self.log_master = LogMaster()

        self.data = self.coin.data

        self.trade_in_going = False
        self.divergence_spotted = False

        list_r = self.coin.list_r

        self.last_high_low_trade_divergence = [0, 0]

        Program.print_self_coin_informations(self)

        waiting_time = 220

        while True:
            divergence, index = Program.divergence_spotter(self)
            same_trade = Program.check_not_same_trade(self)
            if divergence and not same_trade:
                crossed = Program.trade_final_checking(self)
                if crossed:
                    Program.init_trade(self, list_r)

            if self.download_mode:
                self.debug.logs.add_log("\n\n" + str(dt.datetime.now()) + ": Checking in " + str(waiting_time) +
                                        " seconds...")
                time.sleep(waiting_time)
                self.debug.debug_file()
                start = time.time()
                self.coin.update_data()
                self.data = self.coin.data
                Program.print_self_coin_informations(self)
                self.debug.logs.add_log("\n\nThe total check lasted " + str(time.time() - start) + " seconds")

    @staticmethod
    def login():
        keys = GetData()
        from getpass import getpass
        password = getpass()
        key = keys.get_data(password)
        return key

    def short_long_check(self, length_local, low_high_prices):
        self.long = Program.buy_sell(self, low_high_prices[length_local - 1])
        if self.long:
            self.long = Program.buy_sell(self, low_high_prices[length_local])

    def divergence_spotter(self):
        return_value = False
        index = 0

        length_local = len(self.coin.low_local) - 1
        length_macd = len(self.coin.low_macd) - 1

        Program.short_long_check(self, length_local, self.coin.low_prices_indexes)

        if self.long:
            if self.coin.low_local[length_local - 1] > self.coin.low_local[length_local] and \
                    self.coin.low_macd[length_macd - 1] < self.coin.low_macd[length_macd]:
                good_line_position = self.coin.macd_line_checker(self.coin.low_prices_indexes[length_local - 1],
                                                                 self.long)
                if self.debug_mode and not self.divergence_spotted:
                    self.debug.debug_divergence_finder(self.coin.low_prices_indexes, length_local - 1, "long")
                if good_line_position:
                    return_value = True
                    self.divergence_spotted = True
                    index = self.coin.low_wicks_indexes[len(self.coin.low_wicks_indexes) - 1]

        length_local = len(self.coin.high_local) - 1
        length_macd = len(self.coin.high_macd) - 1

        Program.short_long_check(self, length_local, self.coin.high_prices_indexes)

        if not self.long:
            if self.coin.high_local[length_local - 1] < self.coin.high_local[length_local] \
                    and self.coin.high_macd[length_macd - 1] > self.coin.high_macd[length_macd]:
                good_line_position = self.coin.macd_line_checker(self.coin.high_prices_indexes[length_local - 1],
                                                                 self.long)
                if self.debug_mode and not self.divergence_spotted:
                    self.debug.debug_divergence_finder(self.coin.high_prices_indexes, length_local - 1, "short")
                if not return_value:
                    if good_line_position:
                        return_value = True
                        self.divergence_spotted = True
                        index = self.coin.high_wicks_indexes[len(self.coin.high_wicks_indexes) - 1]
                else:
                    raise self.debug.logs.add_log("\n\nError, return value True in long but algorithm think it is "
                                                  "short too.")

        return return_value, index

    def print_self_coin_informations(self):
        self.debug.actualize_data(self.coin)
        d = self.debug

        d.logs.add_log("\n\nHigh prices : ")
        d.logs.add_log("\n" + d.idk(self.coin.high_prices_indexes))
        # d.logs.add_log("\nHigh wicks : ")
        # d.logs.add_log("\n" + d.idk(self.coin.high_wicks_indexes))
        # d.logs.add_log("\nHigh macd : ")
        # d.logs.add_log("\n" + d.idk(self.coin.high_macd_indexes))
        # d.logs.add_log("\nLow prices : ")
        # d.logs.add_log("\n" + d.idk(self.coin.low_prices_indexes))
        # d.logs.add_log("\nLow wicks : ")
        # d.logs.add_log("\n" + d.idk(self.coin.low_wicks_indexes))
        # d.logs.add_log("\nLow macd : ")
        # d.logs.add_log("\n" + d.idk(self.coin.low_macd_indexes))

    def check_not_same_trade(self):
        res = False  # Potentials bugs here, i dunno.
        if self.long:
            if self.last_high_low_trade_divergence[0] == self.coin.high_local[len(self.coin.high_local) - 1]:
                res = True
        else:
            if self.last_high_low_trade_divergence[1] == self.coin.low_local[len(self.coin.low_local) - 1]:
                res = True
        return res

    def init_trade(self, list_r):
        log = self.debug.logs.add_log
        log("\n\n\nInitiating trade procedures...")
        fake_b_indexes = [self.coin.fake_bull_indexes, self.coin.fake_bear_indexes]

        binance = BinanceOrders(
            long=self.long,
            data=self.data,
            list_r=list_r,
            study_range=self.coin.study_range,
            fake_b_indexes=fake_b_indexes,
            client=self.client
        )
        log("\nCalculating stop_loss, take profit...")
        binance.init_calculations()
        log("\nTrade orders calculated.")

        log("\nInitiating binance procedures...")
        # binance.init_long_short()
        # binance.place_sl_and_tp()
        log("\nOrders placed and position open !")
        PrintUser.debug_trade_parameters(
            self=self.debug,
            long=self.long,
            sl=binance.stop_loss,
            tp=binance.take_profit,
            entry_price=binance.entry_price,
            enter_price_index=binance.enter_price_index
        )

        self.last_high_low_trade_divergence[0] = self.coin.high_local[len(self.coin.high_local) - 1]
        self.last_high_low_trade_divergence[1] = self.coin.low_local[len(self.coin.low_local) - 1]

        while binance.trade_in_going:
            win, target_hit = Program.check_first_price_hit(self, binance.stop_loss, binance.take_profit,
                                                            binance.entry_price)
            if target_hit:
                binance.trade_in_going = False
                log("\n\n\nTarget hit ! Won ? | " + str(win))

                real_money = binance.quantity * binance.entry_price

                time_pos_open = self.debug.get_time(binance.enter_price_index)
                Trade.add_to_log_master(binance, win, time_pos_open, real_money, self.log_master)
            time.sleep(220)
            self.coin.update_data()
            self.data = self.coin.data
            self.debug.actualize_data(self.coin)

    def trade_final_checking(self):
        log = self.debug.logs.add_log
        log("\n\nFinal checking procedures, awaiting a macd cross !")
        macd_cross = False
        last_30_hist = self.data['Hist'].tail(5).values
        length = len(last_30_hist) - 2
        divergence, index = Program.divergence_spotter(self)

        if self.long:
            while not macd_cross and divergence:  # Checks if it crossed to enter trade and if it is still a divergence.
                last_30_hist = self.data['Hist'].tail(5).values
                log("\n\nChecking long...")
                divergence, index = Program.divergence_spotter(self)
                log(last_30_hist[length] > 0)
                log(divergence)
                if last_30_hist[length] > 0 and divergence:  # Potential bug with divergence for short
                    # and checking for long or something.
                    macd_cross = True
                log("\nUpdating data")
                time.sleep(5)
                self.coin.update_data()
                self.debug.actualize_data(self.coin)

        else:
            while not macd_cross and divergence:
                last_30_hist = self.data['Hist'].tail(5).values
                log("\n\nChecking short...")
                divergence, index = Program.divergence_spotter(self)
                if last_30_hist[length] < 0 and divergence:
                    macd_cross = True
                log("\nUpdating data")
                time.sleep(5)
                self.coin.update_data()
                self.debug.actualize_data(self.coin)

        return macd_cross

    def check_first_price_hit(self, stop_loss, take_profit, enter_price):
        low_wicks = self.data['low'].tail(5).values
        high_wicks = self.data['high'].tail(5).values
        prices = self.data['close'].tail(5).values
        target_hit = False
        win = False

        len_low = len(low_wicks) - 1
        len_high = len(high_wicks) - 1

        if prices[len_high] != enter_price and prices[len_low] != enter_price:
            if self.long:
                if float(low_wicks[len_low]) < stop_loss:  # Below SL
                    target_hit = True
                    win = False
                elif float(high_wicks[len_high]) > take_profit:  # Above TP
                    target_hit = True
                    win = True
            else:
                if float(high_wicks[len_high]) > stop_loss:  # Above SL
                    target_hit = True
                    win = False
                elif float(low_wicks[len_low]) < take_profit:  # Below TP
                    target_hit = True
                    win = True

        return win, target_hit

    def buy_sell(self, index):
        ema_trend = self.coin.ema_trend.tail(self.coin.study_range).values
        ema_fast = self.coin.ema_fast.tail(self.coin.study_range).values
        res = False
        if ema_trend[index] < ema_fast[index]:
            res = True
        elif ema_trend[index] > ema_fast[index]:
            res = False
        return res


if __name__ == '__main__':
    program = Program()
