class SpecificChipSDRAMResource(object):
    """ Represents the number of cores that need to be allocated
    """

    __slots__ = [

        # The number of cores that need to be allocated on a give chip
        "_sdram_usage",

        # the chip that has these cores allocated
        "_chip"
    ]

    def __init__(self, chip, sdram_usage):
        """

        :param sdram_usage:\
            The amount of SDRAM in bytes needed to be pre-allocated
        :type sdram_usage: int
        :param chip: chip of where the SDRAM is to be allocated
        :type chip: SpiNNMachine.chip.Chip
        :raise None: No known exceptions are raised
        """
        self._sdram_usage = sdram_usage
        self._chip = chip

    @property
    def sdram_usage(self):
        return self._sdram_usage

    @property
    def chip(self):
        return self._chip

    def get_value(self):
        return self._chip, self._sdram_usage
