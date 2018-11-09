from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase
from pacman.model.constraints import AbstractConstraint


@add_metaclass(AbstractBase)
class AbstractPartitionerConstraint(AbstractConstraint):
    """ A constraint on the partitioning of a graph
    """

    __slots__ = []
