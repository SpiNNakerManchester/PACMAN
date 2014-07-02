from pacman.model.constraints.abstract_partitioner_constraint import AbstractPartitionerConstraint


class PartitionerMaximumSizeConstraint(AbstractPartitionerConstraint):
    """ A constraint which limits the number of atoms of a single subvertex\
        during the partitioner process
    """
    
    def __init__(self, size):
        """

        :param size: The maximum number of atoms to assign to each subvertex
        :type size: int
        :raise None: does not raise any known exceptions
        """
        self._size = size
        
    def is_partitioner_constraint(self):
        """ Overridden method to indicate that this is a partitioner constraint
        """
        return True

    @property
    def size(self):
        """ The maximum number of atoms to assign to each subvertex

        :return: the maximum number of atoms to assign to each subvertex
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._size
