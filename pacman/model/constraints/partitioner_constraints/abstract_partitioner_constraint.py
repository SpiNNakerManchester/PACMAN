from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPartitionerConstraint(AbstractConstraint):
    """ A constraint on the partitioning of a graph
    """

    __slots__ = []
