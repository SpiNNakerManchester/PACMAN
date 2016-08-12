from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractKeyAllocatorConstraint(AbstractConstraint):
    """ A constraint on key allocation
    """

    __slots__ = []

