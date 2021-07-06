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
Version : 0.9.6b
Date : 6 / 07 / 2021
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

        self.wait = 265

        while True:
            # Spots divergence, then checks if it is not the same it was used.
            divergence = Program.divergence_spotter(self)
            same_trade = Program.check_not_same_trade(self)
            is_not_obsolete = Program.is_not_obsolete(self)
            if divergence and not same_trade and is_not_obsolete:
                crossed = Program.trade_final_checking(self)  # Check the final indicators compliance.
                if crossed and divergence:
                    Program.init_trade(self, list_r)

            if self.download_mode:
                self.debug.logs.add_log("\n\n" + str(dt.datetime.now()) + ": Checking in " + str(self.wait) +
                                        " seconds...")
                time.sleep(self.wait)
                self.debug.debug_file()  # Just a debug file that print the last time the bot ran.
                start = time.time()
                try:
                    self.update()  # Update the whole indicators and data to the latest.
                except Exception as e:
                    print(e)
                    time.sleep(1800)  # Wait 30 minutes.
                self.debug.logs.add_log("\n\nThe total check lasted " + str(time.time() - start) + " seconds")

    def short_long_check(self, length_local, low_high_prices):  # Check if the bot should long or short
        self.long = Program.buy_sell(self, low_high_prices[length_local - 1])
        if self.long:
            self.long = Program.buy_sell(self, low_high_prices[length_local])

    def is_not_obsolete(self):
        if self.long:
            index = self.coin.low_prices_indexes[len(self.coin.low_prices_indexes) - 1]
            r = Core.macd_cross_detection(self.coin.bear_indexes, index, -5)  # Give True if not crossed; e.a if
            # the divergence is not obsolete.
        else:
            index = self.coin.high_prices_indexes[len(self.coin.high_prices_indexes) - 1]
            r = Core.macd_cross_detection(self.coin.bull_indexes, index, -5)
        if r == -5:
            print("The divergence is not obsolete")
            return True
        else:
            print("The divergence is obsolete")
            self.divergence_spotted = False
            return False

    def divergence_spotter(self):
        # TODO: Modify this function to try to put it in data_detection_algorithms.py and make it static;
        # Need testing. Looks to work. Buggy actually for short.
        data = self.coin
        divergence = False
        log = self.debug.logs.add_log

        Program.buy_sell(self, data.study_range - 2)

        if self.long:
            local = data.low_local
            indexes = data.low_prices_indexes
            macd = data.low_macd
            word = "long"

            Program.short_long_check(self, len(local) - 1, indexes)
        else:
            local = data.high_local
            indexes = data.high_prices_indexes
            macd = data.high_macd
            word = "short"

            Program.short_long_check(self, len(local) - 1, indexes)

        if self.long and word == 'long' or not self.long and word == 'short':
            divergence = Core.comparator_numbers(self.long, local[len(local) - 2], local[len(local) - 1]) \
                     and Core.comparator_numbers(self.long, macd[len(macd) - 1], macd[len(macd) - 2])
            if divergence:
                if self.debug_mode and not self.divergence_spotted:
                    self.debug.debug_divergence_finder(indexes, len(local) - 2, word)
                    log(self.data)
                    log(local)
                    log(macd)
                    self.divergence_spotted = True

        return divergence

    def check_not_same_trade(self):
        res = False  # Potentials bugs here, i dunno.
        if self.long:
            if self.last_high_low_trade_divergence[0] == self.coin.low_local[len(self.coin.low_local) - 1]:
                res = True
        else:
            if self.last_high_low_trade_divergence[1] == self.coin.high_local[len(self.coin.high_local) - 1]:
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
        time_pos_open = self.debug.get_time(self.coin.study_range - 1)  # When is the trade open

        while binance.trade_in_going:
            log = self.debug.logs.add_log
            win, target_hit = Program.check_target(self, binance.stop_loss, binance.take_profit, time_pos_open)
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

        self.last_high_low_trade_divergence[0] = self.coin.low_local[len(self.coin.low_local) - 1]
        self.last_high_low_trade_divergence[1] = self.coin.high_local[len(self.coin.high_local) - 1]

        if self.long:
            log("\n\nChecking long...")
            while not macd_cross and divergence:  # Checks if it crossed to enter trade and if it is still a divergence.
                last_30_hist = self.data['Hist'].tail(5).values
                divergence = Program.divergence_spotter(self)
                if last_30_hist[length] > 0 and divergence and last_30_hist[length-1] < 0:
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
                if last_30_hist[length] < 0 and divergence and last_30_hist[length-1] > 0:
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

    def check_target(self, stop_loss, take_profit, time_pos_open):
        # TODO: Update this function with latest Core methods.
        # See if the position is closed, and if it is lost or won.

        # Get the data
        low_wicks = self.data['low'].tail(5).values
        high_wicks = self.data['high'].tail(5).values
        last_open_time = self.data['open_date_time'].tail(2).values

        target_hit = False
        win = False

        len_low = len(low_wicks) - 2
        len_high = len(high_wicks) - 2

        if not last_open_time[0] == time_pos_open:  # Check if not in the first unclosed candle.
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
