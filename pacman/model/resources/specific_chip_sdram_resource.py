from pacman.model.resources import AbstractSDRAM


class SpecificChipSDRAMResource(object):
    """ Represents the SDRAM required for this Chip
    """

    __slots__ = [

        # The number of cores that need to be allocated on a give chip
        "_sdram_usage",

        # the chip that has this SDRAM usage
        "_chip"
    ]

    def __init__(self, chip, sdram_usage):
        """
        :param sdram_usage:\
            The amount of SDRAM in bytes needed to be pre-allocated
        :type sdram_usage: AbstractSDRAM
            The amount of SDRAM in bytes needed to be preallocated
        :param chip: chip of where the SDRAM is to be allocated
        :type chip: :py:class:`spinn_machine.Chip`
        :raise None: No known exceptions are raised
        """
        assert isinstance(sdram_usage, AbstractSDRAM)
        self._sdram_usage = sdram_usage
        self._chip = chip

    @property
    def sdram_usage(self):
        return self._sdram_usage

    @property
    def chip(self):
        return self._chip

    def get_value(self):
        """
        :return: The chip for which it is required, and the amount of SDRAM\
            required thereon, in bytes.
        """
        return self._chip, self._sdram_usage
