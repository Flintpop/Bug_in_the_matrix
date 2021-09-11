from binance.client import Client

from src.DivergenceRecognition.DivergenceInit import Divergence
from src.Miscellanous.security import GetData
from src.Miscellanous.Settings import Parameters

#####################################################################################
"""
Version : 1.2b
Date : 11 / 09 / 2021
"""
#####################################################################################


class Program:
    def __init__(self):
        # Get the decryption key
        self.client = self.connect()
        settings = Parameters()
        
        strategy = Divergence(client=self.client, settings=settings)
        strategy.scan()
    
    @staticmethod
    # Connect to binance api
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
