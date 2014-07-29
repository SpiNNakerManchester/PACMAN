from spinn_machine.sdram import SDRAM


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
            return SDRAM.DEFAULT_SDRAM_BYTES - self._mapper[key]
        else:
            return SDRAM.DEFAULT_SDRAM_BYTES
