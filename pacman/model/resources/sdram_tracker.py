from pacman import constants as pacman_constants


class SDRAMTracker(object):

    def __init__(self):
        self._mapper = dict()

    def add_usage(self, chip_x, chip_y, usage):
        key = "{}:{}".format(chip_x, chip_y)
        if key in self._mapper.keys():
            self._mapper[key] += usage
        else:
            self._mapper[key] = usage

    def get_usage(self, chip_x, chip_y):
        key = "{}:{}".format(chip_x, chip_y)
        if key in self._mapper.keys():
            return pacman_constants.SDRAM_AVILABLE_BYTES - self._mapper[key]
        else:
            return pacman_constants.SDRAM_AVILABLE_BYTES
