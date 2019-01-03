class SDRAMAvaiable(object):
    """ Represents an amount of SDRAM available on a chip in the machine.
    """

    __slots__ = [
        # The amount of SDRAM in bytes
        "_sdram"
    ]

    def __init__(self, sdram):
        """
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._sdram = sdram

    def get_sdram_available(self):
        """
        :return: The amount of SDRAM required, in bytes.
        """
        return self._sdram
