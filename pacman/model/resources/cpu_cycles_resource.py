from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class CPUCyclesResource(AbstractResource):
    """ Represents the number of CPU clock cycles used or available\
        on a core of a chip in the machine for a simulation
    """

    def __init__(self, cycles):
        """

        :param cycles: The number of CPU clock cycles
        :type cycles: int
        :raise None: No known exceptions are raised
        """
        self._cycles = cycles

    @property
    @overrides(AbstractResource.value)
    def value(self):
        return float(self._cycles)
