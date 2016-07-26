from pacman.model.resources.abstract_resource import AbstractResource
from pacman import exceptions


class SDRAMTagResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    def __init__(self, n_tags, tag_ids):
        """

        :param n_tags: the number of sdram tags that this vertex will need
        :type n_tags: int
        :raises: None: No known exceptions are raised
        """
        self._n_tags = n_tags
        if (self._n_tags is None) == (tag_ids is None):
            raise exceptions.PacmanConfigurationException(
                "Exactly one of n_tags or tags must be specified")

    def get_value(self):
        return self._n_tags
