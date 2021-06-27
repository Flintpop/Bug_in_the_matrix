import datetime as dt
import time

import pandas as pd
from binance.client import Client

from Trade_initiator import Trade


class Program:
    def __init__(self):
        self.client = Client("hn2OOw1SdmnFBf3SYRNa4sruUBj8LFAbUFcYYVLYxEkXdRP48EUb8NutLI2gKRRb",
                             "pkwUZomAYay2rC8I1QjPMbE55wv4zeKinwb5GCu5x0EtF3BOnbIj5E5o7MRO9kmT")

        # What to trade
        self.symbol_trade = 'BTCUSDT'

        self.interval_unit = "5T"
        self.long = False
        self.download_mode = False

        self.csv_file = r'C:\Users\darwh\Documents\btc_chart_excel_short_tests3.csv'
        self.csv_file2 = r'C:\Users\darwh\Documents\btc_chart_excel_short_tests4.csv'
        self.csv_file3 = r'C:\Users\darwh\Documents\btc_chart_excel_short_tests2.csv'

        if not self.download_mode:
            import csv
            file = open(self.csv_file)
            reader = csv.reader(file)
            self.data_range = len(list(reader)) - 2
        else:
            self.data_range = 800  # Min is 600 cuz ema.
        self.study_range = self.data_range - 600

        self.debug_mode = True

        self.n_plot_macd = 3

        self.risk_ratio = 0.675
        self.list_risk_ratio = [2, 4, 6, 7, 8, 9, 10]
        self.buffer = 0.001
        self.ema_buffer = 0.004  # Only looked to lower win rate, not activated
        self.macd_hist_buffer = 0.5  # This one need testing. Not activated

        if self.download_mode:
            self.data = Program.data(self)
            # self.data.to_csv(r'C:\Users\darwh\Documents\btc_chart_excel_short_tests2.csv')
        else:
            self.data = pd.read_csv(self.csv_file)

        self.ema_trend = Program.ema(self, 600)
        self.ema_fast = Program.ema(self, 150)

        Program.macd(self)

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            Program.macd_trend_data(self)

        self.longest_macd_indexes = Program.macd_last_cross(self)
        self.first_cross = Program.first_macd_cross(self)

        self.trade_count = 0
        self.trade_won = 0
        self.trade_lost = 0
        self.trade_in_going = False
        self.divergence_spotted = False

        self.short_won = 0
        self.short_lost = 0
        self.long_won = 0
        self.long_lost = 0

        self.win_streak = 0
        self.loss_streak = 0

        list_r = Program.high_low_finder_v2(self)

        self.high_local, self.high_prices_indexes = list_r[0], list_r[1]
        self.high_wicks, self.high_wicks_indexes = list_r[2], list_r[3]
        self.high_macd, self.high_macd_indexes = list_r[4], list_r[5]

        self.low_local, self.low_prices_indexes = list_r[6], list_r[7]
        self.low_wicks, self.low_wicks_indexes = list_r[8], list_r[9]
        self.low_macd, self.low_macd_indexes = list_r[10], list_r[11]

        waiting_time = 150
        self.last_high_low_trade_divergence = [0, 0]

        while True:
            divergence, index = Program.divergence_spotter(self)
            not_same = Program.check_not_same_trade(self)
            if divergence and not not_same:
                crossed = Program.trade_final_checking(self)
                if crossed:
                    Program.init_trade(self, list_r)

            print("Checking in " + str(waiting_time) + " seconds...")
            time.sleep(waiting_time)
            print("Checking...")
            if self.download_mode:
                self.data = Program.data(self)
                Program.data_init(self)

    def short_long_check(self, length_local, low_high_prices):
        self.long = Program.buy_sell(self, low_high_prices[length_local - 1])
        if self.long:
            self.long = Program.buy_sell(self, low_high_prices[length_local])

    def divergence_spotter(self):
        return_value = False
        index = 0

        length_local = len(self.low_local) - 1
        length_macd = len(self.low_macd) - 1

        Program.short_long_check(self, length_local, self.low_prices_indexes)

        if self.long:
            if self.low_local[length_local - 1] > self.low_local[length_local] and \
                    self.low_macd[length_macd - 1] < self.low_macd[length_macd]:
                good_line_position = Program.macd_line_checker(self, self.low_prices_indexes[length_local - 1],
                                                               self.long)
                if self.debug_mode and not self.divergence_spotted:
                    Program.debug_divergence_finder(self, self.low_prices_indexes, length_local - 1, "long")
                if good_line_position:
                    return_value = True
                    self.divergence_spotted = True
                    index = self.low_wicks_indexes[len(self.low_wicks_indexes) - 1]

        length_local = len(self.high_local) - 1
        length_macd = len(self.high_macd) - 1

        Program.short_long_check(self, length_local, self.high_prices_indexes)

        if not self.long:
            if self.high_local[length_local - 1] < self.high_local[length_local] \
                    and self.high_macd[length_macd - 1] > self.high_macd[length_macd]:
                good_line_position = Program.macd_line_checker(self, self.high_prices_indexes[length_local - 1],
                                                               self.long)
                if self.debug_mode and not self.divergence_spotted:
                    Program.debug_divergence_finder(self, self.high_prices_indexes, length_local - 1, "short")
                if not return_value:
                    if good_line_position:
                        return_value = True
                        self.divergence_spotted = True
                        index = self.high_wicks_indexes[len(self.high_wicks_indexes) - 1]
                else:
                    print("Error, return value True in long but algorithm think it is short too.")

        return return_value, index

    def check_not_same_trade(self):
        res = False  # Potentials bugs here, i dunno.
        if self.long:
            if self.last_high_low_trade_divergence[0] == self.high_local[len(self.high_local) - 1]:
                res = True
        else:
            if self.last_high_low_trade_divergence[1] == self.low_local[len(self.low_local) - 1]:
                res = True
        return res

    def init_trade(self, list_r):
        print("Initiating trade procedures...")
        fake_b_indexes = [self.fake_bull_indexes, self.fake_bear_indexes]

        print("Calculating stop_loss, take profit...")
        trade = Trade(
            long=self.long,
            data=self.data,
            list_r=list_r,
            study_range=self.study_range,
            fake_b_indexes=fake_b_indexes,
            client=self.client
        )

        print("Trade orders calculated.")
        if self.debug_mode:  # I have to recalculate enter_price, or just do it before and then adjust settings.
            Program.debug_trade_parameters(
                self=self,
                sl=trade.stop_loss,
                tp=trade.take_profit,
                enter_price=trade.enter_price,
                enter_price_index=trade.enter_price_index
            )
        print("Initiating binance procedures...")
        # orders = BinanceOrders(
        #     client=self.client,
        #     long=self.long
        # )
        # orders.quantity = trade.quantity
        # orders.leverage = trade.leverage
        # orders.init_long_short(trade.stop_loss, trade.take_profit)
        print("Orders placed and position open !")

        time_pos_open = Program.get_time(self, trade.enter_price_index)

        self.last_high_low_trade_divergence[0] = self.high_local[len(self.high_local) - 1]
        self.last_high_low_trade_divergence[1] = self.low_local[len(self.low_local) - 1]

        self.trade_in_going = trade.trade_in_going

        while self.trade_in_going:
            win, target_hit = Program.check_first_price_hit(self, trade.stop_loss, trade.take_profit, trade.enter_price)
            if target_hit:
                self.trade_in_going = False
                print("Target hit ! Won ? | " + str(win))

                real_money = trade.quantity * trade.enter_price

                Trade.add_to_log_master(trade, win, time_pos_open, real_money)

    def data_init(self):  # Didnt test this function, be careful
        self.ema_trend = Program.ema(self, 600)
        self.ema_fast = Program.ema(self, 150)

        Program.macd(self)

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            Program.macd_trend_data(self)

        self.longest_macd_indexes = Program.macd_last_cross(self)
        self.first_cross = Program.first_macd_cross(self)

        list_r = Program.high_low_finder_v2(self)

        self.high_local, self.high_prices_indexes = list_r[0], list_r[1]
        self.high_wicks, self.high_wicks_indexes = list_r[2], list_r[3]
        self.high_macd, self.high_macd_indexes = list_r[4], list_r[5]

        self.low_local, self.low_prices_indexes = list_r[6], list_r[7]
        self.low_wicks, self.low_wicks_indexes = list_r[8], list_r[9]
        self.low_macd, self.low_macd_indexes = list_r[10], list_r[11]

    def debug_divergence_finder(self, indexes, i, word):
        string_one = Program.get_time(self, indexes[i])
        string_two = Program.get_time(self, indexes[i + 1])

        print("Divergence for " + word + " at : " + str(string_one) + " and " + str(string_two))

    def trade_final_checking(self):
        print("Final checking procedures, awaiting a macd cross !")
        macd_cross = False
        last_30_hist = self.data['Hist'].tail(5).values
        length = len(last_30_hist) - 2
        divergence, index = Program.divergence_spotter(self)

        if self.long:
            while not macd_cross and divergence:  # Checks if it crossed to enter trade and if it is still a divergence.
                last_30_hist = self.data['Hist'].tail(5).values
                print("Checking long...")
                divergence, index = Program.divergence_spotter(self)
                print(last_30_hist[length] > 0)
                print(divergence)
                if last_30_hist[length] > 0 and divergence:  # Potential bug with divergence for short
                    # and checking for long or something.
                    macd_cross = True
                print("Updating data")
                Program.update_data(self, 5, self.csv_file2)
        else:
            while not macd_cross and divergence:
                last_30_hist = self.data['Hist'].tail(5).values
                print("Checking short...")
                divergence, index = Program.divergence_spotter(self)
                if last_30_hist[length] < 0 and divergence:
                    macd_cross = True
                print("Updating data")
                Program.update_data(self, 1, self.csv_file2)

        return macd_cross

    def update_data(self, time_sleep, file=""):
        time.sleep(time_sleep)
        if self.download_mode:
            self.data = Program.data(self)
            Program.data_init(self)
        else:
            import csv
            file2 = open(file)
            reader = csv.reader(file2)
            self.data_range = len(list(reader)) - 2
            self.study_range = self.data_range - 600
            self.data = pd.read_csv(file)
            Program.data_init(self)

    def debug_trade_parameters(self, sl, tp, enter_price, enter_price_index):
        date = Program.get_time(self, enter_price_index)
        print("The enter price is : " + str(enter_price) + " at : " + str(date))
        print("The stop loss is : " + str(sl))
        print("The take profit is : " + str(tp))

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

    def data(self):
        if self.interval_unit == '5T':
            start_min = (self.data_range + 1) * 5
            start_str = str(start_min) + ' minutes ago UTC'
            interval_data = '5m'

            data = pd.DataFrame(
                self.client.futures_historical_klines(symbol=self.symbol_trade, start_str=start_str,
                                                      interval=interval_data))

            data.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
                            'taker_base_vol', 'taker_quote_vol', 'is_best_match']
            data['open_date_time'] = [dt.datetime.fromtimestamp(x / 1000) for x in data.open_time]

            data = data[['open_date_time', 'open', 'high', 'low', 'close', 'volume']]

            return data

    def sma(self, period, column='close'):
        return self.data[column].rolling(window=period).mean()

    def ema(self, period, column='close'):
        return self.data[column].ewm(span=period, adjust=False).mean()

    def buy_sell(self, index):
        ema_trend = self.ema_trend.tail(self.study_range).values
        ema_fast = self.ema_fast.tail(self.study_range).values
        res = False
        if ema_trend[index] < ema_fast[index]:
            res = True
        elif ema_trend[index] > ema_fast[index]:
            res = False
        return res

    def macd(self, period_long=26, period_short=12, period_signal=9, column='close'):
        # Calc short term EMA
        short_ema = Program.ema(self, period_short, column=column)
        # Calc long term EMA
        long_ema = Program.ema(self, period_long, column=column)
        # Calc the MA Convergence divergence (MACD)
        macd = short_ema - long_ema
        self.data['MACD'] = macd
        signal = Program.ema(self, period_signal, column="MACD")
        # Signal line
        self.data['Hist'] = macd - signal
        self.data['Signal_Line'] = Program.ema(self, period_signal, column='MACD')

    def macd_trend_data(self):
        last_150_hist_macd = self.data["Hist"].tail(self.study_range).values

        bull_indexes = []
        bear_indexes = []
        fake_bull = []
        fake_bear = []

        macd_trend = last_150_hist_macd[0]
        fake_macd_trend = macd_trend
        successive_hist_macd_bear = 0
        successive_hist_macd_bull = 0

        for i in range(self.study_range):
            if last_150_hist_macd[i] > 0 and fake_macd_trend < 0:
                fake_bull.append(i)
                fake_macd_trend = last_150_hist_macd[i]
            elif last_150_hist_macd[i] < 0 and fake_macd_trend > 0:
                fake_bear.append(i)
                fake_macd_trend = last_150_hist_macd[i]

            if last_150_hist_macd[i] > 0 and macd_trend < 0:
                successive_hist_macd_bear = 0
                # croise bullish
                if successive_hist_macd_bull > self.n_plot_macd - 1:
                    # croise avec 4 macd hist plot
                    bull_indexes.append(i - self.n_plot_macd)
                    macd_trend = last_150_hist_macd[i - self.n_plot_macd]
                    successive_hist_macd_bull = 0
                else:
                    successive_hist_macd_bull += 1
            elif last_150_hist_macd[i] < 0 and macd_trend > 0:
                successive_hist_macd_bull = 0
                # croise bearish
                if successive_hist_macd_bear > self.n_plot_macd - 1:
                    bear_indexes.append(i - self.n_plot_macd)
                    macd_trend = last_150_hist_macd[i - self.n_plot_macd]
                    successive_hist_macd_bear = 0
                else:
                    successive_hist_macd_bear += 1
            else:
                successive_hist_macd_bear = 0
                successive_hist_macd_bull = 0
        # if self.debug_mode:
        #     Program.debug_macd_trend_data(self, bull_indexes, bear_indexes, fake_bull, fake_bear)

        return bull_indexes, bear_indexes, fake_bull, fake_bear

    def debug_macd_trend_data(self, bull_indexes, bear_indexes, fake_bull, fake_bear):
        # Printing debugging code
        bearish_time = []
        bullish_time = []
        fake_bull_time = []
        fake_bear_time = []

        for i in range(len(bull_indexes)):
            date = Program.get_time(self, bull_indexes[i])
            bullish_time.append(date)
        print("MACD cross bullish at : ")
        print(bullish_time)
        for i in range(len(fake_bull)):
            date = Program.get_time(self, fake_bull[i])
            fake_bull_time.append(date)
        print("MACD fake bullish at : ")
        print(fake_bull_time)

        for i in range(len(bear_indexes)):
            date = Program.get_time(self, bear_indexes[i])
            bearish_time.append(date)
        print("MACD cross bearish at : ")
        print(bearish_time)
        for i in range(len(fake_bear)):
            date = Program.get_time(self, fake_bear[i])
            fake_bear_time.append(date)
        print("MACD fake bearish at : ")
        print(fake_bear_time)

    def macd_last_cross(self):
        if len(self.bear_indexes) > len(self.bull_indexes):
            return "bear"
        elif len(self.bear_indexes) < len(self.bull_indexes):
            return "bull"
        return "none"

    def first_macd_cross(self):
        if self.bear_indexes[0] > self.bull_indexes[0]:
            return "bull"
        elif self.bear_indexes[0] < self.bull_indexes[0]:
            return "bear"

    def high_low_finder_v2(self):  # Wait, mb a fundamental bug is here, with the unused fake bear and bull indexes.
        high_prices = []
        high_wicks = []
        high_macd = []
        high_prices_i = []
        high_wicks_i = []
        high_macd_i = []

        low_prices = []
        low_wicks = []
        low_macd = []
        low_prices_i = []
        low_wicks_i = []
        low_macd_i = []

        prices = self.data['close'].tail(self.study_range).values
        macd = self.data['Hist'].tail(self.study_range).values
        highs = self.data['high'].tail(self.study_range).values
        lows = self.data['low'].tail(self.study_range).values

        lim_bu = len(self.bull_indexes)
        lim_be = len(self.bear_indexes)

        j = 0
        while j < lim_bu:
            # high prices and macd
            temp_high_low, temp_index = Program.finder_high(j, self.bear_indexes, self.bull_indexes, prices)
            high_prices.append(temp_high_low)
            high_prices_i.append(temp_index)

            temp_high_low, temp_index = Program.finder_high(j, self.bear_indexes, self.bull_indexes, highs)
            high_wicks.append(temp_high_low)
            high_wicks_i.append(temp_index)

            temp_high_low, temp_index = Program.finder_high(j, self.bear_indexes, self.bull_indexes, macd)
            high_macd.append(temp_high_low)
            high_macd_i.append(temp_index)

            j += 1

        j = 0
        while j < lim_be:
            # Low prices and macd
            temp_high_low, temp_index = Program.finder_low(j, self.bull_indexes, self.bear_indexes, prices)
            low_prices.append(temp_high_low)
            low_prices_i.append(temp_index)

            temp_high_low, temp_index = Program.finder_low(j, self.bull_indexes, self.bear_indexes, lows)
            low_wicks.append(temp_high_low)
            low_wicks_i.append(temp_index)

            temp_high_low, temp_index = Program.finder_low(j, self.bull_indexes, self.bear_indexes, macd)
            low_macd.append(temp_high_low)
            low_macd_i.append(temp_index)

            j += 1

        # if self.debug_mode:
        #     print("High prices : ")
        #     Program.idk(self, high_prices_i)
        #     print(high_prices)
        #     print("High wicks : ")
        #     Program.idk(self, high_wicks_i)
        #     print(high_wicks)
        #     print("High macd : ")
        #     print(high_macd)
        #     Program.idk(self, high_macd_i)
        #     print("Low prices : ")
        #     Program.idk(self, low_prices_i)
        #     print("Low wicks : ")
        #     Program.idk(self, low_wicks_i)
        #     print("Low macd : ")
        #     Program.idk(self, low_macd_i)

        list_of_return = [high_prices, high_prices_i, high_wicks, high_wicks_i, high_macd, high_macd_i, low_prices,
                          low_prices_i, low_wicks, low_wicks_i, low_macd, low_macd_i]
        return list_of_return

    def idk(self, indexes):
        time_debug = []
        for i in range(len(indexes)):
            date = Program.get_time(self, indexes[i])
            time_debug.append(date)
        print(time_debug)

    @staticmethod
    def finder_high(index, first_indexes, second_indexes, prices):
        temp_high_low = 0
        temp_index = 0
        i = 0
        limit = len(prices)
        length = Program.macd_cross_detection(first_indexes, second_indexes[index], limit) - second_indexes[index]
        while i < length and i < limit:
            if float(prices[i + second_indexes[index]]) > float(temp_high_low):
                temp_high_low = prices[i + second_indexes[index]]
                temp_index = i + second_indexes[index]
            i += 1
        return temp_high_low, temp_index

    @staticmethod
    def finder_low(index, first_indexes, second_indexes, prices):
        temp_high_low = 1000000
        temp_index = 0
        i = 0
        limit = len(prices)
        length = Program.macd_cross_detection(first_indexes, second_indexes[index], limit) - second_indexes[index]
        while i < length and i < limit:
            if float(prices[i + second_indexes[index]]) < float(temp_high_low):
                temp_high_low = prices[i + second_indexes[index]]
                temp_index = i + second_indexes[index]
            i += 1
        return temp_high_low, temp_index

    def last_macd_cross(self):
        lim_be = len(self.bear_indexes) - 1
        lim_b = len(self.bull_indexes) - 1
        if self.bull_indexes[lim_b] > self.bear_indexes[lim_be]:
            res = "bull"
        else:
            res = "bear"
        return res

    def macd_line_checker(self, index, long):
        last_macd_data = self.data['MACD'].tail(self.study_range).values

        res = True
        i = 0

        if long:
            start = Program.macd_cross_detection(self.bull_indexes, index)
            end = Program.macd_cross_detection(self.bear_indexes, start)

            length = end - start
        else:
            start = Program.macd_cross_detection(self.bear_indexes, index)
            end = Program.macd_cross_detection(self.bull_indexes, start)

            length = end - start

        while res and i < length:
            if long:
                if last_macd_data[i + start] > 0:
                    # MACD line crosses 0 or is under 0
                    res = False
            else:
                if last_macd_data[i + start] < 0:
                    # MACD line crosses 0 or is above 0
                    res = False
            i += 1

        return res

    @staticmethod
    def macd_cross_detection(macd_indexes, value, max_value=0):
        crossed = False
        k = 0
        v = 0
        try:
            while not crossed:
                if macd_indexes[k] > value:
                    v = macd_indexes[k]
                    crossed = True
                k += 1
        except IndexError:
            v = max_value
        return v

    def get_time(self, index):
        time_print = self.data['open_date_time']
        index = index + self.data_range - self.study_range + 1
        return time_print[index]


if __name__ == '__main__':
    program = Program()
