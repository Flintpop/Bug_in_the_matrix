from src.Trade.ProceduresAndCalc.calc_orders import CalcOrders
import time


class BinanceOrders(CalcOrders):
    def __init__(self, coin, client, log, lowest_quantity):
        super().__init__(coin, client, log, lowest_quantity)

    def open_trade(self, symbol):
        if self.coin.long:
            side = "BUY"
            position_side = "LONG"
        else:
            side = "SELL"
            position_side = "SHORT"

        BinanceOrders.place_order(self,
                                  position_side=position_side,
                                  side=side,
                                  symbol=symbol
                                  )

    def close_pos(self, symbol_string):
        if self.coin.long:
            side = "SELL"
            position_side = "LONG"
        else:
            side = "BUY"
            position_side = "SHORT"
        try:
            self.client.futures_create_order(symbol=symbol_string,
                                             type="MARKET",
                                             quantity=self.quantity,
                                             side=side,
                                             positionSide=position_side
                                             )
        except Exception as e:
            self.log(e)
            self.log("\n\nWARNING : Failed to cancel trade. Must not exist.\n")

    def place_sl_and_tp(self, symbol):
        BinanceOrders.take_profit_stop_loss(self, "STOP_MARKET", self.stop_loss, symbol)
        BinanceOrders.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", self.take_profit, symbol)

    def take_profit_stop_loss(self, type_action, price_stop, symbol):
        side = "BUY"
        position_side = "SHORT"
        if self.coin.long:
            side = "SELL"
            position_side = "LONG"
        self.client.futures_create_order(symbol=symbol,
                                         closePosition="true",
                                         type=str(type_action),
                                         stopPrice=str(price_stop),
                                         side=side,
                                         positionSide=position_side
                                         )

    def place_order(self, position_side, side, symbol):
        self.client.futures_change_leverage(symbol=symbol, leverage=str(self.leverage))
        time.sleep(4)
        self.client.futures_create_order(symbol=symbol,
                                         positionSide=position_side,
                                         quantity=self.quantity,
                                         side=side,
                                         type="MARKET",
                                         )

    def cancel_all_orders(self, symbols_string):
        for symbol_string in symbols_string:
            self.client.futures_cancel_all_open_orders(symbol=symbol_string)


if __name__ == '__main__':
    from src.Main.main import Program
    connect = Program.connect_to_api()

    # connect.futures_create_order(symbol="ADAUSDT",
    #                                  type="MARKET",
    #                                  quantity=5,
    #                                  side="BUY",
    #                                  positionSide="LONG",
    #                                  )

    # time.sleep(10)

    connect.futures_create_order(symbol="ADAUSDT",
                                     type="MARKET",
                                     quantity=5,
                                     side="SELL",
                                     positionSide="LONG"
                                     )
