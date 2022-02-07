import time

from src.Miscellaneous.settings import Parameters
from src.Data.indicators import Indicators
from src.Miscellaneous.print_and_debug import PrintUser, LogMaster
from src.Trade.ProceduresAndCalc.buy_binance import BinanceOrders
from src.Trade.check_results import TradeResults
from src.Miscellaneous.warn_user import Warn


# OLD to do : - Clean all errors ✔️
#  - Make the necessary objects compatible with this strategy (check target function for exemple) ✔️
#  - Check for the last candle to be ignored ✔️
#  - Deal with error management and implement send mail functions ✔️
#  - Call properly the binance function ✔️
#  - Change the main code to make it call this strategy properly. ✔️
#  - Check the reliability of the update function and the indicators. ✔️
#  - Implement trade records via log history object. ✔️


class EmaFractalsInit:
    def __init__(self, client, settings: Parameters):
        self.settings = settings
        self.client = client
        self.draw_plots = False

        self.ema_right_pos = False
        self.last_closed_candle_index = self.settings.study_range - 1
        self.long = None
        self.price_far_from_ema = False
        self.william_signal = False

        self.study_range = self.settings.study_range
        self.data_range = self.settings.data_range

        self.log_master = LogMaster()

        self.indicators = Indicators(client=client, symbol=self.settings.market_symbol_list[0], symbol_index=0)

        self.indicators.rsi()
        self.data = self.indicators.data

        self.debug = PrintUser(self.indicators)

        self.warn = Warn()

        self.wait = settings.waiting_time
        self.fast_wait = settings.fast_wait_time

    def scan(self):
        log = self.warn.logs.add_log
        stopped = False
        while not stopped:
            try:
                self.check_emas()
                self.william_signal = False
                if self.ema_right_pos and self.long:
                    self.check_price_not_touching()
                    if self.price_far_from_ema:
                        while self.price_far_from_ema:
                            self.check_price_not_touching()
                            if self.price_far_from_ema:
                                self.update()
                        self.check_emas()
                        while not self.william_signal and not self.price_far_from_ema and self.ema_right_pos:
                            self.check_price_not_touching()
                            william_long, william_short = self.check_william_signal()
                            if (self.long and william_long) or (not self.long and william_short):
                                log("\n\nWilliam signal on and price pulled back on ema !")
                                self.indicators.long = self.long
                                self.william_signal = True
                            else:
                                self.update("fast")
                        self.check_emas()

                        if self.last_tests() and self.ema_right_pos and self.long:
                            self.init_trade()
                self.update()
            except Exception as error:
                stopped = True

                from src.watch_tower import send_email
                import traceback

                self.warn.logs.add_log(f"\n\n\nCRITICAL ERROR : Bot stopped !"
                                       f"\n\n{error}"
                                       f"\n\nThe traceback is : "
                                       f"\n\n\n{traceback.format_exc()}")
                word_mail = f"<h3>Bot stopped !</h3>" \
                            f"<p>Here is the current small error msg : </p><p><b>{error}</b></p>" \
                            f"<p>Here is the traceback : </p>" \
                            f"<p>{traceback.format_exc()}</p>"
                send_email(word=word_mail, subject=f"Scan error in the market BTCUSDT")

    # Check if last close candle does not make a negative raw risk percentage trade along with avoiding trade where
    # the candle of william signal has the emas in the wrong position.
    def last_tests(self):
        index = self.last_closed_candle_index
        if self.long:
            condition_one = self.data.loc[index - 2, 'close'] > \
                            self.data.loc[index - 2, 'ema100']
            condition_two = self.data.loc[index, 'close'] > self.data.loc[index, 'ema100']
        else:
            condition_one = self.data.loc[index - 2, 'close'] < \
                            self.data.loc[index - 2, 'ema100']
            condition_two = self.data.loc[index, 'close'] < self.data.loc[index, 'ema100']

        return condition_one and condition_two

    def init_trade(self):
        self.warn.debug_file()
        log = self.warn.logs.add_log
        log("\n\nInitiating trade procedures...")
        binance = BinanceOrders(
            coin=self,
            client=self.client,
            log=log,
            lowest_quantity=self.settings.lowest_quantity[0],
            print_infos=False
        )

        binance.init_calculations(strategy="ema_fractals")
        binance.last_calculations()
        last_take_profit = binance.take_profit
        log("\n\nTrade parameters calculated. Checking for the very last verification procedures...")

        if binance.leverage > 0 and binance.quantity > 0.0:
            try:
                trade_results = TradeResults(self, self.debug)
                binance.print_infos = True
                if self.settings.limit_order_mode:
                    if self.get_lower_price(binance, trade_results):
                        binance.init_calculations(strategy="ema_fractals")
                        binance.take_profit = last_take_profit
                        binance.last_calculations()

                        # binance.place_sl_and_tp(symbol="BTCUSDT")
                        self.launch_procedures(binance, log, trade_results)
                    else:
                        log(f"\nTrade cancelled, order price not filled")
                        binance.cancel_all_orders_symbol(symbol_string="BTCUSDT")
                else:
                    binance.last_calculations()
                    # binance.open_trade(symbol="BTCUSDT") not going to enable it because of open trade limit
                    # binance.place_sl_and_tp(symbol="BTCUSDT")
                    self.launch_procedures(binance, log, trade_results)
            except Exception as e:
                from src.watch_tower import send_email
                import traceback
                log("\n\nWARNING CRITICAL : Binance procedures failed ! Closing all position...\n\n")
                log(e)
                log(f"\n\n\ntraceback.format_exc")
                binance.cancel_all_orders(symbols_string=self.settings.market_symbol_list)
                binance.close_pos(symbol_string="BTCUSDT")
                log("\n\n\nPositions closed.")
                word_mail = f"<h3>Trade cancelled !</h3>" \
                            f"<p>Here is the current small error msg : </p><p><b>{e}</b></p>" \
                            f"<p>Here is the traceback : </p>" \
                            f"<p>{traceback.format_exc()}</p>"
                send_email(word=word_mail, subject=f"Trade error in the market BTCUSDT")
        else:
            log(f"\nTrade aborted because of {binance.leverage}")

    def launch_procedures(self, binance: BinanceOrders, log, trade_results: TradeResults):
        log("\nOrders placed and position open !")
        self.debug.debug_trade_parameters(
            trade=binance,
            long=self.long,
            symbol_string="BTCUSDT"
        )
        infos = self.client.futures_account()

        last_money = float(infos["totalMarginBalance"]).__round__(2)

        while binance.trade_in_going:
            infos = self.client.futures_account()
            current_money = float(infos["totalMarginBalance"]).__round__(2)
            target_hit = trade_results.check_result(binance,
                                                    self.log_master,
                                                    symbol_index=0,
                                                    current_money=current_money,
                                                    last_money=last_money
                                                    )
            if target_hit:
                binance.trade_in_going = False
            else:
                self.update()
                trade_results.update(self, self.debug)

    def get_lower_price(self, trade: BinanceOrders, trade_results: TradeResults):
        order_filled = False
        if self.long:
            order_entry_price = trade.entry_price - \
                                (trade.entry_price - trade.stop_loss) * (self.settings.price_entry_coefficient / 100)
        else:
            order_entry_price = trade.entry_price + \
                                (trade.stop_loss - trade.entry_price) * (self.settings.price_entry_coefficient / 100)

        if order_entry_price > 10000:
            order_entry_price = order_entry_price.__round__()
        elif order_entry_price > 1000:
            order_entry_price = order_entry_price.__round__(2)
        elif order_entry_price > 100:
            order_entry_price = order_entry_price.__round__(3)

        self.debug.logs.add_log(f"\n\nThe entry price is {trade.entry_price} $ at {trade.entry_price_date} and the "
                                f"potential reduced one is {order_entry_price} $")
        self.debug.logs.add_log(f"\nData information debug first entry price : \n{self.data.tail(8)}")

        # trade.open_trade_limit(symbol="BTCUSDT", entry_price=order_entry_price)

        i = 0
        while i < self.settings.limit_wait_price_order and not order_filled:
            if not order_filled:
                self.update()
                trade_results.update(self, self.debug)
            order_filled = trade_results.check_limit_order(order_entry_price)
            i += 1
        if order_filled:
            trade.entry_price = order_entry_price
            self.debug.logs.add_log(f"\nData information debug after order filled : \n{self.data.tail(8)}")
            trade.entry_price_date = self.data.loc[self.last_closed_candle_index, 'open_date_time']

        return order_filled

    def check_emas(self):
        i = self.data
        index = self.last_closed_candle_index

        self.ema_right_pos = (i.loc[index, 'ema20'] > i.loc[index, 'ema50'] >
                              i.loc[index, 'ema100'] or (i.loc[index, 'ema20']) <
                              i.loc[index, 'ema50'] < i.loc[index, 'ema100'])
        self.long = i.loc[index, 'ema20'] > i.loc[index, 'ema50']
        self.indicators.long = self.long

    def check_price_not_touching(self):
        i = self.indicators.data
        self.price_far_from_ema = True
        if self.long:
            for j in range(0, self.settings.candle_ema_range):
                if i.loc[self.last_closed_candle_index - j, 'low'] < i.loc[self.last_closed_candle_index - j, 'ema20']:
                    self.price_far_from_ema = False
        else:
            for j in range(1, self.settings.candle_ema_range + 1):
                if i.loc[self.last_closed_candle_index - j, 'high'] > i.loc[self.last_closed_candle_index - j, 'ema20']:
                    self.price_far_from_ema = False

    def check_william_signal(self):
        middle_index = self.last_closed_candle_index - 2

        high = self.data.loc[:, 'high']
        low = self.data.loc[:, 'low']

        bool_down_buy_fractal = low[middle_index - 1] > low[middle_index] < low[middle_index + 1]
        bool_down_buy_fractal = bool_down_buy_fractal and low[middle_index - 2] > low[middle_index] < low[middle_index
                                                                                                          + 2]

        bool_up_sell_fractal = high[middle_index - 1] < high[middle_index] > high[middle_index + 1]
        bool_up_sell_fractal = bool_up_sell_fractal and high[middle_index - 2] < high[middle_index] > high[middle_index
                                                                                                           + 2]

        return bool_down_buy_fractal, bool_up_sell_fractal

    def update(self, update_type=""):
        self.warn.debug_file()
        if update_type == "fast":
            time.sleep(self.fast_wait)
        else:
            time.sleep(self.wait)
        updated = False

        while not updated:
            try:
                self.indicators.data = self.indicators.download_data()
                self.indicators.actualize_data_ema_fractals()
                self.data = self.indicators.data
                self.debug.actualize_data(self)
                updated = True
            except Exception as e:
                self.warn.debug_file()
                self.warn.logs.add_log(f'\n\nWARNING UPDATE FUNCTION: \n{e}\n')
                time.sleep(self.fast_wait / 2)
