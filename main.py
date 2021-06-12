# import numpy as np
from binance.client import Client
import datetime as dt
import pandas as pd


class Program:
    def __init__(self):
        self.client = Client("hn2OOw1SdmnFBf3SYRNa4sruUBj8LFAbUFcYYVLYxEkXdRP48EUb8NutLI2gKRRb",
                             "pkwUZomAYay2rC8I1QjPMbE55wv4zeKinwb5GCu5x0EtF3BOnbIj5E5o7MRO9kmT")

        # What to trade
        self.symbol_trade = 'BTCUSDT'

        # Order quantity in $
        # order_dollar = 12

        self.interval_unit = "5T"
        self.long = False

        self.debug_mode = True

        self.study_range = 20000
        self.data_range = 299166
        self.debug_trades = []

        self.n_plot_macd = 3

        self.risk_ratio = 0.675
        self.list_risk_ratio = [2, 4, 6, 7, 8, 9, 10]
        self.buffer = 0.001
        self.ema_buffer = 0.004
        # Seems the best value for now. Optimization possible by increasing the
        # value when the price is lower, thus taking more into consideration the volatility of the market
        # (Crypto market)
        self.risk_per_trade = 21
        self.risk_per_trade = 1 - self.risk_per_trade / 100

        self.download_mode = False
        if self.download_mode:
            self.data = Program.data(self)
            self.data.to_csv(r'C:\Users\darwh\Documents\btc_chart_excel_long_three.csv')
        else:
            # self.data = pd.read_excel(r'C:\Users\darwh\Documents\btc_chart_excel_long_two.xlsx')
            self.data = pd.read_csv(r'C:\Users\darwh\Documents\btc_chart_csv_long_three.csv')

        self.ema_trend = Program.ema(self, 600)
        self.ema_fast = Program.ema(self, 150)
        self.money = 100
        self.start_money = self.money

        Program.macd(self)

        print(self.data["open_date_time"].tail(self.study_range))

        self.bull_indexes, self.bear_indexes = Program.macd_trend_data(self)
        self.trade_count = 0
        self.trade_won = 0
        self.trade_lost = 0
        self.trade_aborted = False

        self.short_won = 0
        self.short_lost = 0
        self.long_won = 0
        self.long_lost = 0

        self.win_streak = 0
        self.loss_streak = 0

        self.low_local, self.low_prices_indexes = Program.high_low_finder(self, 'close', 'low')
        self.low_macd, self.low_macd_indexes = Program.high_low_finder(self, 'Hist', 'low')
        self.low_wicks, self.low_wicks_indexes = Program.high_low_finder(self, 'low', 'low')
        # There lacks the ends in the high_low_finder
        # and the high finders but not in the lows finders.

        self.high_local, self.high_prices_indexes = Program.high_low_finder(self, 'close', 'high')
        # high_low_finder doesnt work for highs.
        self.high_macd, self.high_macd_indexes = Program.high_low_finder(self, 'Hist', 'high')
        # Actually all the high algo do not work.
        self.high_wicks, self.high_wicks_indexes = Program.high_low_finder(self, 'high', 'high')

        for j in range(1):
            # self.risk_ratio = self.list_risk_ratio[j]

            print("\nEntered long scanning\n")

            for i in range(len(self.low_local) - 1):
                self.long = Program.buy_sell(self, self.low_prices_indexes[i])
                if self.long:
                    self.long = Program.buy_sell(self, self.low_prices_indexes[i + 1])

                if self.low_local[i] > self.low_local[i + 1] and self.low_macd[i] < self.low_macd[i + 1] and self.long:
                    res = Program.macd_line_checker(self, self.low_prices_indexes[i], self.long)
                    if res:
                        Program.trade_result_instruction(self, self.low_prices_indexes, i, "long")

            print("\nEntered short scanning\n")

            for i in range(len(self.high_local) - 1):
                self.long = Program.buy_sell(self, self.high_prices_indexes[i])
                if not self.long:
                    self.long = Program.buy_sell(self, self.high_prices_indexes[i + 1])

                if self.high_local[i] < self.high_local[i + 1] and self.high_macd[i] > self.high_macd[i + 1] and not self.long:
                    res = Program.macd_line_checker(self, self.high_prices_indexes[i], self.long)
                    if res:
                        Program.trade_result_instruction(self, self.high_prices_indexes, i, "short")

            Program.print_result(self)
            # Program.check_result(self)

    def win_loss_streak_calculator(self):
        self.loss_streak = 0
        self.win_streak = 0
        n_win = 0
        n_loss = 0
        for i in range(len(self.debug_trades)):
            if self.debug_trades[i] == 1:
                n_win += 1
                n_loss = 0
                if n_win > self.win_streak:
                    self.win_streak = n_win
            else:
                n_loss += 1
                n_win = 0
                if n_loss > self.loss_streak:
                    self.loss_streak = n_loss

    @staticmethod
    def forex_data():
        data = pd.read_csv(r'C:\Users\darwh\Downloads\EURUSD_M5_200000.csv', sep="\t")
        data.columns = ['open_date_time', 'open', 'high', 'low', 'close', 'volume']
        # data['open_date_time'] = [dt.datetime.fromtimestamp(x / 1000) for x in data.Time]

        # data = data[['open_date_time', 'open', 'high', 'low', 'close', 'volume']]

        data = data.set_index('open_date_time')

        return data

    def debug_divergence_finder(self, indexes, i, word):
        string_one = Program.get_time(self, indexes[i])
        string_two = Program.get_time(self, indexes[i + 1])

        print("Divergence for " + word + " at : " + str(string_one) + " and " + str(string_two))

    def trade_result_instruction(self, prices_index, i, word):
        if self.debug_mode:
            Program.debug_divergence_finder(self, prices_index, i, word)

        trade, confirmation = Program.init_trade(self, i + 1)
        if confirmation == self.long:
            Program.trade_and_money_update(self, trade)
            self.trade_count += 1

    @staticmethod
    def debug_trade_parameters(sl, tp, enter_price):
        print("The enter price is : " + str(enter_price))
        print("The stop loss is : " + str(sl))
        print("The take profit is : " + str(tp))

    def print_result(self):
        print("\nThere was " + str(self.trade_count) + " trade possible.")
        print("There was " + str(self.trade_won) + " trade won.")
        print("There was " + str(self.trade_lost) + " trade lost.")

        print("\nThere was " + str(self.short_won) + " short won")
        print("There was " + str(self.short_lost) + " short lost")

        print("\nThere was " + str(self.long_won) + " long won")
        print("There was " + str(self.long_lost) + " long lost")

        win_rate = self.trade_won / self.trade_count * 100

        n_short = self.short_won + self.short_lost
        n_long = self.long_won + self.long_lost
        n_short = self.short_won / n_short * 100
        n_long = self.long_won / n_long * 100
        print_var1 = "\nIt is a " + str(win_rate) + " % win rate"
        print_var2 = " with " + str(n_short) + " % short won" + " and " + str(n_long) + " % long won"
        print_var1 += print_var2
        print(print_var1)

        self.money = self.money.__round__()
        print_money = Program.more_readable_numbers(self.money)

        print("\nEven with shit recognition and shit algorithm, you would end up with : " + print_money + "€")

        gain = ((self.money / self.start_money) - 1) * 100
        gain = gain.__round__()
        gain = Program.more_readable_numbers(gain)
        print("Which is a " + str(gain) + " % gain")

        print(self.debug_trades)
        Program.win_loss_streak_calculator(self)

        print("Win streak : " + str(self.win_streak))
        print("Loss streak : " + str(self.loss_streak))

        Program.trade_money_reset(self)

    @staticmethod
    def more_readable_numbers(number):
        return format(number, ',')

    def trade_money_reset(self):
        self.trade_won = 0
        self.trade_lost = 0
        self.trade_count = 0
        self.money = self.start_money

    def trade_and_money_update(self, trade):
        if trade:
            self.trade_won += 1
            self.money = self.money * (1 + (1 - self.risk_per_trade) * self.risk_ratio)
            self.debug_trades.append(1)
            Program.short_long_stats_update(self, trade)
            if self.debug_mode:
                print("Trade won !\n")
        else:
            self.trade_lost += 1
            self.money = self.money * self.risk_per_trade
            self.debug_trades.append(0)
            Program.short_long_stats_update(self, trade)
            if self.debug_mode:
                print("Trade lost !\n")

    def short_long_stats_update(self, trade):
        if self.long:
            if trade:
                self.long_won += 1
            else:
                self.long_lost += 1
        else:
            if trade:
                self.short_won += 1
            else:
                self.short_lost += 1

    @staticmethod
    def debug_conditions(local, macd, i, word):
        if word == "long":
            print(
                "Conditions are : " + str(local[i]) + " > ? " + str(local[i + 1]) + " | " + str(
                    local[i] > local[i + 1]))
            print("And are : " + str(macd[i]) + " < ? " + str(macd[i + 1]) + " | " + str(
                macd[i] < macd[i + 1]) + "\n")
        else:
            print(
                "Conditions are : " + str(local[i]) + " > ? " + str(local[i + 1]) + " | " + str(
                    local[i] > local[i + 1]))
            print("And are : " + str(macd[i]) + " < ? " + str(macd[i + 1]) + " | " + str(
                macd[i] < macd[i + 1]) + "\n")

    def init_trade(self, index):
        prices = self.data['close'].tail(self.study_range).values

        cross_indexes = self.bull_indexes
        wicks_indexes = self.low_wicks_indexes
        if not self.long:
            wicks_indexes = self.high_wicks_indexes
            cross_indexes = self.bear_indexes

        stop_loss = Program.stop_loss_calc(self, index)
        enter_price, enter_price_index = Program.enter_price_calc(cross_indexes, wicks_indexes,
                                                                  index, prices)
        take_profit = Program.take_profit_calc(self, enter_price, stop_loss)
        confirmation = Program.buy_sell(self, enter_price_index)
        trade = Program.check_first_price_hit(self, stop_loss, take_profit, enter_price_index)

        if self.debug_mode:
            Program.debug_trade_parameters(stop_loss, take_profit, enter_price)

        return trade, confirmation

    @staticmethod
    def enter_price_calc(macd_indexes, wicks_indexes, index, prices):
        enter_price_index = Program.macd_cross_detection(macd_indexes, wicks_indexes[index])
        enter_price = prices[enter_price_index]

        return enter_price, enter_price_index

    def take_profit_calc(self, enter_price, stop_loss):
        if self.long:
            take_profit = enter_price + (enter_price - stop_loss) * self.risk_ratio
        else:
            take_profit = enter_price - (stop_loss - enter_price) * self.risk_ratio

        return take_profit

    def stop_loss_calc(self, index):
        if self.long:
            buffer = self.low_wicks[index] * self.buffer
            stop_loss = self.low_wicks[index] - buffer
        else:
            buffer = self.high_wicks[index] * self.buffer
            stop_loss = self.high_wicks[index] + buffer

        return stop_loss

    def check_first_price_hit(self, stop_loss, take_profit, index):
        low_wicks = self.data['low'].tail(self.study_range).values
        high_wicks = self.data['high'].tail(self.study_range).values
        target_hit = False
        res = False

        while not target_hit and index < self.study_range:  # Or instead of study range its data range idk.
            if self.long:
                if low_wicks[index] < stop_loss:  # Above SL
                    target_hit = True
                    res = False
                elif high_wicks[index] > take_profit:  # Below TP
                    target_hit = True
                    res = True
            else:
                if high_wicks[index] > stop_loss:  # Above SK
                    target_hit = True
                    res = False
                elif low_wicks[index] < take_profit:  # Below TP
                    target_hit = True
                    res = True

            index += 1
        return res

    def data(self):
        if self.interval_unit == '5T':
            start_min = (self.data_range + 1) * 5
            start_str = str(start_min) + ' minutes ago UTC'
            # start_str = '10000 minutes ago UTC'
            interval_data = '5m'

            data = pd.DataFrame(
                self.client.get_historical_klines(symbol=self.symbol_trade, start_str=start_str,
                                                  interval=interval_data))

            data.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
                            'taker_base_vol', 'taker_quote_vol', 'is_best_match']
            data['open_date_time'] = [dt.datetime.fromtimestamp(x / 1000) for x in data.open_time]

            data = data[['open_date_time', 'open', 'high', 'low', 'close', 'volume']]

            data = data.set_index('open_date_time')

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
        self.data['Short_MACD_EMA'] = Program.ema(self, period_short, column=column)
        self.data['Signal_Line'] = Program.ema(self, period_signal, column='MACD')

    def macd_trend_data(self):
        last_150_hist_macd = self.data["Hist"].tail(self.study_range).values

        bull_indexes = []
        bear_indexes = []
        macd_trend = last_150_hist_macd[0]
        successive_hist_macd_bear = 0
        successive_hist_macd_bull = 0

        for i in range(self.study_range):
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

        # Program.debug_macd_trend_data(self, bull_indexes, bear_indexes)

        return bull_indexes, bear_indexes

    def debug_macd_trend_data(self, bull_indexes, bear_indexes):
        # Printing debugging code
        bearish_time = []
        bullish_time = []

        for i in range(len(bull_indexes)):
            date = Program.get_time(self, bull_indexes[i])
            bullish_time.append(date)
        print("MACD cross bullish at : ")
        print(bullish_time)

        for i in range(len(bear_indexes)):
            date = Program.get_time(self, bear_indexes[i])
            bearish_time.append(date)
        print("MACD cross bearish at : ")
        print(bearish_time)

    def macd_last_cross(self):
        if self.bear_indexes > self.bull_indexes:
            return "bear"
        else:
            return "bull"

    def high_low_finder(self, type_of_data, high_low):
        high_low_prices = []
        indexes = []
        temp_index = 0

        prices = self.data[type_of_data].tail(self.study_range).values
        len_of_if = self.study_range
        length_bear_indexes = Program.get_length(self)

        # last_cross = Program.macd_last_cross(self)

        check = abs(self.bear_indexes[0] - self.bull_indexes[0])
        j = 0

        while check < len_of_if and j < length_bear_indexes:
            if high_low == "low":
                temp_high_low = 1000000
                check_add = self.bear_indexes
            else:
                check_add = self.bull_indexes
                temp_high_low = 0

            check = abs(self.bear_indexes[j] - self.bull_indexes[j]) + check_add[j]  # Check if out of range

            if high_low == 'high':
                for i in range(abs(self.bear_indexes[j + 1] - self.bull_indexes[j])):
                    if float(prices[i + self.bull_indexes[j]]) > float(temp_high_low):
                        temp_high_low = prices[i + self.bull_indexes[j]]
                        temp_index = i + self.bull_indexes[j]
            elif high_low == 'low':
                for i in range(abs(self.bear_indexes[j] - self.bull_indexes[j])):
                    if float(prices[i + self.bear_indexes[j]]) < float(temp_high_low):  # Low
                        temp_high_low = prices[i + self.bear_indexes[j]]
                        temp_index = i + self.bear_indexes[j]

            high_low_prices.append(temp_high_low)
            indexes.append(temp_index)
            j += 1

        # time_indexes = []
        #
        # for i in range(len(indexes)):
        #     time_indexes.append(Program.get_time(self, indexes[i]))

        # word = "Error"
        #
        # if type_of_data == "close":
        #     if high_low == "high":
        #         word = "highest prices"
        #     else:
        #         word = "lowest prices"
        # elif type_of_data == "high":
        #     word = "highest wicks"
        # elif type_of_data == "low":
        #     word = "lowest wicks"
        # elif type_of_data == "Hist":
        #     if high_low == "high":
        #         word = "highest MACD"
        #     else:
        #         word = "lowest MACD"
        #
        # print("The  " + word + " are : ")
        # print(time_indexes)

        return high_low_prices, indexes

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
    def macd_cross_detection(macd_indexes, value):
        crossed = False
        k = 0
        v = 0
        while not crossed:
            if macd_indexes[k] > value:
                v = macd_indexes[k]
                crossed = True
            k += 1
        return v

    def get_length(self):  # I think its a flawed function.
        if len(self.bear_indexes) > len(self.bull_indexes):
            length = len(self.bull_indexes)
        else:
            length = len(self.bear_indexes)
        return length

    def get_time(self, index):
        time = self.data['open_date_time']
        index = index + self.data_range - self.study_range + 1
        return time[index]

    def check_result(self):
        money = 100
        cash_out = 0
        for i in range(len(self.debug_trades)):
            if self.debug_trades[i] == 1:
                money = money * (1 + (1 - self.risk_per_trade) * self.risk_ratio)
                cash_out += money * 0.005
                money = money * 0.995
            else:
                money = money * self.risk_per_trade
                money += cash_out * 0.1
                cash_out = cash_out * 0.9
            print("Debug money : " + money.__format__(','))
            print("You have saved : " + cash_out.__format__(','))


if __name__ == '__main__':
    program = Program()
