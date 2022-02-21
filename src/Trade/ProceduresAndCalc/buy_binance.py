from src.Trade.ProceduresAndCalc.calc_orders import CalcOrders
import time


class BinanceOrders(CalcOrders):
    def __init__(self, coin):
        super().__init__(coin)

    def open_trade_market(self, symbol_string: str):
        """
        Open a position in market mode (Taker fees) with the parameters of CalcOrders.\n
        :param symbol_string: The pair to trade with, i.e. "BTCBUSD"
        :return: Nothing. It opens the position.
        """
        if self.coin.long:
            side = "BUY"
            position_side = "LONG"
        else:
            side = "SELL"
            position_side = "SHORT"

        BinanceOrders.place_market_order(self,
                                         position_side=position_side,
                                         side=side,
                                         symbol_string=symbol_string
                                         )

    def place_limit_order(self, symbol_string: str, entry_price):
        """
        Place the limit type buy order to long or short, with the right leverage and quantity.\n
        :param symbol_string: The pair to trade with, i.e. "BTCBUSD"
        :param entry_price: The limit order buy price
        :return: Nothing. Places the order on binance
        """
        if self.coin.long:
            side = "BUY"
            position_side = "LONG"
        else:
            side = "SELL"
            position_side = "SHORT"

        BinanceOrders.place_order_limit(self,
                                        position_side=position_side,
                                        side=side,
                                        symbol_string=symbol_string,
                                        price=entry_price)

    def close_pos(self, symbol_string):
        """
        Closes the open position of the trade related to the symbol sent in parameter.\n
        :param symbol_string: The pair to trade with, i.e. "BTCBUSD"
        :return: Nothing. Closes the position. Error handling in the function.
        """
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

    def place_sl_and_tp(self, symbol_string: str):
        """
        Places the stop loss and the take profit according to the self.long mode.\n
        :param symbol_string: The pair to trade with, i.e. "BTCBUSD"
        :return: Nothing. Places stop loss and take profit according to the class CalcOrders.
        """
        BinanceOrders.take_profit_stop_loss(self, "STOP_MARKET", self.stop_loss, symbol_string)
        BinanceOrders.take_profit_stop_loss(self, "TAKE_PROFIT_MARKET", self.take_profit, symbol_string)

    def take_profit_stop_loss(self, type_action, price_stop, symbol_string: str):
        side = "BUY"
        position_side = "SHORT"
        if self.coin.long:
            side = "SELL"
            position_side = "LONG"
        self.client.futures_create_order(symbol=symbol_string,
                                         closePosition="true",
                                         type=str(type_action),
                                         stopPrice=str(price_stop),
                                         side=side,
                                         positionSide=position_side
                                         )

    def place_market_order(self, position_side: str, side: str, symbol_string: str):
        self.client.futures_change_leverage(symbol=symbol_string, leverage=str(self.leverage))
        time.sleep(4)
        self.client.futures_create_order(symbol=symbol_string,
                                         positionSide=position_side,
                                         quantity=self.quantity,
                                         side=side,
                                         type="MARKET",
                                         )

    def place_order_limit(self, position_side: str, side: str, symbol_string: str, price):
        self.client.futures_change_leverage(symbol=symbol_string, leverage=str(self.leverage))
        time.sleep(4)
        self.client.futures_create_order(symbol=symbol_string,
                                         positionSide=position_side,
                                         quantity=self.quantity,
                                         side=side,
                                         type="LIMIT",
                                         price=price,
                                         timeInForce="GTC"
                                         )

    def cancel_all_orders(self, symbols_string: str):
        for symbol_string in symbols_string:
            self.client.futures_cancel_all_open_orders(symbol=symbol_string)

    def cancel_all_orders_symbol(self, symbol_string: str):
        self.client.futures_cancel_all_open_orders(symbol=symbol_string)


if __name__ == '__main__':
    from src.Main.main import Program

    connect = Program.connect_to_api()

    connect.futures_create_order(symbol="ETHUSDT",
                                 type="STOP",
                                 quantity=0.009,
                                 price=2000,
                                 stopPrice=2000,
                                 side="SELL",
                                 positionSide="LONG")
