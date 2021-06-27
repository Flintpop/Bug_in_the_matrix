import time
import datetime as dt
import pandas as pd
from DetectionAlgorithms import Detector

# TODO: Refactor the MACD trend data func, too much code in 1 function
# TODO: Try to make as much functions as possible.


class Data:
    def __init__(self, client):
        self.symbol_trade = 'BTCUSDT'
        self.client = client
        self.interval_unit = '5T'

        self.data_range = 800  # Min is 600 cuz ema.
        self.study_range = self.data_range - 600

        self.data = Data.download_data(self)

    def download_data(self):
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


class Indicators(Data):  # Mb i can put it as a child of data idk.
    def __init__(self, client):
        super().__init__(client)
        self.algorithms = Detector()

        self.ema_trend = self.ema(600)
        self.ema_fast = self.ema(150)
        self.n_plot_macd = 3

        self.macd()

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            self.macd_trend_data()

        self.list_r = self.high_low_finder_v2()

        # I could overhaul this part below
        self.high_local, self.high_prices_indexes = self.list_r[0], self.list_r[1]
        self.high_wicks, self.high_wicks_indexes = self.list_r[2], self.list_r[3]
        self.high_macd, self.high_macd_indexes = self.list_r[4], self.list_r[5]

        self.low_local, self.low_prices_indexes = self.list_r[6], self.list_r[7]
        self.low_wicks, self.low_wicks_indexes = self.list_r[8], self.list_r[9]
        self.low_macd, self.low_macd_indexes = self.list_r[10], self.list_r[11]

    def sma(self, period, column='close'):
        return self.data[column].rolling(window=period).mean()

    def ema(self, period, column='close'):
        return self.data[column].ewm(span=period, adjust=False).mean()

    def macd(self, period_long=26, period_short=12, period_signal=9, column='close'):
        # Calc short term EMA
        short_ema = Indicators.ema(self, period_short, column=column)
        # Calc long term EMA
        long_ema = Indicators.ema(self, period_long, column=column)
        # Calc the MA Convergence divergence (MACD)
        macd = short_ema - long_ema
        self.data['MACD'] = macd
        signal = Indicators.ema(self, period_signal, column="MACD")
        # Signal line
        self.data['Hist'] = macd - signal
        self.data['Signal_Line'] = Indicators.ema(self, period_signal, column='MACD')

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

    def high_low_finder_v2(self):
        # Wait, mb a fundamental bug is here, with the unused fake bear and bull indexes.
        # I could reduce the number of lines here of about 50% maybe;
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
            temp_high_low, temp_index = self.algorithms.finder_high(j, self.bear_indexes, self.bull_indexes, prices)
            high_prices.append(temp_high_low)
            high_prices_i.append(temp_index)

            temp_high_low, temp_index = self.algorithms.finder_high(j, self.bear_indexes, self.bull_indexes, highs)
            high_wicks.append(temp_high_low)
            high_wicks_i.append(temp_index)

            temp_high_low, temp_index = self.algorithms.finder_high(j, self.bear_indexes, self.bull_indexes, macd)
            high_macd.append(temp_high_low)
            high_macd_i.append(temp_index)

            j += 1

        j = 0
        while j < lim_be:
            # Low prices and macd
            temp_high_low, temp_index = self.algorithms.finder_low(j, self.bull_indexes, self.bear_indexes, prices)
            low_prices.append(temp_high_low)
            low_prices_i.append(temp_index)

            temp_high_low, temp_index = self.algorithms.finder_low(j, self.bull_indexes, self.bear_indexes, lows)
            low_wicks.append(temp_high_low)
            low_wicks_i.append(temp_index)

            temp_high_low, temp_index = self.algorithms.finder_low(j, self.bull_indexes, self.bear_indexes, macd)
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

    def macd_line_checker(self, index, long):
        last_macd_data = self.data['MACD'].tail(self.study_range).values

        res = True
        i = 0

        if long:
            start = self.algorithms.macd_cross_detection(self.bull_indexes, index)
            end = self.algorithms.macd_cross_detection(self.bear_indexes, start)

            length = end - start
        else:
            start = self.algorithms.macd_cross_detection(self.bear_indexes, index)
            end = self.algorithms.macd_cross_detection(self.bull_indexes, start)

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

    def data_init(self):  # Didnt test this function, be careful
        self.ema_trend = self.ema(600)
        self.ema_fast = self.ema(150)

        self.macd()

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            self.macd_trend_data()

        list_r = self.high_low_finder_v2()

        self.high_local, self.high_prices_indexes = list_r[0], list_r[1]
        self.high_wicks, self.high_wicks_indexes = list_r[2], list_r[3]
        self.high_macd, self.high_macd_indexes = list_r[4], list_r[5]

        self.low_local, self.low_prices_indexes = list_r[6], list_r[7]
        self.low_wicks, self.low_wicks_indexes = list_r[8], list_r[9]
        self.low_macd, self.low_macd_indexes = list_r[10], list_r[11]

    def update_data(self, time_sleep):
        time.sleep(time_sleep)
        self.data = Data.download_data(self)
        self.data_init()
