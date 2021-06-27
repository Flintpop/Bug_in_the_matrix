import pandas as pd

# datas = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]] the data has to be this way.


class LogMaster:
    def __init__(self):
        # LogMaster.init_csv()
        self.trade_data = LogMaster.get_data()

    @staticmethod
    def init_csv():
        # df = [[1, '2021-06-16 00:20:00', 104.96, 119.6544]]
        df = pd.DataFrame(columns=['win_loss', 'trade_enter_time',
                                   'money_traded', 'result_money'])
        # ['win_loss', 'trade_enter_time', 'money_traded', 'result_money']
        df.to_csv(r'C:\Users\darwh\Documents\TradeHistory.csv', index=False)

    @staticmethod
    def get_data():
        r = pd.read_csv(r"C:\Users\darwh\Documents\TradeHistory.csv")
        return r

    def append_trade_history(self, list_of_results: list):
        list_of_results = pd.DataFrame(data=list_of_results, columns=['win_loss', 'trade_enter_time',
                                                                      'money_traded', 'result_money'])
        frames = [self.trade_data, list_of_results]
        self.trade_data = pd.concat(frames, ignore_index=True)
        self.trade_data.to_csv(r'C:\Users\darwh\Documents\TradeHistory.csv', index=False)
        return pd.read_csv(r"C:\Users\darwh\Documents\TradeHistory.csv")


if __name__ == '__main__':
    oui = LogMaster()
