class Utils():

    @staticmethod
    def clamp(value, smallest, largest):
        return min(largest, max(value, smallest))

    @staticmethod
    def truncate_float(f, n):
        '''Truncates/pads a float f to n decimal places without rounding'''
        s = '%.12f' % f
        i, p, d = s.partition('.')
        return '.'.join([i, (d+'0'*n)[:n]])