from binance.client import Client

from src.DivergenceRecognition.DivergenceInit import Divergence
from src.Miscellanous.security import GetData
from src.Miscellanous.Settings import Parameters

#####################################################################################
"""
Version : 1.2
Date : 25 / 09 / 2021
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
        key = GetData.login()
        successful_login = False
        client = None
        while not successful_login:
            try:
                client = Client(key[0], key[1])
                successful_login = True
            except Exception as e:
                print(e)
                print("Please try again.")
        key = ""
        print(key)
        if client is None:
            raise EnvironmentError
        return client


if __name__ == '__main__':
    program = Program()
