from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPartitionerConstraint(AbstractConstraint):
    """ A constraint that will be used by the partitioner
    """
    
    def is_constraint(self):
        """ Overridden method indicating that this is a constraint
        
        :return: True
        :rtype: bool
        """
        return True
    
    @abstractmethod
    def is_partitioner_constraint(self):
        """ Ensures that this is a partitioner constraint
        
        :return: True if this is a partitioner constraint
        :rtype: bool
        """
        pass
