import datetime as dt
import time

import pandas as pd
from src.Miscellaneous.settings import Parameters

# the data has to be this way :
# datas = [['BTCUSDT', 'long/short', 1, '2021-06-16 00:20:00', '2021-06-16 10:45:00',104.96, 119.6544]]


def os_path_fix():
    import platform
    current_os = platform.system()
    if current_os == 'Windows':
        string = "src/Output/"
    else:
        string = "../Output/"

    return string


# noinspection PyTypeChecker
class LogMaster:
    def __init__(self):
        self.logs_path = os_path_fix() + "logs.txt"
        self.trade_path = os_path_fix() + "TradeHistory.csv"
        try:
            self.trade_data = self.get_data()
        except Exception as e:
            print("An error occurred")
            print(e)
            self.init_trade_history()
            time.sleep(3)
            print("Trade history initialized")
            self.trade_data = self.get_data()

    def init_trade_history(self):
        df = pd.DataFrame(columns=['symbol', 'trade_type', 'win_loss', 'trade_enter_time', 'trade_close_time',
                                   'money_traded', 'result_money'])
        df.to_csv(self.trade_path, index=False)

    def init_log(self):
        f = open(self.logs_path, "w+")
        f.write("File created at : " + str(dt.datetime.now()) + "\n\n")
        f.close()
        f = open(self.logs_path, "a")
        f.write("Logs initialized.\n")
        f.close()

    def add_log(self, words):
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
            f = open(self.logs_path, "a")
            f.write(str(word))
            f.close()
        except Exception as e:
            print(e)
            f = open(self.logs_path, "a")
            f.write("\n\n" + str(e))
            f.close()

    def get_data(self):
        r = pd.read_csv(self.trade_path)
        return r

    def append_trade_history(self, list_of_results: list):
        self.trade_data = self.get_data()
        list_of_results = pd.DataFrame(data=list_of_results, columns=['symbol', 'trade_type', 'win_loss',
                                                                      'trade_enter_time', 'trade_close_time',
                                                                      'money_traded', 'result_money'])
        frames = [self.trade_data, list_of_results]
        self.trade_data = pd.concat(frames, ignore_index=True)
        self.trade_data.to_csv(self.trade_path, index=False)
        return pd.read_csv(self.trade_path)


class PrintUser:
    def __init__(self, coin_obj):
        self.logs_path = os_path_fix() + "logs.txt"
        self.trade_path = os_path_fix() + "TradeHistory.csv"

        self.data = coin_obj.data
        self.data_range = coin_obj.data_range
        self.study_range = coin_obj.study_range
        self.settings = Parameters()

        self.logs = LogMaster()  # TODO: Potential bug here.
        self.print_log = self.logs.add_log

    def actualize_data(self, coin):
        self.data = coin.data

    def print_trade_aborted(self, crossed, divergence, good_macd_pos, symbol, threshold):
        self.print_log(f"\n\nTrade cancelled on {self.get_current_trade_symbol(symbol)} "
                       f"because of : \n"
                       f"- crossed ? |         {crossed}"
                       f"\n- divergence ? |    {divergence}"
                       f"\n- good_macd_pos ? | {good_macd_pos}"
                       f"\n- threshold ? |     {threshold}")

    def debug_macd_trend_data(self, bull_indexes, bear_indexes, fake_bull, fake_bear):
        bearish_time = []
        bullish_time = []
        fake_bull_time = []
        fake_bear_time = []

        for i in range(len(bull_indexes)):
            date = PrintUser.get_time(self, bull_indexes[i] - 1)
            bullish_time.append(date)
        print("MACD cross bullish at : ")
        print(bullish_time)
        for i in range(len(fake_bull)):
            date = PrintUser.get_time(self, fake_bull[i] - 1)
            fake_bull_time.append(date)
        print("MACD fake bullish at : ")
        print(fake_bull_time)

        for i in range(len(bear_indexes)):
            date = PrintUser.get_time(self, bear_indexes[i] - 1)
            bearish_time.append(date)
        print("MACD cross bearish at : ")
        print(bearish_time)
        for i in range(len(fake_bear)):
            date = PrintUser.get_time(self, fake_bear[i] - 1)
            fake_bear_time.append(date)
        print("MACD fake bearish at : ")
        print(fake_bear_time)

    def print_date_list(self, indexes):
        time_debug = []
        for i in range(len(indexes)):
            date = PrintUser.get_time(self, indexes[i])
            time_debug.append(date)
        return str(time_debug)

    def debug_divergence_finder(self, indexes, i, word):
        string_one = PrintUser.get_time(self, indexes[i])
        string_two = PrintUser.get_time(self, indexes[i + 1])

        string = "\n\nDivergence for " + word + " at : " + str(string_one) + " and " + str(string_two)
        self.logs.add_log(string)

    def debug_trade_parameters(self, trade, symbol):
        log = self.logs.add_log
        date = PrintUser.get_time(self, trade.entry_price_index)

        log(f"\n\n\nIt is a {self.trade_type_string(trade.long)} for the {symbol} market")
        log(f"\nThe entry price is : {trade.entry_price} at : {date}")
        log(f"\nThe stop loss is : {trade.sl}")
        log(f"\nThe take profit is : {trade.tp}")

    def get_current_trade_symbol(self, symbol_index):
        return self.settings.market_symbol_list[symbol_index]

    @staticmethod
    def trade_type_string(long):
        if long:
            res = "long"
        else:
            res = "short"
        return res

    def get_time(self, index):
        time_print = self.data['open_date_time']
        index = index + self.data_range - self.study_range + 2
        try:
            res = time_print[index]
        except Exception as e:
            print(e)
            res = time_print[len(time_print) - 1]
        return res


if __name__ == '__main__':
    a = LogMaster()
    datas = [['BTCUSDT', 'long/short', 1, '2021-06-16 00:20:00', '2021-06-16 10:45:00', 104.96, 119.6544]]
    a.append_trade_history(datas)
