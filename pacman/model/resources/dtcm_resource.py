from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class DTCMResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """
    
    def __init__(self, dtcm):
        """
        
        :param dtcm: The amount of dtcm in bytes
        :type dtcm: int
        :raise None: No known exceptions are raised
        """
        self._dtcm = dtcm

    @overrides(AbstractResource.get_value)
    def get_value(self):
        """ See :py:meth:`pacman.model.resources.abstract_resource\
        .AbstractResource.get_value`
        """
        return self._dtcm

    def add_to_usage_value(self, new_value):
        """
        supports adding new requirements after oriignally built.
        :param new_value:  the extra usage requirement
        :return:
        """
        self._dtcm += new_value
