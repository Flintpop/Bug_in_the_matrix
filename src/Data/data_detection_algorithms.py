
class Core:
    @staticmethod
    def finder(index: int, first_indexes: list, second_indexes: list, prices: list, high: bool):
        first_index_search = second_indexes[index]
        temp_high_low = prices[first_index_search]
        temp_index = 0
        i = 0
        limit = len(prices) - 2
        length = Core.macd_cross_detection(first_indexes, first_index_search, limit) - first_index_search

        while i < length and i <= limit:
            res = Core.comparator_numbers(high, prices[i + first_index_search], temp_high_low)
            if res:
                temp_high_low = prices[i + first_index_search]
                temp_index = i + first_index_search
            i += 1

        return temp_high_low, temp_index

    @staticmethod
    def comparator_numbers(boolean: bool, element_one, element_two):
        if boolean:
            res = element_one > element_two
        else:
            res = element_one < element_two
        return res

    @staticmethod
    def switcher(boolean: bool, first_index, second_index):
        if boolean:
            res = first_index, second_index
        else:
            res = second_index, first_index
        return res

    @staticmethod
    def macd_cross_detection(macd_indexes: list, value, max_value=2):
        crossed = False
        k = 0
        v = 0
        try:
            while not crossed:
                if macd_indexes[k] > value:
                    v = macd_indexes[k]
                    crossed = True
                k += 1
        except IndexError:
            v = max_value
        return v
