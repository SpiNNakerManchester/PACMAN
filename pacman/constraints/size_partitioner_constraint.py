__author__ = 'daviess'

from pacman.constraints.abstract_partitioner_constraint import AbstractPartitionerConstraint


class SizePartitionerConstraint(AbstractPartitionerConstraint):
    """
    Creates an object to limit the number of atoms of a single\
    subvertex during the partitioner process
    """
    
    def __init__(self, size):
        """

        :param size: number of atoms to assign to each subvertex
        :type size: int
        :return: the constraint object created
        :rtype: pacman.constraints.size_partitioner_constraint.SizePartitionerConstraint
        :raise None: does not raise any known exceptions
        """
        self._size = size

    @property
    def size(self):
        """
        Returns the number of atoms to assign to each subvertex

        :return: the number of atoms to assign to each subvertex
        :rtype int
        :raise None: does not raise any known exceptions
        """
        return self._size
