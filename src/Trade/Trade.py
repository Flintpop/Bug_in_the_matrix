from WarnUser import Warn
from src.Miscellanous.Settings import Parameters
from src.Data.High_Low_Data import HighLowHistory
import datetime
import time


class Trade:
    def __init__(self, coin: HighLowHistory, client, log):
        settings = Parameters()
        self.risk_ratio = settings.risk_ratio
        self.risk_per_trade = settings.risk_per_trade_brut
        self.risk_per_trade_brut = self.risk_per_trade
        self.risk_per_trade = 1 - self.risk_per_trade / 100
        self.warn = Warn()

        self.buffer = settings.buffer
        self.client = client

        self.long = coin.long
        self.data = coin.data
        self.study_range = settings.study_range
        self.log = log

        self.high_wicks, self.high_wicks_indexes = coin.list_r[2], coin.list_r[3]
        self.low_wicks, self.low_wicks_indexes = coin.list_r[8], coin.list_r[9]
        self.fake_bull_indexes = coin.fake_bull_indexes
        self.fake_bear_indexes = coin.fake_bear_indexes

        self.trade_in_going = False

        self.infos = self.client.futures_account()

        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

        self.stop_loss = 0
        self.entry_price, self.entry_price_index = 0, 0
        self.take_profit = 0

        self.quantity, self.leverage = 0, 0

    def init_calculations(self):
        if not self.trade_in_going:
            self.entry_price, self.entry_price_index = self.entry_price_calc()
            self.stop_loss = Trade.stop_loss_calc(self)
            self.take_profit = Trade.take_profit_calc(self, self.entry_price, self.stop_loss)

            self.trade_in_going = True
            self.log("\n\nTrade in going !")

            self.current_balance = float(self.infos["totalMarginBalance"])
            self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

            self.quantity, self.leverage = Trade.quantity_calculator(self, self.balance_available)

    def entry_price_calc(self):
        prices = self.data['close'].tail(10).values
        enter_price_index = len(prices) - 2
        entry_price = prices[enter_price_index]

        return float(entry_price), int(enter_price_index)

    def take_profit_calc(self, enter_price, stop_loss):
        if self.long:
            take_profit = enter_price + (enter_price - stop_loss) * self.risk_ratio
        else:
            take_profit = enter_price - (stop_loss - enter_price) * self.risk_ratio
        take_profit.__round__()

        return int(take_profit)

    def stop_loss_calc(self):
        low_l = len(self.low_wicks) - 1
        high_l = len(self.high_wicks) - 1
        if self.long:
            buffer = float(self.low_wicks[low_l]) * self.buffer
            stop_loss = float(self.low_wicks[low_l]) - buffer
        else:
            buffer = float(self.high_wicks[high_l]) * self.buffer
            stop_loss = float(self.high_wicks[high_l]) + buffer
        print("The stop loss is : " + str(stop_loss))
        stop_loss.__round__()

        if (stop_loss > self.entry_price and self.long) or (stop_loss < self.entry_price and not self.long):
            self.log("Fatal error, could not calculate properly the stop loss; due likely to self.high/low_wicks "
                     "to not be correct.")
            long_word = self.warn.trade_type_string(self.long)
            self.log(f"It was a {long_word}\n High wicks : {self.high_wicks}\n Low wicks : {self.low_wicks}\n"
                     f"Data : \n{self.data}\n At : {datetime.datetime.now()}\n")
            raise ValueError
        return int(stop_loss)

    def add_to_trade_history(self, win, time_pos_open, time_pos_hit, money, debug):
        if win:
            end_money = money * (1 + (self.risk_per_trade_brut / 100 * self.risk_ratio))
            win = 1
        else:
            end_money = money * self.risk_per_trade
            win = 0
        datas = [[win, time_pos_open, time_pos_hit, money, end_money]]
        debug.append_trade_history(datas)

    def quantity_calculator(self, money_available):
        money_divided = 1
        money_traded = money_available / money_divided

        percentage_risked_trade = self.percentage_risk_calculation()
        self.log("\n\nThe percentage risked on the trade is wo leverage : " + str(percentage_risked_trade))
        leverage = self.leverage_calculation(percentage_risked_trade, money_divided)
        self.log("\nThe leverage is : " + str(leverage))

        quantity = (money_traded / self.entry_price) * leverage
        quantity = quantity - 0.001
        quantity = quantity.__round__(3)

        self.log("\nMaximum loss of current trade : " +
                 str(float(leverage * percentage_risked_trade).__round__()) + " %")

        self.log("\nThe quantity is : " + str(quantity) + " BTC")

        return quantity, leverage

    def leverage_calculation(self, percentage_risked, money_divided):
        self.log("\nThe diviseur in leverage calc is : " + str(percentage_risked * self.risk_per_trade_brut))
        leverage = (1 / percentage_risked * self.risk_per_trade_brut) * money_divided
        leverage = leverage.__round__()
        self.correct_leverage(leverage=leverage, risk_trade=percentage_risked)
        return int(leverage)

    def percentage_risk_calculation(self):
        if self.stop_loss < self.entry_price:  # Determine if short or long, which change the operation
            percentage_risked_trade = (1 - self.stop_loss / self.entry_price) * 100  # long
        else:
            percentage_risked_trade = (1 - self.entry_price / self.stop_loss) * 100  # short
        return percentage_risked_trade

    @staticmethod
    def correct_leverage(leverage, risk_trade):
        while leverage * risk_trade * 1.5 >= 100:  # Not tested. Looks to work
            print("\nHigh risk of liquidation ! Reducing leverage...")
            leverage = leverage - ((leverage * 0.1).__round__())
        if leverage >= 125:
            print("\nLeverage too high. The platform cannot handle it.")
            leverage = 120
        elif leverage < 1:
            print("\nLeverage inferior to 1 !")
            leverage = 1
        return leverage


class BinanceOrders(Trade):
    def __init__(self, coin, client, log, symbol):
        super().__init__(coin, client, log)

        BinanceOrders.cancel_all_orders(self, symbol)

    def open_trade(self, symbol):
        if self.long:
            side = "BUY"
            position_side = "LONG"
        else:
            side = "SELL"
            position_side = "SHORT"

        BinanceOrders.place_order(self,
                                  position_side=position_side,
                                  side=side,
                                  symbol=symbol
                                  )

    def place_sl_and_tp(self, symbol):
        BinanceOrders.take_profit_stop_loss(self, "STOP_MARKET", self.stop_loss, symbol)
        BinanceOrders.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", self.take_profit, symbol)

    def place_order(self, position_side, side, symbol):
        self.client.futures_change_leverage(symbol=symbol, leverage=str(self.leverage))
        time.sleep(4)
        print(self.quantity)
        self.client.futures_create_order(symbol=symbol,
                                         positionSide=position_side,
                                         quantity=self.quantity,
                                         side=side,
                                         type="MARKET",
                                         )

    def cancel_all_orders(self, symbol):
        self.client.futures_cancel_all_open_orders(symbol=symbol)

    def take_profit_stop_loss(self, type_action, price_stop, symbol):
        side = "BUY"
        position_side = "SHORT"
        if self.long:
            side = "SELL"
            position_side = "LONG"
        self.client.futures_create_order(symbol=symbol,
                                         closePosition="true",
                                         type=str(type_action),
                                         stopPrice=str(price_stop),
                                         side=side,
                                         positionSide=position_side
                                         )
