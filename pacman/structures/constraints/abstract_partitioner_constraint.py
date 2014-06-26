__author__ = 'daviess'

from pacman.structures.constraints.abstract_constraint import AbstractConstraint


class AbstractPartitionerConstraint(AbstractConstraint):
    """
    Object which is inherited by every constraint class\
    related to the partitioner algorithm
    """
    
    def __init__(self):
        """
        
        :return: the partitioner constraint object just created
        :rtype: pacman.constraints.abstract_partitioner_constraint.AbstractPartitionerConstraint
        :raise None: Raises no known exceptions
        """
        pass
