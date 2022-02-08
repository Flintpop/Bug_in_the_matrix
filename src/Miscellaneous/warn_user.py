import datetime

from src.watch_tower import send_email
from src.Miscellaneous.print_and_debug import os_path_fix, LogMaster


class Warn:
    def __init__(self):
        self.logs = LogMaster()

    @staticmethod
    def send_result_email(symbol_string: str, long: bool, win: bool, entry_price, close_price, time_pos_hit,
                          time_pos_open, last_money, current_money):
        won = Warn.win_loss_string(win)
        word = Warn.trade_type_string(long)
        gain_percentage = (float(current_money) / float(last_money) - 1) * 100
        gain_or_loss = "gain" if win else "loss"

        send_string = f"<h3>Trade completed on {symbol_string} !</h3>" \
                      f"<h4>The trade was a {word}, and it is {won}.</h4>"  \
                      f"<p>The entry price is <b>{entry_price}</b> at : {time_pos_open}.</p>"\
                      f"<p>The close price is <b>{close_price}</b> at : {time_pos_hit}.</p>"\
                      f"<p>There is now <b>{current_money}$</b> in your account instead of <b>{last_money}$</b>.</p>"\
                      f"<p>The trade resulted in a <b>{gain_percentage} %</b> {gain_or_loss}."

        send_email(word=send_string, subject=f"Trade {won} !")

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

    @staticmethod
    def write_on_file(word):
        debug_file_path = os_path_fix() + "debug_file.txt"
        f = open(debug_file_path, "w+")
        f.write(word)
        f.close()


if __name__ == '__main__':
    warn = Warn()
    warn.send_result_email("BTCUSDT", True, True, 3050, 3200, '2021-13-10:20:20', '2021-13-10-15:45:50',
                           last_money=20, current_money=35)
