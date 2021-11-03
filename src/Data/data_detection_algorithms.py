
class Core:
    @staticmethod
    # Get all the high_low variation in function of macd crosses
    def finder(index: int, first_indexes: list, second_indexes: list, prices: list, high: bool):
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
        if boolean:
            bool_return = x > y
        else:
            bool_return = x < y
        return bool_return

    @staticmethod
    def switcher(boolean: bool, x, y):
        if boolean:
            values_switched = x, y
        else:
            values_switched = y, x
        return values_switched

    @staticmethod
    # Returns index of macd cross after macd_indexes
    def macd_cross_detection(macd_indexes: list, value, max_value=2):
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
