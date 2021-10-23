from binance.client import Client

from src.DivergenceRecognition.divergence_init import Divergence
from src.Miscellanous.security import GetData
from src.Miscellanous.settings import Parameters
import traceback

#####################################################################################
"""
Version : 1.3.1
Date : 23 / 10 / 2021
"""
#####################################################################################


class Program:
    def __init__(self):
        # Get the decryption key
        self.client = self.connect()
        settings = Parameters()

        macd_divergence = Divergence(client=self.client, settings=settings)
        macd_divergence.scan()

    # Connect to binance api
    @staticmethod
    def connect():
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
