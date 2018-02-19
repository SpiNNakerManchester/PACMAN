from .abstract_resource import AbstractResource
from spinn_utilities.overrides import overrides


class SDRAMResource(AbstractResource):
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

    @overrides(AbstractResource.get_value)
    def get_value(self):
        """ See \
            :py:meth:`pacman.model.resources.AbstractResource.get_value`
        """
        return self._sdram
