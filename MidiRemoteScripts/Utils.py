class Utils:
    def __init__(self):
        pass

    @staticmethod
    def clamp(value, smallest, largest):
        return min(largest, max(value, smallest))

    @staticmethod
    def truncate_float(f, n):
        """Truncates/pads a float f to n decimal places without rounding

        Args:
            f: Float value to truncate.
            n: Number of decimal places to limit float value to.
        """
        s = '%.12f' % f
        i, p, d = s.partition('.')
        return '.'.join([i, (d+'0'*n)[:n]])
