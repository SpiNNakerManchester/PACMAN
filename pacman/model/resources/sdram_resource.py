class SDRAMResource(object):
    """ Represents an amount of SDRAM used or available on a chip in the\
        machine.
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

    def get_value(self):
        return self._sdram
