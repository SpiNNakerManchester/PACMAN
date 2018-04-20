# pacman import
from .abstract_partitioner_constraint import AbstractPartitionerConstraint


class MinVertexAtomsConstraint(AbstractPartitionerConstraint):
    """ A constraint which limits the number of atoms on each division of a\
        vertex
    """

    __slots__ = [
        # The minimum number of atoms to split the application vertex into
        "_size"
    ]

    def __init__(self, size):
        """

        :param size: The minimum number of atoms to split the vertex into
        :type size: int
        """
        self._size = size

    @property
    def size(self):
        """ The minimum number of atoms to split the vertex into

        :rtype: int
        """
        return self._size

    def __repr__(self):
        return "MinVertexAtomsConstraint(size={})".format(self._size)

    def __eq__(self, other):
        if not isinstance(other, MinVertexAtomsConstraint):
            return False
        return self._size == other.size

    def __hash__(self):
        return hash((self._size,))
