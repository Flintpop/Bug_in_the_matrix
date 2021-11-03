import datetime as dt
import pandas as pd

from src.Miscellaneous.settings import Parameters


class Data:
    def __init__(self, client, symbol):
        settings = Parameters()
        self.symbol = symbol
        self.client = client
        self.interval_unit = settings.interval_unit

        self.data_range = settings.data_range
        self.study_range = settings.study_range
        self.n_plot_macd = settings.n_plot_macd

        self.data = Data.download_data(self)

    def download_data(self):
        if self.interval_unit == '5T':
            start_min = (self.data_range + 1) * 5
            start_str = str(start_min) + ' minutes ago UTC'
            interval_data = '5m'

            data = self.data_download(start_str, interval_data)

            return data

    def data_download(self, start_str, interval_data):
        data = pd.DataFrame(
            self.client.futures_historical_klines(symbol=self.symbol, start_str=start_str,
                                                  interval=interval_data))

        data.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
                        'taker_base_vol', 'taker_quote_vol', 'is_best_match']
        data['open_date_time'] = [dt.datetime.fromtimestamp(x / 1000) for x in data.open_time]
        data = data[['open_date_time', 'open', 'high', 'low', 'close', 'volume']]
        return data
