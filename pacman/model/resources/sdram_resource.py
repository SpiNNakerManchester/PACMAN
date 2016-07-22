from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class SDRAMResource(AbstractResource):
    """ Represents an amount of SDRAM used or available on a chip in the machine
    """

    def __init__(self, sdram):
        """

        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._sdram = sdram

    @property
    @overrides(AbstractResource.value)
    def value(self):
        return float(self._sdram)
