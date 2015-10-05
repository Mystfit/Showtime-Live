class Utils():

    @staticmethod
    def clamp(value, smallest, largest):
        return min(largest, max(value, smallest))
