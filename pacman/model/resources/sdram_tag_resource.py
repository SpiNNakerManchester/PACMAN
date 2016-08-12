from pacman.model.resources.abstract_resource import AbstractResource
from pacman import exceptions
from pacman.model.decorators.overrides import overrides


class SDRAMTagResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    __slots__ = [

        # the number of sdram tags that this vertex will need
        "_n_tags",

        # iterable of ints. The list of tag ids needed
        "_tag_ids"
    ]

    def __init__(self, n_tags, tag_ids):
        """

        :param n_tags: the number of sdram tags that this vertex will need
        :type n_tags: int
        :param tag_ids: the list of tag ids needed
        :type tag_ids: iterable of int
        :raises: None: No known exceptions are raised
        """
        self._n_tags = n_tags
        self._tag_ids = tag_ids
        if (self._n_tags is None) == (tag_ids is None):
            raise exceptions.PacmanConfigurationException(
                "Exactly one of n_tags or tags must be specified")

    @property
    def n_tags(self):
        return self._n_tags

    def add_to_n_tags(self, n_more_tags):
        if self._n_tags is not None:
            self._n_tags += n_more_tags
        else:
            raise exceptions.PacmanConfigurationException(
                "cant add more n_tags when tag_ids have been used")

    @property
    def tag_ids(self):
        return self._tag_ids

    def add_to_tag_ids(self, more_tag_ids):
        if self._tag_ids is not None:
            self._tag_ids.extend(more_tag_ids)
        else:
            raise exceptions.PacmanConfigurationException(
                "cant add more tag_ids when n_tags have been used")

    def add_tags(self, n_tags, tag_ids):
        if (n_tags is None) == (tag_ids is None):
            raise exceptions.PacmanConfigurationException(
                "Exactly one of n_tags or tags must be specified")
        elif n_tags is not None:
            self.add_to_n_tags(n_tags)
        elif tag_ids is not None:
            self.add_to_tag_ids(tag_ids)

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return [self._n_tags, self._tag_ids]
