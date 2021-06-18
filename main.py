# import numpy as np
from binance.client import Client
import datetime as dt
import pandas as pd
import time
from Trade_initiator import quantity_calculator


class Program:
    def __init__(self):
        self.client = Client("hn2OOw1SdmnFBf3SYRNa4sruUBj8LFAbUFcYYVLYxEkXdRP48EUb8NutLI2gKRRb",
                             "pkwUZomAYay2rC8I1QjPMbE55wv4zeKinwb5GCu5x0EtF3BOnbIj5E5o7MRO9kmT")

        # What to trade
        self.symbol_trade = 'BTCUSDT'

        self.infos = self.client.futures_account()

        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

        print("The current total funds are : " + str(self.current_balance))
        print("The current available funds are : " + str(self.balance_available))

        self.interval_unit = "5T"
        self.long = False
        self.download_mode = True

        csv_file = r'C:\Users\darwh\Documents\btc_chart_excel_short_tests5.csv'
        csv_file2 = r'C:\Users\darwh\Documents\btc_chart_excel_short_tests5.csv'

        if not self.download_mode:
            import csv
            file = open(csv_file2)
            reader = csv.reader(file)
            self.data_range = len(list(reader)) - 2
        else:
            self.data_range = 750  # Min is 600 cuz ema.
        self.study_range = 300
        # Program.place_order(self, "LONG", "BUY", "")
        # time.sleep(5)

        self.debug_mode = False

        self.debug_trades = []

        self.n_plot_macd = 3

        self.risk_ratio = 0.675
        self.list_risk_ratio = [2, 4, 6, 7, 8, 9, 10]
        self.buffer = 0.001
        self.ema_buffer = 0.004  # Only looked to lower win rate
        self.macd_hist_buffer = 0.5  # This one need testing.

        self.risk_per_trade = 21
        self.risk_per_trade = 1 - self.risk_per_trade / 100

        Program.cancel_all_orders(self)

        if self.download_mode:
            self.data = Program.data(self)
            # self.data.to_csv(r'C:\Users\darwh\Documents\btc_chart_excel_short_tests2.csv')
        else:
            self.data = pd.read_csv(csv_file)

        self.ema_trend = Program.ema(self, 600)
        self.ema_fast = Program.ema(self, 150)
        self.money = 200
        self.start_money = self.money

        Program.macd(self)

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            Program.macd_trend_data(self)

        self.longest_macd_indexes = Program.macd_last_cross(self)
        self.first_cross = Program.first_macd_cross(self)

        self.trade_count = 0
        self.trade_won = 0
        self.trade_lost = 0
        self.trade_aborted = False
        self.trade_in_going = False

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

        while True:

            print("\nEntered long scanning\n")

            for i in range(len(self.low_local) - 1):
                self.long = Program.buy_sell(self, self.low_prices_indexes[i])
                if self.long:
                    self.long = Program.buy_sell(self, self.low_prices_indexes[i + 1])

                if self.low_local[i] > self.low_local[i + 1] and self.low_macd[i] < self.low_macd[i + 1] and self.long:
                    res = Program.macd_line_checker(self, self.low_prices_indexes[i], self.long)
                    if self.debug_mode:
                        Program.debug_divergence_finder(self, self.low_prices_indexes, i, "long")
                    if res and i + 1 != len(self.low_local) - 1:
                        if i + 1 != len(self.low_local) - 1:
                            Program.trade_result_instruction(self, i)
                        else:
                            while self.trade_in_going:
                                print("Checking in 30 seconds.")
                                time.sleep(30)
                                print("Checking...")
                                Program.data_init(self)
                                Program.trade_result_instruction(self, i)

            print("\nEntered short scanning\n")

            for i in range(len(self.high_local) - 1):
                self.long = Program.buy_sell(self, self.high_prices_indexes[i])
                if not self.long:
                    self.long = Program.buy_sell(self, self.high_prices_indexes[i + 1])

                if self.high_local[i] < self.high_local[i + 1] and self.high_macd[i] > self.high_macd[
                    i + 1] and not self.long:
                    res = Program.macd_line_checker(self, self.high_prices_indexes[i], self.long)
                    if self.debug_mode:
                        Program.debug_divergence_finder(self, self.high_prices_indexes, i, "short")
                    if res:
                        if i + 1 != len(self.high_local) - 1:
                            Program.trade_result_instruction(self, i)
                        else:
                            Program.trade_result_instruction(self, i)
                            while self.trade_in_going:
                                print("Checking in 30 seconds.")
                                time.sleep(30)
                                print("Checking...")
                                Program.data_init(self)
                                Program.trade_result_instruction(self, i)

            time.sleep(300)
            self.trade_in_going = False
            if self.download_mode:
                Program.data_init(self)

    def place_order(self, position_side, side, quantity, leverage):
        self.client.futures_change_leverage(symbol="BTCUSDT", leverage=str(leverage))
        time.sleep(5)
        self.client.futures_create_order(symbol="BTCUSDT",
                                         positionSide=position_side,
                                         quantity=quantity,
                                         side=side,
                                         type="MARKET",
                                         )
        time.sleep(1)

    def take_profit_stop_loss(self, type_action, price_stop):
        side = "BUY"
        position_side = "SHORT"
        if self.long:
            side = "SELL"
            position_side = "LONG"
        self.client.futures_create_order(symbol="BTCUSDT",
                                         closePosition="true",
                                         type=str(type_action),
                                         stopPrice=str(price_stop),
                                         side=side,
                                         positionSide=position_side
                                         )
        time.sleep(1)

    def cancel_all_orders(self):
        self.client.futures_cancel_all_open_orders(symbol="BTCUSDT")

    def init_long(self, sl, tp, leverage, quantity):
        Program.place_order(self,
                            position_side="LONG",
                            leverage=leverage,
                            quantity=quantity,
                            side="BUY"
                            )
        Program.take_profit_stop_loss(self, "STOP_MARKET", sl)
        Program.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", tp)

    def init_short(self, sl, tp, leverage, quantity):
        Program.place_order(self,
                            position_side="SHORT",
                            leverage=leverage,
                            quantity=quantity,
                            side="SELL"
                            )
        Program.take_profit_stop_loss(self, "STOP_MARKET", sl)
        Program.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", tp)

    def data_init(self):
        self.data = Program.data(self)
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

    def trade_result_instruction(self, i):
        trade, confirmation, target_hit = Program.init_trade(self, i)
        if confirmation == self.long and target_hit:
            self.trade_in_going = False

    def debug_trade_parameters(self, sl, tp, enter_price, enter_price_index):
        date = Program.get_time(self, enter_price_index)
        print("The enter price is : " + str(enter_price) + " at : " + str(date))
        print("The stop loss is : " + str(sl))
        print("The take profit is : " + str(tp))

    @staticmethod
    def more_readable_numbers(number):
        return format(number, ',')

    def init_trade(self, index):
        prices = self.data['close'].tail(self.study_range).values

        cross_indexes = self.fake_bull_indexes
        wicks_indexes = self.low_wicks_indexes
        confirmation = self.long
        stop_loss = 0
        enter_price, enter_price_index = 0, 0
        take_profit = 0

        if not self.long:
            wicks_indexes = self.high_wicks_indexes
            cross_indexes = self.fake_bear_indexes

        if not self.trade_in_going:
            stop_loss = Program.stop_loss_calc(self, index + 1)
            enter_price, enter_price_index = Program.enter_price_calc(cross_indexes, wicks_indexes,
                                                                      index + 1, prices)
            take_profit = Program.take_profit_calc(self, enter_price, stop_loss)

            confirmation = Program.buy_sell(self, enter_price_index)

        if not self.trade_in_going and self.long == confirmation and enter_price != 0:
            quant, lev = quantity_calculator(self.risk_per_trade, stop_loss, enter_price, self.balance_available)
            time.sleep(1)

            if self.long:
                Program.init_long(self, stop_loss, take_profit, lev, quant)
            else:
                Program.init_short(self, stop_loss, take_profit, lev, quant)

        trade, target_hit = Program.check_first_price_hit(self, stop_loss, take_profit, enter_price_index)

        if self.debug_mode and not self.trade_in_going:
            Program.debug_trade_parameters(self, stop_loss, take_profit, enter_price, enter_price_index)
        if not target_hit and confirmation == self.long and not self.trade_in_going:
            self.trade_in_going = True
            print("Trade in going")

        return trade, confirmation, target_hit

    @staticmethod
    def enter_price_calc(macd_indexes, wicks_indexes, index, prices):
        enter_price_index = Program.macd_cross_detection(macd_indexes, wicks_indexes[index])
        enter_price = prices[enter_price_index]

        return float(enter_price), int(enter_price_index)

    def take_profit_calc(self, enter_price, stop_loss):
        if self.long:
            take_profit = enter_price + (enter_price - stop_loss) * self.risk_ratio
        else:
            take_profit = enter_price - (stop_loss - enter_price) * self.risk_ratio

        return take_profit

    def stop_loss_calc(self, index):
        if self.long:
            buffer = float(self.low_wicks[index]) * self.buffer
            stop_loss = float(self.low_wicks[index]) - buffer
        else:
            buffer = float(self.high_wicks[index]) * self.buffer
            stop_loss = float(self.high_wicks[index]) + buffer

        return float(stop_loss)

    def check_first_price_hit(self, stop_loss, take_profit, index):
        low_wicks = self.data['low'].tail(self.study_range).values
        high_wicks = self.data['high'].tail(self.study_range).values
        target_hit = False
        res = False

        while not target_hit and index < self.study_range:  # Or instead of study range its data range idk.
            if self.long:
                if float(low_wicks[index]) < stop_loss:  # Above SL
                    target_hit = True
                    res = False
                elif float(high_wicks[index]) > take_profit:  # Below TP
                    target_hit = True
                    res = True
            else:
                if float(high_wicks[index]) > stop_loss:  # Above SK
                    target_hit = True
                    res = False
                elif float(low_wicks[index]) < take_profit:  # Below TP
                    target_hit = True
                    res = True

            index += 1

        return res, target_hit

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
        if self.debug_mode:
            Program.debug_macd_trend_data(self, bull_indexes, bear_indexes, fake_bull, fake_bear)

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

    def high_low_finder_v2(self):
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

        if self.debug_mode:
            print("High prices : ")
            Program.idk(self, high_prices_i)
            print(high_prices)
            print("High wicks : ")
            Program.idk(self, high_wicks_i)
            print(high_wicks)
            print("High macd : ")
            print(high_macd)
            Program.idk(self, high_macd_i)
            print("Low prices : ")
            Program.idk(self, low_prices_i)
            print("Low wicks : ")
            Program.idk(self, low_wicks_i)
            print("Low macd : ")
            Program.idk(self, low_macd_i)

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
