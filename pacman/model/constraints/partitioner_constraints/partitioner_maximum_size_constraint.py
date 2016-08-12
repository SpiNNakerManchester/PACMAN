# pacman import
from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint
from pacman.model.decorators.overrides import overrides


class PartitionerMaximumSizeConstraint(AbstractPartitionerConstraint):
    """ A constraint which limits the number of atoms on each division of a\
        vertex
    """

    __slots__ = [
        # The maximum number of atoms to split the application vertex into
        "_size"
    ]

    def __init__(self, size):
        """

        :param size: The maximum number of atoms to split the vertex into
        :type size: int
        """
        self._size = size

    @property
    def size(self):
        """ The maximum number of atoms to split the vertex into

        :rtype: int
        """
        return self._size

    @overrides(AbstractPartitionerConstraint.label)
    def label(self):
        return "partitioner max atom per core constraint with size {}"\
            .format(self._size)

