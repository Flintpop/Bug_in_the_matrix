import time
from binance.client import Client


class Trade:
    def __init__(self, long, data, list_r, study_range, fake_b_indexes, client):

        self.risk_ratio = 0.675
        self.risk_per_trade = 21
        self.risk_per_trade_brut = self.risk_per_trade
        self.risk_per_trade = 1 - self.risk_per_trade / 100

        self.buffer = 0.001
        self.client = client

        self.long = long
        self.data = data
        self.study_range = study_range

        self.high_wicks, self.high_wicks_indexes = list_r[2], list_r[3]
        self.low_wicks, self.low_wicks_indexes = list_r[8], list_r[9]
        self.fake_bull_indexes = fake_b_indexes[0]
        self.fake_bear_indexes = fake_b_indexes[1]

        self.trade_in_going = False

        self.infos = self.client.futures_account()

        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

        self.stop_loss = 0
        self.entry_price, self.enter_price_index = 0, 0
        self.take_profit = 0

        self.quantity, self.leverage = 0, 0

    def init_calculations(self):
        if not self.trade_in_going:
            self.stop_loss = Trade.stop_loss_calc(self)
            self.entry_price, self.enter_price_index = self.enter_price_calc()
            self.take_profit = Trade.take_profit_calc(self, self.entry_price, self.stop_loss)

            self.trade_in_going = True
            print("Trade in going !")

            self.current_balance = float(self.infos["totalMarginBalance"])
            self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

            self.quantity, self.leverage = Trade.quantity_calculator(self, self.balance_available)

    def enter_price_calc(self):
        prices = self.data['close'].tail(self.study_range).values
        enter_price_index = len(prices) - 2
        enter_price = prices[enter_price_index]

        return float(enter_price), int(enter_price_index)

    def take_profit_calc(self, enter_price, stop_loss):
        if self.long:
            take_profit = enter_price + (enter_price - stop_loss) * self.risk_ratio
        else:
            take_profit = enter_price - (stop_loss - enter_price) * self.risk_ratio

        return take_profit

    def stop_loss_calc(self):
        low_l = len(self.low_wicks) - 1
        high_l = len(self.high_wicks) - 1
        if self.low_wicks_indexes[low_l] == self.study_range - 1:
            low_l -= 1
        if self.high_wicks_indexes[high_l] == self.study_range - 1:
            high_l -= 1
        if self.long:
            buffer = float(self.low_wicks[low_l]) * self.buffer
            stop_loss = float(self.low_wicks[low_l]) - buffer
        else:
            buffer = float(self.high_wicks[high_l]) * self.buffer
            stop_loss = float(self.high_wicks[high_l]) + buffer

        return float(stop_loss)

    def add_to_log_master(self, win, time_pos_open, money, debug):
        if win:
            end_money = money * (1 + (self.risk_per_trade_brut / 100 * self.risk_ratio))
            win = 1
        else:
            end_money = money * self.risk_per_trade
            win = 0
        datas = [[win, time_pos_open, money, end_money]]
        debug.append_trade_history(datas)

    def quantity_calculator(self, money_available):
        money_traded = money_available / 1.5
        quantity = money_traded / self.entry_price
        quantity = quantity.__round__(3)

        if self.stop_loss < self.entry_price:  # Determine if short or long, which change the operation
            percentage_risked_trade = (1 - self.stop_loss / self.entry_price) * 100  # long
        else:
            percentage_risked_trade = (1 - self.entry_price / self.stop_loss) * 100  # short

        real_money_traded = quantity * self.entry_price
        diviseur = money_available / real_money_traded
        percentage_risked_trade = percentage_risked_trade / diviseur
        leverage = ((1 - self.risk_per_trade) * 100) / (percentage_risked_trade / 100 * real_money_traded)
        leverage = leverage.__round__()

        print("Maximum loss of current trade : " +
              str(float(leverage * percentage_risked_trade * 1.5).__round__()) + " %")

        leverage = Trade.adjust_leverage(leverage=leverage, risk_trade=percentage_risked_trade)

        print("The quantity is : " + str(quantity) + " BTC")
        print("The money traded is : " + str(real_money_traded))

        return quantity, leverage

    @staticmethod
    def adjust_leverage(leverage, risk_trade):
        r = leverage
        while leverage * risk_trade * 1.5 >= 100:  # Not tested
            print("High risk of liquidation ! Reducing leverage...")
            r = r - ((r * 0.1).__round__())

        if leverage >= 125:
            print("Leverage too high. The platform cannot handle it.")
            r = 120
        elif leverage >= 90:
            print("Very high leverage ! Think about putting more money in the trade !")
        elif leverage < 1:
            print("Leverage too low !")
            r = 1
        print("The leverage is : " + str(leverage))
        return r


class BinanceOrders(Trade):
    def __init__(self, client: Client, long, data, list_r, study_range, fake_b_indexes):
        super().__init__(long, data, list_r, study_range, fake_b_indexes, client)

        BinanceOrders.cancel_all_orders(self)

    def init_long_short(self):
        if self.long:
            side = "BUY"
            position_side = "LONG"
        else:
            side = "SELL"
            position_side = "SHORT"

        BinanceOrders.place_order(self,
                                  position_side=position_side,
                                  side=side
                                  )

        self.take_profit_recalculation()

    def take_profit_recalculation(self):
        self.entry_price = self.client.futures_position_information(symbol="BTCUSDT")
        self.entry_price = self.entry_price[1]

        self.take_profit_calc(self.entry_price, self.stop_loss)

    def place_sl_and_tp(self):
        BinanceOrders.take_profit_stop_loss(self, "STOP_MARKET", self.stop_loss)
        BinanceOrders.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", self.take_profit)

    def place_order(self, position_side, side):
        self.client.futures_change_leverage(symbol="BTCUSDT", leverage=str(self.leverage))
        time.sleep(5)
        self.client.futures_create_order(symbol="BTCUSDT",
                                         positionSide=position_side,
                                         quantity=self.quantity,
                                         side=side,
                                         type="MARKET",
                                         )
        time.sleep(1)

    def cancel_all_orders(self):
        self.client.futures_cancel_all_open_orders(symbol="BTCUSDT")
        # Doesnt close positions => Be careful.

    def take_profit_stop_loss(self, type_action, price_stop):
        side = "BUY"
        position_side = "SHORT"
        if self.long:
            side = "SELL"
            position_side = "LONG"
        self.client.futures_create_order(symbol="BTCUSDT",
                                         closePosition="true",
                                         type=str(type_action),
                                         stopPrice=str(price_stop),
                                         side=side,
                                         positionSide=position_side
                                         )
        time.sleep(0.5)
