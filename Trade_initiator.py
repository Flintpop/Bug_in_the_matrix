import time


def quantity_calculator(risk_per_trade, sl, enter_price, money_available):
    money_traded = money_available / 2
    quantity = money_traded / enter_price
    quantity = quantity.__round__(3)

    if sl < enter_price:
        percentage_risked_trade = (1 - sl / enter_price) * 100  # Ex : 0.5% for long
    else:
        percentage_risked_trade = (1 - enter_price / sl) * 100  # short

    real_money_traded = quantity * enter_price
    diviseur = money_available / real_money_traded
    percentage_risked_trade = percentage_risked_trade / diviseur
    leverage = ((1 - risk_per_trade) * 100) / (percentage_risked_trade / 100 * real_money_traded)
    leverage = leverage.__round__()

    print(leverage * percentage_risked_trade * 2)

    if leverage * percentage_risked_trade * 2 >= 100:
        print("High risk of liquidation !")
    if leverage >= 125:
        print("Leverage too high. The platform cannot handle it.")
        leverage = 120
    elif leverage >= 90:
        print("Very high leverage ! Think about putting more money in the trade !")
    elif leverage < 1:
        leverage = 1

    print("The quantity is : " + str(quantity) + " BTC")
    print("The leverage is : " + str(leverage))
    print("The money traded is : " + str(real_money_traded))

    return quantity, leverage


class Trade:
    def __init__(self, long, data, list_r, study_range, fake_b_indexes, index):

        self.risk_ratio = 0.675
        self.risk_per_trade = 21
        self.risk_per_trade = 1 - self.risk_per_trade / 100
        self.buffer = 0.001

        self.long = long
        self.data = data
        self.study_range = study_range

        self.high_wicks, self.high_wicks_indexes = list_r[2], list_r[3]
        self.low_wicks, self.low_wicks_indexes = list_r[8], list_r[9]
        self.fake_bull_indexes = fake_b_indexes[0]
        self.fake_bear_indexes = fake_b_indexes[1]

        self.trade_in_going = False

        prices = self.data['close'].tail(study_range).values

        if not self.trade_in_going:
            self.stop_loss = Trade.stop_loss_calc(self)
            self.enter_price, self.enter_price_index = Trade.enter_price_calc(prices)
            self.take_profit = Trade.take_profit_calc(self, self.enter_price, self.stop_loss)

            self.trade_in_going = True
            print("Trade in going !")

    @staticmethod
    def enter_price_calc(prices):
        enter_price_index = len(prices) - 2  # Not good, should buy first then use the margin enter price to calculate
        # the sl and tp.
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


class BinanceOrders:
    def __init__(self, sl, enter_price, tp, risk_per_trade, client, long):
        self.client = client
        self.long = long

        BinanceOrders.cancel_all_orders(self)

        self.infos = self.client.futures_account()

        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

        self.quantity, self.leverage = quantity_calculator(risk_per_trade, sl, enter_price, self.balance_available)

        BinanceOrders.init_long_short(self, sl, tp)

    def init_long_short(self, sl, tp):
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
        BinanceOrders.take_profit_stop_loss(self, "STOP_MARKET", sl)
        BinanceOrders.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", tp)

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
