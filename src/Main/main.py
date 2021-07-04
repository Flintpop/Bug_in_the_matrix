import time

import datetime as dt
from binance.client import Client

from src.Main.Trade_initiator import Trade, BinanceOrders
from src.Miscellanous.print_and_debug import PrintUser, LogMaster
from src.Data.data import HighLowHistory
from src.Miscellanous.security import GetData
from src.Data.data_detection_algorithms import Core

#####################################################################################
"""
Version : 0.9.5b
Date : 3 / 07 / 2021
"""
#####################################################################################


class Program:
    def __init__(self):
        # Get the decryption key
        key = GetData.login()
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

        self.coin = HighLowHistory(self.client)
        self.debug = PrintUser(self.coin)

        self.log_master = LogMaster()

        self.data = self.coin.data

        self.trade_in_going = False
        self.divergence_spotted = False

        list_r = self.coin.list_r

        self.last_high_low_trade_divergence = [0, 0]

        self.debug.debug_file()
        self.state_csv = 0
        self.all_csv = ["bug_two_debug - middle backbull.csv", "bug_two_debug - middle bear.csv",
                        "bug_two_debug - last.csv", "bug_two_debug - very last.csv", "bug_two_debug - lol.csv"]

        self.wait = 265

        no_exception = True

        # This no exception is used to write in the log file the exception in the try except.
        while no_exception:
            print(self.debug.print_date_list(self.coin.low_wicks_indexes))
            try:
                # Spots divergence, then checks if it is not the same it was used.
                divergence = Program.divergence_spotter(self)
                same_trade = Program.check_not_same_trade(self)
                if divergence and not same_trade:
                    crossed = Program.trade_final_checking(self)  # Check the final indicators compliance.
                    if crossed and divergence:
                        Program.init_trade(self, list_r)

                if self.download_mode:
                    self.debug.logs.add_log("\n\n" + str(dt.datetime.now()) + ": Checking in " + str(self.wait) +
                                            " seconds...")
                    time.sleep(self.wait)
                    self.debug.debug_file()  # Just a debug file that print the last time the bot ran.
                    start = time.time()
                    self.update()  # Update the whole indicators and data to the latest.
                    self.debug.logs.add_log("\n\nThe total check lasted " + str(time.time() - start) + " seconds")
            except Exception as e:
                self.debug.logs.log(e)
                no_exception = False

    def short_long_check(self, length_local, low_high_prices):  # Check if the bot should long or short
        self.long = Program.buy_sell(self, low_high_prices[length_local - 1])
        if self.long:
            self.long = Program.buy_sell(self, low_high_prices[length_local])

    def divergence_spotter(self):
        # TODO: Modify this function to try to put it in data_detection_algorithms.py and make it static;
        # Need testing.
        data = self.coin

        length_local = len(data.low_local) - 1
        length_macd = len(data.low_macd) - 1

        Program.short_long_check(self, length_local, data.low_prices_indexes)

        if self.long:
            local = data.low_local
            macd = data.low_macd
        else:
            local = data.high_local
            macd = data.high_macd

        divergence = Core.comparator_numbers(self.long, local[len(local) - 1], local[len(local)]) \
                 and Core.comparator_numbers(self.long, macd[len(macd)], macd[len(macd) - 1])
        if divergence:
            if self.debug_mode and not self.divergence_spotted:
                self.debug.debug_divergence_finder(data.low_prices_indexes, length_local - 1, "long")
            self.divergence_spotted = True

        # if self.long:
        #     # The magical if that determines if there is a divergence or not for long and below same for short
        #     if data.low_local[length_local - 1] > data.low_local[length_local] and \
        #             data.low_macd[length_macd - 1] < data.low_macd[length_macd]:
        #         # good_line_position = self.coin.macd_line_checker(self.coin.low_prices_indexes[length_local - 1],
        #         #                                                 self.long)
        #         if self.debug_mode and not self.divergence_spotted:
        #             self.debug.debug_divergence_finder(data.low_prices_indexes, length_local - 1, "long")
        #         if True:
        #             divergence = True
        #             self.divergence_spotted = True
        #
        # length_local = len(data.high_local) - 1
        # length_macd = len(data.high_macd) - 1
        #
        # if not self.long:
        #     if data.high_local[length_local - 1] < data.high_local[length_local] \
        #             and data.high_macd[length_macd - 1] > data.high_macd[length_macd]:
        #         # good_line_position = self.coin.macd_line_checker(self.coin.high_prices_indexes[length_local - 1],
        #         #                                                  self.long)
        #         if self.debug_mode and not self.divergence_spotted:
        #             self.debug.debug_divergence_finder(data.high_prices_indexes, length_local - 1, "short")
        #         if not divergence:
        #             if True:
        #                 divergence = True
        #                 self.divergence_spotted = True
        #         else:
        #             raise self.debug.logs.add_log("\n\nError, return value True in long but algorithm think it is "
        #                                           "short too.")

        return divergence

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
        self.divergence_spotted = False
        log(self.data)
        fake_b_indexes = [self.coin.fake_bull_indexes, self.coin.fake_bear_indexes]

        log("\n\n\nInitiating trade procedures...")

        # BinanceOrders has all the methods that is related to sl, tp, leverage, quantity calc in function of the risk
        # chosen per trade and other parameters. This class contains also all the methods related to actually open a 
        # position and open orders.
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
        # Just print all the trade informations and add it to the log file.
        PrintUser.debug_trade_parameters(
            self=self.debug,
            long=self.long,
            sl=binance.stop_loss,
            tp=binance.take_profit,
            entry_price=binance.entry_price,
            enter_price_index=self.coin.study_range - 1
        )

        self.check_result(binance)

    def check_result(self, binance):
        log = self.debug.logs.add_log
        time_pos_open = self.debug.get_time(self.coin.study_range - 1)  # When is the trade open

        while binance.trade_in_going:
            win, target_hit = Program.check_target(self, binance.stop_loss, binance.take_profit,
                                                   binance.entry_price)
            if target_hit:  # When an order is hit and the position is closed.
                binance.trade_in_going = False
                log("\n\n\nTarget hit ! Won ? | " + str(win))

                time_pos_hit = self.debug.get_time(self.coin.study_range - 1)
                real_money = binance.quantity * binance.entry_price
                Trade.add_to_trade_history(binance, win, time_pos_open, time_pos_hit, real_money, self.log_master)
            time.sleep(self.wait)
            self.update()

    def trade_final_checking(self):
        log = self.debug.logs.add_log
        log("\n\nFinal checking procedures, awaiting a macd cross !")
        macd_cross = False
        last_30_hist = self.data['Hist'].tail(5).values
        length = len(last_30_hist) - 2  # -2 to avoid the non closed last candle.
        divergence = Program.divergence_spotter(self)

        self.last_high_low_trade_divergence[0] = self.coin.high_local[len(self.coin.high_local) - 1]
        self.last_high_low_trade_divergence[1] = self.coin.low_local[len(self.coin.low_local) - 1]

        if self.long:
            log("\n\nChecking long...")
            while not macd_cross and divergence:  # Checks if it crossed to enter trade and if it is still a divergence.
                last_30_hist = self.data['Hist'].tail(5).values
                divergence = Program.divergence_spotter(self)
                if last_30_hist[length] > 0 and divergence:
                    macd_cross = True
                else:
                    time.sleep(5)
                    self.update()
                # self.debug_csv_data()

        else:
            log("\n\nChecking short...")
            while not macd_cross and divergence:
                last_30_hist = self.data['Hist'].tail(5).values
                divergence = Program.divergence_spotter(self)
                if last_30_hist[length] < 0 and divergence:
                    macd_cross = True
                else:
                    time.sleep(5)
                    self.update()
                # self.debug_csv_data()

        return macd_cross

    def update(self):
        self.coin.update_data()
        self.data = self.coin.data
        self.debug.actualize_data(self.coin)

    def debug_csv_data(self):
        if self.state_csv < len(self.all_csv):
            name = self.all_csv[self.state_csv]
            self.state_csv += 1
            self.coin.read_data_csv(name)
        self.coin.indicators_init()
        self.data = self.coin.data
        self.debug.actualize_data(self.coin)

    def check_target(self, stop_loss, take_profit, enter_price):
        # See if the position is closed, and if it is lost or won.

        # Get the data
        low_wicks = self.data['low'].tail(5).values
        high_wicks = self.data['high'].tail(5).values
        prices = self.data['close'].tail(5).values

        target_hit = False
        win = False

        len_low = len(low_wicks) - 1
        len_high = len(high_wicks) - 1

        if prices[len_high] != enter_price and prices[len_low] != enter_price:  # This "if" should not work; to redo.
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
