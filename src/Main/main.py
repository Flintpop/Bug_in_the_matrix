from binance.client import Client

from src.Strategies.EmaFractalsRecognition.ema_fractals_init import EmaFractalsInit
from src.Miscellaneous.security import GetData
from src.Miscellaneous.settings import Parameters
import traceback

#####################################################################################
"""
Version : 2.0b
Date : 04 / 02 / 2022
"""
#####################################################################################


class Program:
    def __init__(self):
        # Get the decryption key
        self.client = self.connect_to_api()
        settings = Parameters()

        # Init divergence algorithms
        ema_fractals = EmaFractalsInit(client=self.client, settings=settings)

        # Launch scan.
        ema_fractals.scan()

    # Connect to binance api
    @staticmethod
    def connect_to_api():
        successful_login = False
        client = None
        while not successful_login:
            try:
                key = GetData.login()
                client = None
                api_key, secret_key = key[0], key[1]
                client = Client(api_key, secret_key)
                successful_login = True
            except Exception as e:
                print(traceback.format_exc())
                print(e)
                print("Wrong password. Please try again.")

        key = ""
        print(key)

        if client is None:
            raise EnvironmentError
        return client


if __name__ == '__main__':
    program = Program()
