from .abstract_resource import AbstractResource
from spinn_utilities.overrides import overrides


class DTCMResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    __slots__ = [

        # The number of DTCM (in bytes) needed for a given object
        "_dtcm"
    ]

    def __init__(self, dtcm):
        """

        :param dtcm: The amount of DTCM in bytes
        :type dtcm: int
        :raise None: No known exceptions are raised
        """
        self._dtcm = dtcm

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return self._dtcm
