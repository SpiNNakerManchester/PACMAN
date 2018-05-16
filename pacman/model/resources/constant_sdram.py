from .abstract_sdram import AbstractSDRAM


class ConstantSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used  on a chip in the machine.

    This is used when the amount of SDRAM needed is not effected by runtime
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

    def get_total_sdram(self):
        return self._sdram
