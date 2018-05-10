from spinn_utilities.overrides import overrides
from .abstract_resource import AbstractResource


class CPUCyclesPerTickResource(AbstractResource):
    """ Represents the number of CPU clock cycles per tick used or available\
        on a core of a chip in the machine
    """

    __slots__ = [

        # The number of cpu cycles needed for a given object
        "_cycles"
    ]

    def __init__(self, cycles):
        """

        :param cycles: The number of CPU clock cycles
        :type cycles: int
        :raise None: No known exceptions are raised
        """
        self._cycles = cycles

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return self._cycles
