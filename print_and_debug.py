import datetime as dt

import pandas as pd

# datas = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]] the data has to be this way.


class LogMaster:
    def __init__(self):

        self.init_csv()
        try:
            self.trade_data = self.get_data()
        except FileNotFoundError:
            self.init_csv()
            self.trade_data = self.get_data()

    @staticmethod
    def init_csv():
        # df = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]]
        df = pd.DataFrame(columns=['win_loss', 'trade_enter_time',
                                   'money_traded', 'result_money'])
        # ['win_loss', 'trade_enter_time', 'money_traded', 'result_money']
        df.to_csv('TradeHistory.csv', index=False)

    @staticmethod
    def get_data():
        r = pd.read_csv("TradeHistory.csv")
        return r

    def append_trade_history(self, list_of_results: list):
        list_of_results = pd.DataFrame(data=list_of_results, columns=['win_loss', 'trade_enter_time',
                                                                      'money_traded', 'result_money'])
        frames = [self.trade_data, list_of_results]
        self.trade_data = pd.concat(frames, ignore_index=True)
        self.trade_data.to_csv('TradeHistory.csv', index=False)
        return pd.read_csv("TradeHistory.csv")


class PrintUser:
    def __init__(self, coin_obj):
        self.data = coin_obj.data
        self.data_range = coin_obj.data_range
        self.study_range = coin_obj.study_range

    def actualize_data(self, coin):
        self.data = coin.data
        self.data_range = coin.data_range
        self.study_range = coin.study_range

    def debug_macd_trend_data(self, bull_indexes, bear_indexes, fake_bull, fake_bear):
        bearish_time = []
        bullish_time = []
        fake_bull_time = []
        fake_bear_time = []

        for i in range(len(bull_indexes)):
            date = PrintUser.get_time(self, bull_indexes[i])
            bullish_time.append(date)
        print("MACD cross bullish at : ")
        print(bullish_time)
        for i in range(len(fake_bull)):
            date = PrintUser.get_time(self, fake_bull[i])
            fake_bull_time.append(date)
        print("MACD fake bullish at : ")
        print(fake_bull_time)

        for i in range(len(bear_indexes)):
            date = PrintUser.get_time(self, bear_indexes[i])
            bearish_time.append(date)
        print("MACD cross bearish at : ")
        print(bearish_time)
        for i in range(len(fake_bear)):
            date = PrintUser.get_time(self, fake_bear[i])
            fake_bear_time.append(date)
        print("MACD fake bearish at : ")
        print(fake_bear_time)

    def idk(self, indexes):
        time_debug = []
        for i in range(len(indexes)):
            date = PrintUser.get_time(self, indexes[i])
            time_debug.append(date)
        print(time_debug)

    def debug_divergence_finder(self, indexes, i, word):
        string_one = PrintUser.get_time(self, indexes[i])
        string_two = PrintUser.get_time(self, indexes[i + 1])

        print("Divergence for " + word + " at : " + str(string_one) + " and " + str(string_two))

    def debug_trade_parameters(self, sl, tp, enter_price, enter_price_index):
        date = PrintUser.get_time(self, enter_price_index)
        print("The enter price is : " + str(enter_price) + " at : " + str(date))
        print("The stop loss is : " + str(sl))
        print("The take profit is : " + str(tp))

    def get_time(self, index):
        time_print = self.data['open_date_time']
        index = index + self.data_range - self.study_range + 1
        return time_print[index]

    @staticmethod
    def debug_file():
        f = open("debug_file.txt", "w+")
        f.write("File created at : " + str(dt.datetime.now()))
        f.close()


if __name__ == '__main__':
    oui = LogMaster()
