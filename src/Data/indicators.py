import numpy as np

from src.Data.data import Data


class Indicators(Data):
    def __init__(self, client, symbol, symbol_index):
        super().__init__(client, symbol, symbol_index)
        self.long = None

        self.ema_trend = self.ema(600)
        self.ema_fast = self.ema(150)

        self.data['ema20'] = self.ema(period=self.settings.ema_fractals_ema[0])
        self.data['ema50'] = self.ema(period=self.settings.ema_fractals_ema[1])
        self.data['ema100'] = self.ema(period=self.settings.ema_fractals_ema[2])

        self.macd()

    def actualize_data_ema_fractals(self):
        # Initializing necessary emas.
        self.data['ema20'] = self.ema(period=self.settings.ema_fractals_ema[0])
        self.data['ema50'] = self.ema(period=self.settings.ema_fractals_ema[1])
        self.data['ema100'] = self.ema(period=self.settings.ema_fractals_ema[2])

    def sma(self, period, column='close'):
        return self.data[column].rolling(window=period).mean()

    def ema(self, period, column='close'):
        return self.data[column].ewm(span=period, adjust=False).mean()

    def macd(self, period_long=26, period_short=12, period_signal=9, column='close'):
        # Calc short term EMA
        short_ema = self.ema(period_short, column=column)
        # Calc long term EMA
        long_ema = self.ema(period_long, column=column)
        # Calc the MA Convergence divergence (MACD)
        macd = short_ema - long_ema
        self.data['MACD'] = macd
        signal = Indicators.ema(self, period_signal, column="MACD")
        # Signal line
        self.data['Hist'] = macd - signal
        self.data['Signal_Line'] = Indicators.ema(self, period_signal, column='MACD')

    def rsi(self):
        self.data['returns'] = self.data['close'].pct_change()
        self.data['up'] = np.maximum(self.data['close'].diff(), 0)
        self.data['down'] = np.maximum(-self.data['close'].diff(), 0)
        self.data['rs'] = self.data['up'].rolling(self.settings.rsi_period).mean() / \
                          self.data['down'].rolling(self.settings.rsi_period).mean()
        self.data['rsi'] = 100 - 100 / (1 + self.data['rs'])
