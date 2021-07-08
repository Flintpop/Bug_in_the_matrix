
class Core:
    @staticmethod
    def finder(index, first_indexes, second_indexes, prices, high):  # Not tested ! Looks to work though.
        temp_high_low = Core.finder_temp(high)
        temp_index = 0
        i = 0
        limit = len(prices) - 2  # Maybe -2 is too much, but one for to go in list and another one to avoid unclosed
        # candle.
        length = Core.macd_cross_detection(first_indexes, second_indexes[index], limit) - second_indexes[index]

        while i < length and i <= limit:
            res = Core.comparator_numbers(high, float(prices[i + second_indexes[index]]), float(temp_high_low))
            if res:
                temp_high_low = prices[i + second_indexes[index]]
                temp_index = i + second_indexes[index]
            i += 1

        return temp_high_low, temp_index

    @staticmethod
    def finder_temp(high):
        if high:
            temp_high_low = 0
        else:
            temp_high_low = 1000000
        return temp_high_low

    @staticmethod
    def comparator_numbers(boolean, element_one, element_two):
        if boolean:
            res = element_one > element_two
        else:
            res = element_one < element_two
        return res

    @staticmethod
    def switcher(boolean, first_index, second_index):
        if boolean:
            res = first_index, second_index
        else:
            res = second_index, first_index
        return res

    @staticmethod
    def macd_cross_detection(macd_indexes, value, max_value=2):
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

    @staticmethod
    def indicator_finder(macd_limit, bear, bull, compared, high):  # Not completed; buggy.
        i = 0
        first_index, second_index = Core.switcher(high, bear, bull)
        list_return = [[], []]
        while i < macd_limit:
            temp_high_low, temp_index = Core.finder(i, first_index, second_index, compared, high)
            list_return[0].append(temp_high_low)
            list_return[1].append(temp_index)
        return list_return

    @staticmethod
    def list_appender(list_one: list, list_two: list, value, value_two):  # Useless tbh
        list_one.append(value)
        list_two.append(value_two)
