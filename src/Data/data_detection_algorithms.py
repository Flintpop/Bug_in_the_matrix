class Core:
    """
    Class used to store core algorithms of the "DivergenceRecognition" trading strategy algorithm.
    The functions stored here are designed to work either for short trades or long trades.
    """

    @staticmethod
    def finder(index: int, first_indexes: list, second_indexes: list, prices: list, high: bool):
        """
        Get all high or low variation of prices or macd data in relationship to macd crossed.\n
        :param index: Starting point of the algorithm
        :param first_indexes: First macd data
        :param second_indexes: Second macd data
        :param prices: Prices data corresponding to the macd indicator
        :param high: Short or long boolean flag
        :return: The high or low of prices or macd data and the indexes of them
        """
        first_index_search = second_indexes[index]
        high_low_local = prices[first_index_search]
        h_l_index = 0
        i = 0
        limit = len(prices) - 2
        length = Core.macd_cross_detection(first_indexes, first_index_search, limit) - first_index_search

        while i < length and i <= limit:
            res = Core.comparator_numbers(high, prices[i + first_index_search], high_low_local)
            if res:
                high_low_local = prices[i + first_index_search]
                h_l_index = i + first_index_search
            i += 1

        return high_low_local, h_l_index

    @staticmethod
    def comparator_numbers(boolean: bool, x, y):
        """
        Simple function used to enable generic use for both short and long trading operations. Compare values.\n
        :param boolean: Short or long flag
        :param x: Value X
        :param y: Value Y
        :return: Is X superior to Y if long or reverse if short
        """
        if boolean:
            return x > y
        return x < y

    @staticmethod
    def switcher(boolean: bool, x, y):
        """
        Simple function used to enable generic use for both short and long trading operations. Switches values.\n
        :param boolean: Short or long flag
        :param x: Value X
        :param y: Value Y
        :return: x, y if long and reverse if short.
        """
        if boolean:
            return x, y
        return y, x

    @staticmethod
    def macd_cross_detection(macd_indexes: list, value, max_value=2):
        """
        Returns an index of a macd cross of lines after a set of macd indexes.\n
        :param macd_indexes: List of macd indexes that is used to compare and get a cross of macd lines
        :param value: Value of macd line to be superior to
        :param max_value: In case of error, if it does not find a cross it returns max_value. Optional parameter.
        :return: Index of a macd cross in relationship to macd_indexes and value.
        """
        crossed = False
        macd_index = 0
        cross_index = 0
        try:
            while not crossed:
                if macd_indexes[macd_index] > value:
                    cross_index = macd_indexes[macd_index]
                    crossed = True
                macd_index += 1
        except IndexError:
            cross_index = max_value
        return cross_index
