import datetime

from src.WatchTower import send_email
from src.Miscellanous.print_and_debug import os_path_fix, LogMaster


class Warn:
    def __init__(self):
        self.logs = LogMaster()

    @staticmethod
    def send_result_email(symbol, long, win, entry_price, time_pos_hit, time_pos_open):
        won = Warn.win_loss_string(win)
        word = Warn.trade_type_string(long)

        send_email(f"<p>Trade completed on {symbol}!</p>"
                   f"<p>The trade was a {str(word)}, and it is {str(won)}</p>"
                   f"<p>The entry price is {str(entry_price)} at : {str(time_pos_open)}</p>"
                   f"<p>The trade was closed at {str(time_pos_hit)} </p>",
                   "Trade results"
                   )

    @staticmethod
    def trade_type_string(long):
        if long:
            res = "long"
        else:
            res = "short"
        return res

    @staticmethod
    def win_loss_string(win):
        if win:
            res = "won"
        else:
            res = "lost"
        return res

    @staticmethod
    def debug_file():
        debug_file_path = os_path_fix() + "debug_file.txt"
        f = open(debug_file_path, "w+")
        f.write("File created at : " + str(datetime.datetime.now()))
        f.close()
