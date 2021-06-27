
class Detector:
    @staticmethod
    def finder_high(index, first_indexes, second_indexes, prices):
        temp_high_low = 0
        temp_index = 0
        i = 0
        limit = len(prices)
        length = Detector.macd_cross_detection(first_indexes, second_indexes[index], limit) - second_indexes[index]
        while i < length and i < limit:
            if float(prices[i + second_indexes[index]]) > float(temp_high_low):
                temp_high_low = prices[i + second_indexes[index]]
                temp_index = i + second_indexes[index]
            i += 1
        return temp_high_low, temp_index

    @staticmethod
    def finder_low(index, first_indexes, second_indexes, prices):
        temp_high_low = 1000000
        temp_index = 0
        i = 0
        limit = len(prices)
        length = Detector.macd_cross_detection(first_indexes, second_indexes[index], limit) - second_indexes[index]
        while i < length and i < limit:
            if float(prices[i + second_indexes[index]]) < float(temp_high_low):
                temp_high_low = prices[i + second_indexes[index]]
                temp_index = i + second_indexes[index]
            i += 1
        return temp_high_low, temp_index

    @staticmethod
    def macd_cross_detection(macd_indexes, value, max_value=0):
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
