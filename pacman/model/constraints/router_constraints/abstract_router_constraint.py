from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractRouterConstraint(AbstractConstraint):
    """ A constraint on routing
    """

    __slots__ = []
