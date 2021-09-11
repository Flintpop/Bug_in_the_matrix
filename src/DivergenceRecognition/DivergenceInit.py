import time
import traceback

from WarnUser import Warn
from print_and_debug import PrintUser, LogMaster
from src.Data.High_Low_Data import HighLowHistory
from src.DivergenceRecognition.Conditions import StrategyConditions
from src.Trade.CheckResults import TradeResults
from src.Trade.Trade import BinanceOrders
from src.Miscellanous.Settings import Parameters


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

        for symbol in range(self.n_coin):
            self.coins.append(HighLowHistory(self.client, settings.market_symbol_list[symbol]))
            current_coin = self.coins[symbol]
            self.debugs.append(PrintUser(current_coin))
            current_debug = self.debugs[symbol]
            self.conditions.append(StrategyConditions(current_coin, current_debug))

        self.log_master = LogMaster()

        self.trade_in_going = False
        self.divergence_spotted = False

        self.warn = Warn()

        self.warn.debug_file()

        self.wait = 285
        self.fast_wait = 5

        self.warn.logs.add_log("\n\nBot initialized !")

    def scan(self):
        while True:
            crossed = False
            # Spots divergence, then checks if it is not the same it was used.
            for symbol in range(self.n_coin):
                divergence = self.conditions[symbol].divergence_spotter()
                same_trade = self.conditions[symbol].check_not_same_trade()
                is_obsolete = self.conditions[symbol].is_obsolete()
                if divergence and not same_trade and not is_obsolete:
                    self.warn.logs.add_log(f"\nFor "
                                           f"{self.debugs[symbol].get_current_trade_symbol(symbol_index=symbol)}")
                    self.conditions[symbol].init_trade_final_checking()

                    while not crossed and divergence:
                        self.update(symbol, update_type="fast")
                        crossed, divergence = self.conditions[symbol].trade_final_checking()  # Check the final
                        # indicators compliance.
                    if crossed and divergence:
                        self.init_trade(symbol)
                    else:
                        self.warn.logs.add_log(f"\nTrade cancelled on {self.symbols[symbol]}!")

                if self.download_mode:
                    self.update(symbol, wait_exception=1800)  # Update indicators and data.

    def init_trade(self, symbol):
        self.warn.debug_file()
        log = self.warn.logs.add_log
        self.divergence_spotted = False
        log(self.coins[symbol].data)
        self.debugs[symbol].actualize_data(self.coins[symbol])
        string_symbol = self.debugs[symbol].get_current_trade_symbol(symbol_index=symbol)

        log("\n\n\nInitiating trade procedures...")

        # BinanceOrders has all the methods that is related to sl, tp, leverage, quantity calc in function of the risk
        # chosen per trade and other parameters. This class contains also all the methods related to actually open a
        # position and open orders.
        binance = BinanceOrders(
            coin=self.coins[symbol],
            client=self.client,
            log=self.warn.logs.add_log,
            symbol=string_symbol
        )
        log("\nCalculating stop_loss, take profit...")
        binance.init_calculations()
        log("\nTrade orders calculated.")

        log("\nInitiating binance procedures...")
        # binance.open_trade(symbol=string_symbol)
        # binance.place_sl_and_tp(symbol=string_symbol)
        log("\nOrders placed and position open !")
        # Just print all the trade informations and add it to the log file.
        PrintUser.debug_trade_parameters(
            self=self.debugs[symbol],
            long=self.coins[symbol].long,
            sl=binance.stop_loss,
            tp=binance.take_profit,
            entry_price=binance.entry_price,
            entry_price_index=self.coins[symbol].study_range - 2,
            symbol=string_symbol
        )

        trade_results = TradeResults(self.coins[symbol], self.debugs[symbol])
        time_pos_open = self.debugs[symbol].get_time(self.coins[symbol].study_range - 2)  # When is the trade open

        while binance.trade_in_going:
            res = trade_results.check_result(binance, self.log_master, symbol=symbol, time_pos_open=time_pos_open)

            if res:
                binance.trade_in_going = False
                time.sleep(self.settings.wait_after_trade_seconds)
            else:
                self.update(symbol)
                trade_results.update(self.coins[symbol], self.debugs[symbol])

    def update(self, symbol, update_type="", wait_exception=20):
        if update_type == "fast":
            time.sleep(self.fast_wait)
        else:
            time.sleep(self.wait)
        self.warn.debug_file()
        # Update to the latest price data and indicators related to it.
        try:
            self.coins[symbol] = self.coins[symbol].update_data()
            self.debugs[symbol] = self.debugs[symbol].actualize_data(self.coins[symbol])
            self.conditions[symbol] = self.conditions[symbol].actualize_data(coin=self.coins[symbol],
                                                                             debug_obj=self.debugs[symbol])
        except Exception as e:
            n = 0
            wait = wait_exception
            if wait_exception != 20:
                wait = wait_exception / 10

            error_msg_connection_reset = 'Connection reset by peer'
            if str(e) != error_msg_connection_reset:
                tb = traceback.format_exc()
                self.warn.logs.add_log("\n\n" + str(tb))
                raise SystemError
            while n < 10:  # This code to avoid WatchTower sending false positive mails.
                self.warn.debug_file()
                time.sleep(wait)
                n += 1
