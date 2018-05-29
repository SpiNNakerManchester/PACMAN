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

    def get_total_sdram(self, n_timesteps):
        return self._sdram

    @property
    def fixed(self):
        return self._sdram

    @property
    def per_timestep(self):
        return 0

    def __add__(self, other):
        if isinstance(other, ConstantSDRAM):
            return ConstantSDRAM(
                self._sdram + other._sdram)
        else:
            # The other is more complex so delegate to it
            return other.__add__(self)

