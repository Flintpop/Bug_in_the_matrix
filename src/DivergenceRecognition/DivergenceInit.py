import time
import traceback

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
        self.coin = HighLowHistory(self.client)
        self.debug = PrintUser(self.coin)
        self.conditions = StrategyConditions(self.coin, self.debug)

        self.log_master = LogMaster()

        self.trade_in_going = False
        self.divergence_spotted = False

        self.debug.debug_file()

        self.wait = 285
        self.fast_wait = 5

        self.debug.logs.add_log("Bot initialized !")

    def scan(self):
        crossed = False
        while True:
            # Spots divergence, then checks if it is not the same it was used.
            divergence = self.conditions.divergence_spotter()
            same_trade = self.conditions.check_not_same_trade()
            is_obsolete = self.conditions.is_obsolete()
            if divergence and not same_trade and not is_obsolete:
                self.conditions.init_trade_final_checking()
                while not crossed and divergence:
                    crossed, divergence = self.conditions.trade_final_checking()  # Check the final indicators
                    # compliance.
                    self.update("fast")
                if crossed and divergence:
                    self.init_trade()
                else:
                    self.debug.logs.add_log("\nTrade cancelled !")

            if self.download_mode:
                self.update(wait_exception=1800)  # Update the whole indicators and data to the latest.

    def init_trade(self):
        self.debug.debug_file()
        log = self.debug.logs.add_log
        self.divergence_spotted = False
        log(self.coin.data)
        self.debug.actualize_data(self.coin)

        log("\n\n\nInitiating trade procedures...")

        # BinanceOrders has all the methods that is related to sl, tp, leverage, quantity calc in function of the risk
        # chosen per trade and other parameters. This class contains also all the methods related to actually open a
        # position and open orders.
        binance = BinanceOrders(
            coin=self.coin,
            client=self.client,
            log=self.debug.logs.add_log
        )
        log("\nCalculating stop_loss, take profit...")
        binance.init_calculations()
        log("\nTrade orders calculated.")

        log("\nInitiating binance procedures...")
        binance.init_long_short()
        binance.place_sl_and_tp()
        log("\nOrders placed and position open !")
        # Just print all the trade informations and add it to the log file.
        PrintUser.debug_trade_parameters(
            self=self.debug,
            long=self.coin.long,
            sl=binance.stop_loss,
            tp=binance.take_profit,
            entry_price=binance.entry_price,
            entry_price_index=self.coin.study_range - 2
        )

        trade_results = TradeResults(self.coin, self.debug)

        while binance.trade_in_going:
            res = trade_results.check_result(binance, self.log_master)

            if res:
                binance.trade_in_going = False
                time.sleep(self.settings.wait_after_trade_seconds)
            else:
                self.update()
                trade_results.update(self.coin, self.debug)

    def update(self, update_type="", wait_exception=20):
        if update_type == "fast":
            time.sleep(self.fast_wait)
        else:
            time.sleep(self.wait)
        self.debug.debug_file()
        # Update to the latest price data and indicators related to it.
        try:
            self.coin.update_data()
            self.debug.actualize_data(self.coin)
            self.conditions.actualize_data(coin=self.coin, debug_obj=self.debug)
        except Exception as e:
            n = 0
            wait = wait_exception
            if wait_exception != 20:
                wait = wait_exception / 10

            error_msg_connection_reset = 'Connection reset by peer'
            if str(e) != error_msg_connection_reset:
                tb = traceback.format_exc()
                self.debug.logs.add_log("\n\n" + str(tb))
            self.debug.logs.add_log("\n\nThe error message is : \n" + str(e))
            while n < 10:  # This code to avoid WatchTower sending false positive mails.
                self.debug.debug_file()
                time.sleep(wait)
                n += 1
