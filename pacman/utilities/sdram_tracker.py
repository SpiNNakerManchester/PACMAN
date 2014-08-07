

class SDRAMTracker(object):

    def __init__(self):
        self._mapper = dict()

    def add_usage(self, chip_x, chip_y, usage):
        key = self.key_from_chip_coords(chip_x, chip_y)
        if key in self._mapper.keys():
            self._mapper[key] += usage
        else:
            self._mapper[key] = usage

    def get_usage(self, chip_x, chip_y):
        key = self.key_from_chip_coords(chip_x, chip_y)
        if key in self._mapper.keys():
            return self._mapper[key]
        else:
            return 0

    @property
    def keys(self):
        return self._mapper.keys()

    @staticmethod
    def key_from_chip_coords(x, y):
        return "{}:{}".format(x, y)
