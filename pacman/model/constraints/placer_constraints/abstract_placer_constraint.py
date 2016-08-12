from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPlacerConstraint(AbstractConstraint):
    """ A constraint on placement
    """

    __slots__ = []

