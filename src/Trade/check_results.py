from src.Miscellaneous.warn_user import Warn
from src.Trade.ProceduresAndCalc.calc_orders import CalcOrders


class TradeResults:
    def __init__(self, coin, debug_obj):
        self.coin = coin
        self.debug = debug_obj

    def check_result(self, binance, log_master, symbol_index: int, last_money, current_money):

        log = self.debug.logs.add_log
        win, target_hit = self.check_target(binance.stop_loss, binance.take_profit)
        if target_hit:  # When an order is hit and the position is closed.
            binance.trade_in_going = False
            log("\n\n\nTarget hit ! Won ? | " + str(win))

            # for some reason the real target hit is last_closed_candle_index + 1; small bug here maybe.
            time_pos_hit = self.coin.data.loc[self.coin.last_closed_candle_index, 'open_date_time']
            warn = Warn()
            symbol_string = self.debug.get_current_trade_symbol(symbol_index=symbol_index)

            close_price = binance.take_profit if win else binance.stop_loss

            warn.send_result_email(
                long=self.coin.long,
                entry_price=binance.entry_price,
                close_price=close_price,
                time_pos_hit=time_pos_hit,
                time_pos_open=binance.entry_price_date,
                win=win,
                symbol_string=symbol_string,
                last_money=last_money,
                current_money=current_money
            )
            trade_type_string = warn.trade_type_string(self.coin.long)

            CalcOrders.add_to_trade_history(binance, symbol_string, trade_type_string, win, binance.entry_price_date,
                                            time_pos_hit, binance.current_balance, log_master)
            return True
        return False

    def check_target(self, stop_loss, take_profit):
        # See if the position is closed, and if it is lost or won.

        # Get the data
        low_wicks = self.coin.data['low'].tail(5)
        high_wicks = self.coin.data['high'].tail(5)

        target_hit = False
        win = False

        len_list = self.coin.last_closed_candle_index
        if self.coin.long:
            if low_wicks[len_list] <= stop_loss:  # Below SL
                target_hit = True
                win = False
            elif high_wicks[len_list] >= take_profit:  # Above TP
                target_hit = True
                win = True
        else:
            if high_wicks[len_list] >= stop_loss:  # Above SL
                target_hit = True
                win = False
            elif low_wicks[len_list] <= take_profit:  # Below TP
                target_hit = True
                win = True

        return win, target_hit

    def check_limit_order(self, target):
        low_wicks = self.coin.data['low'].tail(5)
        high_wicks = self.coin.data['high'].tail(5)
        target_hit = False

        if self.coin.long:
            if float(low_wicks[self.coin.last_closed_candle_index]) <= target:  # Below target
                target_hit = True
        else:
            if float(high_wicks[self.coin.last_closed_candle_index]) >= target:  # Above target
                target_hit = True

        return target_hit

    def update(self, coin, debug):
        self.coin = coin
        self.debug = debug
