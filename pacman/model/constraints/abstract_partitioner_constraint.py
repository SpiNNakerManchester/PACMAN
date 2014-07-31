from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPartitionerConstraint(AbstractConstraint):
    """ A constraint that will be used by the partitioner
    """

    def __init__(self, label):
        AbstractConstraint.__init__(self, label)
