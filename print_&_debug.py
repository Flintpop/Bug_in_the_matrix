import csv
import pandas as pd
import numpy as np


class LogMaster:
    def __init__(self):
        LogMaster.init_csv()
        self.trade_data = LogMaster.get_data()
        print(self.trade_data)
        datas = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]]
        self.trade_data = LogMaster.append_trade_history(self, datas)

    @staticmethod
    def init_csv():
        df = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]]
        df = pd.DataFrame(data=df, columns=['win_loss', 'trade_enter_time',
                                            'money_traded', 'result_money'])
        # ['win_loss', 'trade_enter_time', 'money_traded', 'result_money']
        df.to_csv(r'C:\Users\darwh\Documents\TradeHistory.csv')

    @staticmethod
    def get_data():
        return pd.read_csv(r"C:\Users\darwh\Documents\TradeHistory.csv")

    def append_trade_history(self, list_of_results: list):
        list_of_results = pd.DataFrame(data=list_of_results, columns=['win_loss', 'trade_enter_time',
                                                                      'money_traded', 'result_money'])
        self.trade_data.append(list_of_results, ignore_index=True)
        print(self.trade_data)
        self.trade_data.to_csv(r'C:\Users\darwh\Documents\TradeHistory.csv')
        return pd.read_csv(r"C:\Users\darwh\Documents\TradeHistory.csv")


if __name__ == '__main__':
    oui = LogMaster()
