from src.Data.indicators import Indicators
from src.Data.data import Data
from src.Data.data_detection_algorithms import Core


class HighLowHistory(Indicators):
    """
    Builds and stores local highs and local lows of macd, candles wicks, and closed prices.
    """
    def __init__(self, client, symbol, symbol_index):
        """
        Initialize the class with the correct data, in accordance to the client and the symbol pair.
        :param client: Client binance API object to get plots data.
        :param symbol: Symbol to also get binance plot data
        :param symbol_index: Somewhat obsolete parameter used to use this strategy on multiple different pairs.
        """
        super().__init__(client, symbol, symbol_index)

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            self.macd_trend_data()

        self.list_r = self.high_low_finder_v2()

        # To me this is just addresses copy. It takes near to no time to do.
        self.high_local, self.high_prices_indexes = self.list_r[0], self.list_r[1]
        self.high_wicks, self.high_wicks_indexes = self.list_r[2], self.list_r[3]
        self.high_macd, self.high_macd_indexes = self.list_r[4], self.list_r[5]

        self.low_local, self.low_prices_indexes = self.list_r[6], self.list_r[7]
        self.low_wicks, self.low_wicks_indexes = self.list_r[8], self.list_r[9]
        self.low_macd, self.low_macd_indexes = self.list_r[10], self.list_r[11]

    def macd_trend_data(self):
        """
        Computes the macd trend. This gives the trend of the macd indicator in function of the candle.
        :return: An array with all the indexes of the beginning of a macd trend. The index corresponds to a price / date
        of the main pandas dataframe.
        """
        last_macd_hist = self.data["Hist"].tail(self.study_range).values

        bull_indexes = []
        bear_indexes = []
        fake_bull = []
        fake_bear = []

        macd_trend = last_macd_hist[0]
        fake_macd_trend = macd_trend
        successive_hist_macd_bear = 0
        successive_hist_macd_bull = 0

        for i in range(self.study_range - 1):  # Fake means that the macd trend calculator doesn't take into account
            # a trigger that, when reached, declares a new trend. This code was for debugging purpose.
            if last_macd_hist[i] > 0 > fake_macd_trend:
                fake_bull.append(i)
                fake_macd_trend = last_macd_hist[i]
            elif last_macd_hist[i] < 0 < fake_macd_trend:
                fake_bear.append(i)
                fake_macd_trend = last_macd_hist[i]

            if last_macd_hist[i] > 0 > macd_trend:  # Bull and bear indexes
                successive_hist_macd_bear = 0
                # croise bullish
                if successive_hist_macd_bull > self.n_plot_macd - 1:
                    # croise avec 4 macd hist plot
                    bull_indexes.append(i - self.n_plot_macd)
                    macd_trend = last_macd_hist[i - self.n_plot_macd]
                    successive_hist_macd_bull = 0
                else:
                    successive_hist_macd_bull += 1
            elif last_macd_hist[i] < 0 < macd_trend:
                successive_hist_macd_bull = 0
                # croise bearish
                if successive_hist_macd_bear > self.n_plot_macd - 1:
                    bear_indexes.append(i - self.n_plot_macd)
                    macd_trend = last_macd_hist[i - self.n_plot_macd]
                    successive_hist_macd_bear = 0
                else:
                    successive_hist_macd_bear += 1
            else:
                successive_hist_macd_bear = 0
                successive_hist_macd_bull = 0

        return bull_indexes, bear_indexes, fake_bull, fake_bear

    def high_low_finder_v2(self):
        """
        Core function that builds the high low arrays.
        :return:
        """
        list_of_high_low = [[], [], [], [], [], [], [], [], [], [], [], []]

        prices = self.data['close'].tail(self.study_range).values
        # candle.
        macd = self.data['MACD'].tail(self.study_range).values
        highs = self.data['high'].tail(self.study_range).values
        lows = self.data['low'].tail(self.study_range).values

        # list_data = [prices, highs, macd]

        lim_bull = len(self.bull_indexes)
        lim_bear = len(self.bear_indexes)

        j = 0
        while j < lim_bull:
            # high prices and macd

            temp_high_low, temp_index = Core.finder(j, self.bear_indexes, self.bull_indexes, prices, True)
            list_of_high_low[0].append(temp_high_low)
            list_of_high_low[1].append(temp_index)

            temp_high_low, temp_index = Core.finder(j, self.bear_indexes, self.bull_indexes, highs, True)
            list_of_high_low[2].append(temp_high_low)
            list_of_high_low[3].append(temp_index)

            temp_high_low, temp_index = Core.finder(j, self.bear_indexes, self.bull_indexes, macd, True)
            list_of_high_low[4].append(temp_high_low)
            list_of_high_low[5].append(temp_index)

            j += 1

        j = 0
        while j < lim_bear:
            # Low prices and macd

            temp_high_low, temp_index = Core.finder(j, self.bull_indexes, self.bear_indexes, prices, False)
            list_of_high_low[6].append(temp_high_low)
            list_of_high_low[7].append(temp_index)

            temp_high_low, temp_index = Core.finder(j, self.bull_indexes, self.bear_indexes, lows, False)
            list_of_high_low[8].append(temp_high_low)
            list_of_high_low[9].append(temp_index)

            temp_high_low, temp_index = Core.finder(j, self.bull_indexes, self.bear_indexes, macd, False)
            list_of_high_low[10].append(temp_high_low)
            list_of_high_low[11].append(temp_index)

            j += 1

        return list_of_high_low

    def indicators_init(self):
        """
        Initialize data. Used when the data set is updated, or when the class is created.
        :return: Nothing.
        """
        self.ema_trend = self.ema(600)
        self.ema_fast = self.ema(150)

        self.macd()

        self.bull_indexes, self.bear_indexes, self.fake_bull_indexes, self.fake_bear_indexes = \
            self.macd_trend_data()

        self.list_r = self.high_low_finder_v2()

        self.high_local, self.high_prices_indexes = self.list_r[0], self.list_r[1]
        self.high_wicks, self.high_wicks_indexes = self.list_r[2], self.list_r[3]
        self.high_macd, self.high_macd_indexes = self.list_r[4], self.list_r[5]

        self.low_local, self.low_prices_indexes = self.list_r[6], self.list_r[7]
        self.low_wicks, self.low_wicks_indexes = self.list_r[8], self.list_r[9]
        self.low_macd, self.low_macd_indexes = self.list_r[10], self.list_r[11]

    def update_data(self):
        """
        Updates the indicators, overriding all preceding data (nothing is stored)
        :return: Nothing.
        """
        self.data = Data.download_data(self)
        self.indicators_init()
