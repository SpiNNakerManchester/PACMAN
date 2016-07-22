# pacman import
from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint


class PartitionerMaximumSizeConstraint(AbstractPartitionerConstraint):
    """ A constraint which limits the number of atoms on each division of a\
        vertex
    """

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
