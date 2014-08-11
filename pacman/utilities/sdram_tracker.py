

class SDRAMTracker(object):

    def __init__(self):
        self._mapper = dict()

    def add_usage(self, chip_x, chip_y, usage):
        key = (chip_x, chip_y)
        if key in self._mapper.keys():
            self._mapper[key] += usage
        else:
            self._mapper[key] = usage

    def get_usage(self, chip_x, chip_y):
        key = (chip_x, chip_y)
        if key in self._mapper.keys():
            return self._mapper[key]
        else:
            return 0

    @property
    def keys(self):
        return self._mapper.keys()
