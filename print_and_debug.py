import datetime as dt

import pandas as pd

# datas = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]] the data has to be this way.


class LogMaster:
    def __init__(self):
        try:
            self.trade_data = self.get_data()
        except FileNotFoundError:
            self.init_trade_history()
            print("Log file initialized")
            self.trade_data = self.get_data()

    @staticmethod
    def init_trade_history():
        df = pd.DataFrame(columns=['win_loss', 'trade_enter_time', 'money_traded', 'result_money'])
        df.to_csv('TradeHistory.csv', index=False)

    @staticmethod
    def init_log():
        f = open("logs.txt", "w+")
        f.write("File created at : " + str(dt.datetime.now()) + "\n\n")
        f.close()
        f = open("logs.txt", "a")
        f.write("Logs initialized.\n")
        f.close()

    @staticmethod
    def add_log(words):
        try:
            if type(words) == str:
                word_print = words.replace("\n", "")
                word = words
            elif type(words) == bool:
                word_print = words
                word = "\n\n" + str(words)
            else:
                word_print = words
                word = words
            print(word_print)
            f = open("logs.txt", "a")
            f.write(str(word))
            f.close()
        except Exception as e:
            print(e)
            f = open("logs.txt", "a")
            f.write("\n\n" + str(e))
            f.close()

    @staticmethod
    def get_data():
        r = pd.read_csv("TradeHistory.csv")
        return r

    def append_trade_history(self, list_of_results: list):
        self.trade_data = self.get_data()
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
        
        self.logs = LogMaster()

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
        return str(time_debug)

    def debug_divergence_finder(self, indexes, i, word):
        string_one = PrintUser.get_time(self, indexes[i])
        string_two = PrintUser.get_time(self, indexes[i + 1])
        
        string = "\n\nDivergence for " + word + " at : " + str(string_one) + " and " + str(string_two)
        print(string)
        self.logs.add_log(string)

    def debug_trade_parameters(self, sl, tp, entry_price, enter_price_index, long):
        date = PrintUser.get_time(self, enter_price_index)

        string = "\n\nIt is a long ? | " + str(long) + "\n" + "The enter price is : " + str(entry_price) + " at : " + \
                 str(date) + "\n" + "The stop loss is : " + str(sl) + "\n" + "The take profit is : " + str(tp)
        print("It is a long ? | " + str(long))
        print("The enter price is : " + str(entry_price) + " at : " + str(date))
        print("The stop loss is : " + str(sl))
        print("The take profit is : " + str(tp))

        self.logs.add_log(string)

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
    a = LogMaster()
    a.add_log(0 > 1)
