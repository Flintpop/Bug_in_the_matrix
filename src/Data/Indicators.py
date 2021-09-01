from src.Data.data import Data


class Indicators(Data):
    def __init__(self, client, symbol):
        super().__init__(client, symbol)

        self.ema_trend = self.ema(600)
        self.ema_fast = self.ema(150)

        self.macd()

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
