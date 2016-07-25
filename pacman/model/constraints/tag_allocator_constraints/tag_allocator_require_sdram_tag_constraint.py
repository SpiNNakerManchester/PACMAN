from pacman.model.constraints.tag_allocator_constraints\
    .abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
from pacman import exceptions


class TagAllocatorRequireSDRAMTagConstraint(AbstractTagAllocatorConstraint):
    """ Constraint that indicates that one or more SDRAM tags are required
    """

    def __init__(self, n_tags=None, tags=None):
        """

        :param n_tags:\
            The optional number of tags required (exactly one of n_tags or\
            is required)
        :type n_tags: int
        :param tags:\
            The optional list of tags required (exactly one of n_tags or\
            tags is required)
        :type tags: list of int
        """
        self._n_tags = n_tags
        self._tags = tags
        if (n_tags is None) == (tags is None):
            raise exceptions.PacmanConfigurationException(
                "Exactly one of n_tags or tags must be specified")

    @property
    def n_tags(self):
        """ The number of SDRAM tags required

        :rtype: int
        """
        if self._n_tags is None:
            return len(self._tags)
        return self._n_tags

    @property
    def tags(self):
        """ The list of SDRAM tags required or None if any tags are OK

        :rtype: list of int or None
        """
        return self._tags
