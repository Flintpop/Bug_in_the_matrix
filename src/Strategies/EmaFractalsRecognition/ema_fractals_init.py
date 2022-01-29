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

        self.wait = 3500
        self.fast_wait = 1700

    def scan(self):
        stopped = False
        while not stopped:
            try:
                self.update()
                self.check_emas()
                self.william_signal = False
                if self.ema_right_pos and self.long:
                    self.check_price_not_touching()
                    if self.price_far_from_ema:
                        while self.price_far_from_ema:
                            self.check_price_not_touching()
                            self.update()
                        self.check_emas()
                        while not self.william_signal and not self.price_far_from_ema and self.ema_right_pos:
                            self.check_price_not_touching()

                            william_long, william_short = self.check_william_signal()
                            if (self.long and william_long) or (not self.long and william_short):
                                self.indicators.long = self.long
                                self.william_signal = True
                            else:
                                self.update()
                        self.check_emas()
                        if self.last_tests() and self.ema_right_pos and self.long:
                            self.init_trade()
            except Exception as e:
                stopped = True

                from src.watch_tower import send_email
                import traceback

                self.warn.logs.add_log(f"\n\n\nCRITICAL ERROR : Bot stopped !"
                                       f"\n\n{e}"
                                       f"\n\nThe traceback is : "
                                       f"\n\n\n{traceback.format_exc()}")
                word_mail = f"<h3>Bot stopped !</h3>" \
                            f"<p>Here is the current small error msg : </p><p><b>{e}</b></p>" \
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
            condition_two = self.data.loc[index, 'close'] > \
                            self.data.loc[index, 'ema100']
            rsi_good_pos = self.settings.long_rsi_max > self.data.loc[index - 2, 'rsi'] > self.settings.long_rsi_min
        else:
            condition_one = self.data.loc[index - 2, 'close'] < \
                            self.data.loc[index - 2, 'ema100']
            condition_two = self.data.loc[index, 'close'] < \
                            self.data.loc[index, 'ema100']
            rsi_good_pos = self.settings.short_rsi_min < self.data.loc[index - 2, 'rsi']

        return condition_one and condition_two and rsi_good_pos

    def init_trade(self):
        self.warn.debug_file()
        log = self.warn.logs.add_log
        binance = BinanceOrders(
            coin=self,
            client=self.client,
            log=self.log_master,
            lowest_quantity=self.settings.lowest_quantity[0]
        )
        self.debug.actualize_data(self)

        binance.init_calculations(strategy="ema_fractals")

        if binance.leverage > 0 and binance.quantity > 0.0:
            self.debug.debug_trade_parameters(
                trade=binance,
                symbol="BTCUSDT"
            )
            try:
                binance.open_trade(symbol="BTCUSDT")
                binance.place_sl_and_tp(symbol="BTCUSDT")
                log("\nOrders placed and position open !")
                infos = self.client.futures_account()

                last_money = float(infos["totalMarginBalance"]) - float(infos["totalPositionInitialMargin"])
                trade_results = TradeResults(self, self.debug)
                date_pos_open = self.debug.get_time(self.study_range - 2)

                while binance.trade_in_going:
                    infos = self.client.futures_account()
                    current_money = float(infos["totalMarginBalance"])
                    target_hit = trade_results.check_result(binance, self.log_master, symbol="BTCUSDT",
                                                            time_pos_open=date_pos_open, current_money=current_money,
                                                            last_money=last_money)
                    if target_hit:
                        binance.trade_in_going = False
                    else:
                        self.update()
                        trade_results.update(self, self.debug)
            except Exception as e:
                log("\n\nWARNING : Binance procedures failed !\n\n")
                log(e)
                log(f"\n\n\ntraceback.format_exc")
                binance.cancel_all_orders(symbols_string=self.settings.market_symbol_list)
                binance.close_pos(symbol_string="BTCUSDT")
        else:
            log("\nTrade aborted because of leverage of quantity set to 0 !")

    def check_emas(self):
        i = self.data
        index = self.last_closed_candle_index

        self.ema_right_pos = (i.loc[index, 'ema20'] > i.loc[index, 'ema50'] >
                              i.loc[index, 'ema100'] or (i.loc[index, 'ema20']) <
                              i.loc[index, 'ema50'] < i.loc[index, 'ema100'])
        self.long = i.loc[index, 'ema20'] > i.loc[index, 'ema50']

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
        bool_down_buy_fractal = bool_down_buy_fractal and low[middle_index - 2] > low[middle_index] < \
                                low[middle_index + 2]

        bool_up_sell_fractal = high[middle_index - 1] < high[middle_index] > high[middle_index + 1]
        bool_up_sell_fractal = bool_up_sell_fractal and high[middle_index - 2] < high[middle_index] > \
                               high[middle_index + 2]

        return bool_down_buy_fractal, bool_up_sell_fractal

    def update(self, update_type=""):
        if update_type == "fast":
            time.sleep(self.fast_wait)
        else:
            time.sleep(self.wait)
        self.warn.debug_file()
        updated = False

        while not updated:
            try:
                self.indicators.download_data()
                self.indicators.actualize_data_ema_fractals()
                self.data = self.indicators.data
                updated = True
            except Exception as e:
                self.warn.logs.add_log(f'\n\nWARNING UPDATE FUNCTION: \n{e}\n')
                time.sleep(100)
