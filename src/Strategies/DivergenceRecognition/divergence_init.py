import time

from src.Miscellaneous.warn_user import Warn
from src.Miscellaneous.print_and_debug import PrintUser, LogMaster
from src.Data.high_low_data import HighLowHistory
from src.Strategies.DivergenceRecognition.conditions import MacdDivergenceConditions
from src.Trade.check_results import TradeResults
from src.Trade.ProceduresAndCalc.buy_binance import BinanceOrders
from src.Miscellaneous.settings import Parameters


class Divergence:
    def __init__(self, client, settings: Parameters):
        self.client = client
        self.settings = settings

        self.download_mode = settings.download_mode

        self.debug_mode = settings.debug_mode
        self.coins = []
        self.debugs = []
        self.conditions = []

        self.n_coin = len(settings.market_symbol_list)
        self.symbols = settings.market_symbol_list
        self.lowest_quantities = settings.lowest_quantity
        self.macd_line_mode = settings.macd_line_mode

        for symbol in range(self.n_coin):
            self.coins.append(HighLowHistory(self.client, settings.market_symbol_list[symbol], symbol))
            current_coin = self.coins[symbol]
            self.debugs.append(PrintUser(current_coin))
            current_debug = self.debugs[symbol]
            self.conditions.append(MacdDivergenceConditions(current_coin, current_debug, symbol))

        self.log_master = LogMaster()

        self.trade_in_going = False
        self.divergence_spotted = False

        self.warn = Warn()

        self.warn.debug_file()

        # Wait in seconds
        self.wait = 285
        self.fast_wait = 5

        self.current_trade_spec = {
            "delta_price": float,
            "delta_macd": float,
            "delta_ema": float,
            "raw_percentage_risked": float,
            "leverage": int
        }

        self.warn.logs.add_log("\n\nBot initialized !")

    def scan(self):
        stopped = False
        while not stopped:
            crossed = False
            # Spots divergence, then checks if it is not the same it was used.
            for symbol in range(self.n_coin):
                try:
                    divergence = self.conditions[symbol].divergence_spotter()
                    same_trade = self.conditions[symbol].check_not_same_trade()
                    is_obsolete = self.conditions[symbol].is_obsolete()

                    # WARNING MIGHT CREATE BUGS RELATED TO DETECTION | nothing so far I guess ?
                    if self.macd_line_mode:
                        good_macd_pos = self.conditions[symbol].macd_line_checker()
                    else:
                        good_macd_pos = True

                    if divergence and not same_trade and not is_obsolete and good_macd_pos and not \
                            self.conditions[symbol].coin.long and not self.coins[symbol].long:
                        self.warn.logs.add_log(f"\n\nFor "
                                               f"{self.debugs[symbol].get_current_trade_symbol(symbol_index=symbol)}")
                        self.conditions[symbol].init_trade_final_checking()

                        # Check the final indicators' compliance.
                        while not crossed and divergence and good_macd_pos:
                            self.update(symbol, update_type="fast")
                            crossed, divergence = self.conditions[symbol].trade_final_checking()
                            if self.macd_line_mode:
                                good_macd_pos = self.conditions[symbol].macd_line_checker()
                            else:
                                good_macd_pos = True
                        threshold = self.conditions[symbol].threshold_check()
                        if crossed and divergence and good_macd_pos and threshold:
                            self.init_trade(symbol)
                        else:
                            self.debugs[symbol].print_trade_aborted(crossed, divergence, good_macd_pos, symbol,
                                                                    threshold)

                    if self.download_mode:
                        self.update(symbol, wait_exception=1800)  # Update indicators and data.
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
                    send_email(word=word_mail, subject=f"Scan error in the market "
                                                       f"{self.debugs[symbol].get_current_trade_symbol(symbol)}")

    def init_trade(self, index_symbol):
        self.warn.debug_file()
        log = self.warn.logs.add_log
        self.divergence_spotted = False
        log(f"\n{self.coins[index_symbol].data}")
        self.debugs[index_symbol].actualize_data(self.coins[index_symbol])
        string_symbol = self.debugs[index_symbol].get_current_trade_symbol(symbol_index=index_symbol)

        log("\n\n\nInitiating first trade procedures...")

        # BinanceOrders has all the methods that is related to sl, tp, leverage, quantity calc in function of the risk
        # chosen per trade and other parameters. This class contains also all the methods related to actually open a
        # position and open orders.
        binance = BinanceOrders(
            coin=self.coins[index_symbol],
            client=self.client,
            log=self.warn.logs.add_log,
            lowest_quantity=self.lowest_quantities[index_symbol],
            print_infos=True
        )

        binance.cancel_all_orders(symbols_string=self.settings.market_symbol_list)

        log("\nCalculating stop_loss, take profit...")
        binance.init_calculations()
        log("\nTrade orders calculated.")

        if binance.leverage > 0 and self.settings.maximum_leverage[index_symbol] > binance.quantity > 0:
            log("\n\nTrade in going !")
            self.debugs[index_symbol].debug_trade_parameters(
                trade=self.coins[index_symbol],
                symbol_string=string_symbol,
                long=self.coins[index_symbol].long
            )

            log("\nInitiating binance procedures...")

            try:
                binance.open_trade_market(symbol_string=string_symbol)
                binance.place_sl_and_tp(symbol_string=string_symbol)
                log("\nOrders placed and position open !")
                infos = self.client.futures_account()

                last_money = float(infos["totalMarginBalance"])
                trade_results = TradeResults(self.coins[index_symbol], self.debugs[index_symbol])

                while binance.trade_in_going:
                    infos = self.client.futures_account()
                    current_money = float(infos["totalMarginBalance"])
                    target_hit = trade_results.check_result(binance, self.log_master, symbol_index=index_symbol,
                                                            current_money=current_money, last_money=last_money)
                    if target_hit:
                        binance.trade_in_going = False
                        time.sleep(self.settings.wait_after_trade_seconds)
                    else:
                        self.update(index_symbol)
                        trade_results.update(self.coins[index_symbol], self.debugs[index_symbol])
            except Exception as e:
                log("\n\nWARNING : Binance procedures failed !\n\n")
                log(e)
                log(f"\n\n\ntraceback.format_exc")
                binance.cancel_all_orders(symbols_string=self.settings.market_symbol_list)
                binance.close_pos(symbol_string=string_symbol)
        else:
            log("\nTrade aborted because of leverage of quantity set to 0 !")

        self.update_all("fast")

    def update_all(self, update_type=""):
        for index_symbol in range(len(self.symbols) - 1):
            self.update(index_symbol, update_type)

    def update(self, index_symbol, update_type="", wait_exception=20):
        if update_type == "fast":
            time.sleep(self.fast_wait)
        else:
            time.sleep(self.wait)
        self.warn.debug_file()
        # Update to the latest price data and indicators related to it.
        try:
            self.coins[index_symbol].update_data()
            self.debugs[index_symbol].actualize_data(self.coins[index_symbol])
            self.conditions[index_symbol].actualize_data(coin=self.coins[index_symbol],
                                                         debug_obj=self.debugs[index_symbol])
        except Exception as e:
            self.warn.logs.add_log(f'\n\nWARNING UPDATE FUNCTION: \n{e}\n')
            self.warn.logs.add_log(f"Debug data : \n{self.coins[index_symbol]}\n"
                                   f"{self.debugs[index_symbol]}\n{self.conditions[index_symbol]}\n\n")

            # Avoid WatchTower sending false positive mails.
            n = 0
            wait = wait_exception
            if wait_exception != 20:
                wait = wait_exception / 10

            while n < 10:
                self.warn.debug_file()
                time.sleep(wait)
                n += 1
