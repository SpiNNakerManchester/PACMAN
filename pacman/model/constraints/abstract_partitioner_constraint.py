from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPartitionerConstraint(AbstractConstraint):
    """ A constraint that will be used by the partitioner
    """

    def is_constraint(self):
        return True

    @abstractmethod
    def is_partitioner_constraint(self):
        """ Determine if this is a partitioner constraint
        """
        pass

    def __init__(self, label):
        AbstractConstraint.__init__(self, label)
