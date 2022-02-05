from src.Miscellaneous.warn_user import Warn
from src.Miscellaneous.settings import Parameters


class CalcOrders:
    def __init__(self, coin, client, log, lowest_quantity):
        self.settings = Parameters()
        self.warn = Warn()

        self.lowest_quantity = lowest_quantity

        self.buffer = self.settings.buffer
        self.client = client

        self.coin = coin

        self.study_range = self.settings.study_range
        self.fees = self.settings.fees
        self.log = log

        self.trade_in_going = False

        self.infos = self.client.futures_account()

        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])

        self.stop_loss = 0
        self.entry_price, self.entry_price_index = 0, 0
        self.take_profit = 0

        self.quantity, self.leverage = 0, 0
        self.risk_ratio_adjusted = self.settings.risk_ratio

    def init_calculations(self, strategy="divergence"):
        if not self.trade_in_going:
            self.entry_price, self.entry_price_index = self.entry_price_calc()
            if strategy == "divergence":
                self.stop_loss = self.stop_loss_calc()
            elif strategy == "ema_fractals":
                self.stop_loss = self.stop_loss_calc_ema_fractals()
            self.take_profit = self.take_profit_calc(self.entry_price, self.stop_loss)

    def last_calculations(self):
        self.trade_in_going = True
        self.get_quantity_leverage()

    def get_quantity_leverage(self):
        self.current_balance = float(self.infos["totalMarginBalance"])
        self.balance_available = self.current_balance - float(self.infos["totalPositionInitialMargin"])
        self.quantity, self.leverage = self.lev_quant_calc(self.balance_available)

    def entry_price_calc(self):
        prices = self.coin.data['close'].tail(2).values
        enter_price_index = len(prices) - 2
        entry_price = prices[enter_price_index]

        return entry_price, enter_price_index

    def take_profit_calc(self, enter_price, stop_loss):
        if self.coin.long:
            take_profit = enter_price + (enter_price - stop_loss) * self.settings.risk_ratio
        else:
            take_profit = enter_price - (stop_loss - enter_price) * self.settings.risk_ratio
        take_profit.__round__()

        return int(take_profit)

    def calc_real_risk_ratio(self):  # Maybe do an abs function
        if self.coin.long:
            self.risk_ratio_adjusted = (self.take_profit - self.entry_price) / (self.entry_price - self.stop_loss)
        else:
            self.risk_ratio_adjusted = (self.entry_price - self.take_profit) / (self.stop_loss - self.entry_price)
        self.risk_ratio_adjusted = self.risk_ratio_adjusted.__round__(2)

    def stop_loss_calc(self):
        low_l = len(self.coin.low_wicks) - 1
        high_l = len(self.coin.high_wicks) - 1
        if self.coin.long:
            buffer = self.coin.low_wicks[low_l] * self.buffer
            stop_loss = self.coin.low_wicks[low_l] - buffer
        else:
            buffer = self.coin.high_wicks[high_l] * self.buffer
            stop_loss = self.coin.high_wicks[high_l] + buffer
        print("The stop loss is : " + str(stop_loss))
        stop_loss.__round__()

        self.check_sl(stop_loss)
        return int(stop_loss)

    def stop_loss_calc_ema_fractals(self):
        data, error = self.coin.data.loc, False
        i = self.settings.study_range - 2
        low = data[i, 'low']
        high = data[i, 'high']
        stop_loss = 0

        if self.coin.long:
            if low > data[i, 'ema100']:
                if data[i, 'ema20'] > low > data[i, 'ema50']:
                    stop_loss = data[i + 2, 'ema50']
                elif low < data[i, 'ema20'] and low < data[i, 'ema50']:
                    stop_loss = data[i + 2, 'ema100']
                else:
                    print("Error in stop loss calculation")
                    error = True
            else:
                print("Trade cancelled ! Wrong candle position related to 100 ema")
                error = True
        else:
            if high < data[i, 'ema100']:
                if data[i, 'ema20'] < high < data[i, 'ema50']:
                    stop_loss = data[i + 2, 'ema50']
                elif high > data[i, 'ema20'] and high > data[i, 'ema50']:
                    stop_loss = data[i + 2, 'ema100']
                else:
                    print("Error in stop loss calculation")
                    error = True
            else:
                print("Trade cancelled ! Wrong candle position related to 100 ema")
                error = True

        if not error:
            self.check_sl(stop_loss=stop_loss)
            if self.coin.long:
                stop_loss -= self.buffer * stop_loss
            else:
                stop_loss += self.buffer * stop_loss

        return int(stop_loss)

    def check_sl(self, stop_loss):
        if (stop_loss > self.entry_price and self.coin.long) or (stop_loss < self.entry_price and not self.coin.long):
            print(f"It was a long ? | {self.coin.long}")
            print(f"The entry price is : {self.entry_price}")
            try:
                print(f'Debug data lows : \n{self.coin.low_wicks}')
                print(f'Debug data highs : \n{self.coin.high_wicks}')
            except Exception as e:
                print("May not be the divergence strategy")
                print(e)
            print(f"The stop loss was : {stop_loss} and the entry_price : {self.entry_price}")
            import pandas
            with pandas.option_context('display.max_columns', None):  # more options can be specified also
                print(f"The last prices were : \n{self.coin.data}")
            raise print("Fatal error, could not calculate properly the stop loss; due to self.high/low_wicks "
                        "to not be correct.")

    def add_to_trade_history(self, symbol, trade_type, win, time_pos_open, time_pos_hit, money, debug):
        end_money = money
        if win:
            end_money = end_money - (end_money * self.fees * self.leverage)
            end_money = end_money * (1 + (1 - self.settings.risk_per_trade) * self.risk_ratio_adjusted)
            end_money = end_money - (end_money * self.fees * self.leverage)
            win = 1
        else:
            end_money = end_money - (end_money * self.fees * self.leverage)
            end_money = end_money * self.settings.risk_per_trade
            end_money = end_money - (end_money * self.fees * self.leverage)
            win = 0
        datas = [[symbol, trade_type, win, time_pos_open, time_pos_hit, money, end_money]]
        debug.append_trade_history(datas)

    def lev_quant_calc(self, money_available):
        money_divided = 1
        money_traded = money_available / money_divided

        percentage_risked_trade = self.percentage_risk_calculation()
        self.log(f"\n\nThe percentage risked on the trade is wo leverage : {percentage_risked_trade.__round__(2)}")

        lowest_entry_price_trade = self.lowest_quantity * self.entry_price
        leverage = self.leverage_calculation(percentage_risked_trade)

        if leverage < 1:
            leverage_diviseur = 1
        else:
            leverage_diviseur = leverage

        # If the lowest money I can put on the trade is superior to the money available, trade cancelled.
        if (lowest_entry_price_trade / leverage_diviseur) > self.balance_available:
            leverage = 0
            quantity = 0
        else:
            # If the minimum possible of what I can afford to lose is superior to the maximum of what I
            # can afford to lose, trade cancelled.
            if (lowest_entry_price_trade * (percentage_risked_trade / 100)) > \
                    (self.balance_available * (self.settings.risk_per_trade / 100)) and leverage <= 1:
                leverage = 0
                quantity = 0
            else:
                # Having a leverage of 1 in the end, while reducing money exposition.
                if self.settings.risk_per_trade < percentage_risked_trade:
                    while leverage < 1 and money_traded > self.settings.lowest_money_binance:
                        money_divided += 0.1
                        money_traded = money_available / money_divided
                        percentage_risked_trade_adjusted = percentage_risked_trade / money_divided
                        leverage = self.leverage_calculation(percentage_risked_trade_adjusted)
                else:
                    leverage = self.leverage_calculation(percentage_risked_trade)

                self.log(f"\nThe leverage before round is : {leverage} and after : {leverage.__round__()}")
                leverage = leverage.__round__()
                if money_traded > self.settings.lowest_money_binance and leverage >= 1:
                    quantity = (money_traded / self.entry_price) * leverage

                    count = 1
                    temp = self.lowest_quantity
                    div = 1
                    entered = False

                    # Determine where to round the quantity. entered is when lowest_quantity = 1
                    while temp % div != 0:
                        div = div / 10
                        count += 1
                        entered = True

                    last_quantity = quantity
                    if not entered:
                        quantity = quantity.__round__()
                    else:
                        quantity = quantity.__round__(count - 1)

                    # When it rounds, it can give quantity + lowest_quantity; this code is to avoid that and only get
                    # quantity rounded to the lower.
                    if quantity > self.lowest_quantity and last_quantity < quantity:
                        quantity = quantity - self.lowest_quantity
                    elif quantity <= self.lowest_quantity:
                        quantity = 0

                    quotient_div_money = self.balance_available / (quantity / leverage * self.entry_price)

                    self.log("\nThe leverage is : " + str(leverage))
                    self.log("\nMaximum loss of current trade : " +
                             str(float(leverage * percentage_risked_trade / quotient_div_money).__round__(2)) + " %")
                    self.log("\nThe quantity is : " + str(quantity))

                    quantity, leverage = self.last_leverage_quantity_check(leverage=leverage, quantity=quantity)
                else:
                    if money_traded < self.settings.lowest_money_binance:
                        self.log(f"\n\nWARNING MONEY ENTRY : TOO LOW ({money_traded.__round__(2)})")
                    else:
                        self.log(f"\n\nWARNING LEVERAGE : BELOW 1 ({leverage})")
                    quantity = 0
                    leverage = 0

        return quantity, leverage

    # Last check of possible incorrect leverage or quantity. Avoid incorrect input in binance APIs.
    def last_leverage_quantity_check(self, leverage, quantity):
        if leverage < 1:
            self.log("\n\n\nWARNING LEVERAGE : Leverage was set at 0 or below 1")
            leverage = 0
        if quantity == 0:
            leverage = 0
            self.log("\nWARNING QUANTITY : Quantity was set at 0")

        return quantity, leverage

    def leverage_calculation(self, percentage_risked):
        leverage = (1 / percentage_risked) * self.settings.risk_per_trade_brut
        self.correct_leverage(leverage=leverage, risk_trade=percentage_risked)
        return int(leverage)

    def percentage_risk_calculation(self):
        if self.stop_loss < self.entry_price:  # Determine if short or long, which change the operation
            percentage_risked_trade = (1 - self.stop_loss / self.entry_price) * 100  # long
        else:
            percentage_risked_trade = (1 - self.entry_price / self.stop_loss) * 100  # short
        return percentage_risked_trade

    def correct_leverage(self, leverage, risk_trade):
        while leverage * risk_trade * 1.5 >= 100:  # Not tested. Looks to work
            self.log("\nHigh risk of liquidation ! Reducing leverage...")
            leverage = leverage - (leverage * 0.1).__round__()
        if leverage >= 125:
            self.log("\nLeverage too high. The platform cannot handle it.")
            leverage = 120
        elif leverage < 1:
            self.log(f"\nSMALL WARNING : Leverage inferior to 1 ! | {leverage}")
        return leverage
