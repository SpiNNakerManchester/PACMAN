from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(AbstractBase)
class AbstractKeyAllocatorConstraint(AbstractConstraint):
    """ A constraint on key allocation
    """

    __slots__ = []
