from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class DTCMResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    def __init__(self, dtcm):
        """

        :param dtcm: The amount of DTCM in bytes
        :type dtcm: int
        :raise None: No known exceptions are raised
        """
        self._dtcm = dtcm

    @property
    @overrides(AbstractResource.value)
    def value(self):
        return float(self._dtcm)
