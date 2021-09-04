from WarnUser import Warn
from src.Trade.Trade import Trade
from src.Data.High_Low_Data import HighLowHistory


class TradeResults:
    def __init__(self, coin: HighLowHistory, debug_obj):
        self.coin = coin
        self.debug = debug_obj

    def check_result(self, binance, log_master, symbol):
        time_pos_open = self.debug.get_time(self.coin.study_range - 2)  # When is the trade open

        log = self.debug.logs.add_log
        win, target_hit = self.check_target(binance.stop_loss, binance.take_profit, time_pos_open)
        if target_hit:  # When an order is hit and the position is closed.
            binance.trade_in_going = False
            log("\n\n\nTarget hit ! Won ? | " + str(win))

            time_pos_hit = self.debug.get_time(self.coin.study_range - 2)
            warn = Warn()
            symbol_word = self.debug.get_current_trade_symbol(symbol_index=symbol)
            warn.send_result_email(
                long=self.coin.long,
                entry_price=binance.entry_price,
                time_pos_hit=time_pos_hit,
                time_pos_open=time_pos_open,
                win=win,
                symbol=symbol_word
            )

            Trade.add_to_trade_history(binance, win, time_pos_open, time_pos_hit, binance.current_balance,
                                       log_master)
            return True
        return False

    def check_target(self, stop_loss, take_profit, time_pos_open):
        # See if the position is closed, and if it is lost or won.

        # Get the data
        low_wicks = self.coin.data['low'].tail(5).values
        high_wicks = self.coin.data['high'].tail(5).values
        last_open_time = self.coin.data['open_date_time'].tail(2).values

        target_hit = False
        win = False

        len_low = len(low_wicks) - 2
        len_high = len(high_wicks) - 2

        if not last_open_time[0] == time_pos_open:  # Check if not in the first unclosed candle.
            if self.coin.long:
                if float(low_wicks[len_low]) <= stop_loss:  # Below SL
                    target_hit = True
                    win = False
                elif float(high_wicks[len_high]) >= take_profit:  # Above TP
                    target_hit = True
                    win = True
            else:
                if float(high_wicks[len_high]) > stop_loss:  # Above SL
                    target_hit = True
                    win = False
                elif float(low_wicks[len_low]) < take_profit:  # Below TP
                    target_hit = True
                    win = True

        return win, target_hit

    def update(self, coin, debug):
        self.coin = coin
        self.debug = debug
