from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from pacman.model.constraints import AbstractConstraint


@add_metaclass(AbstractBase)
class AbstractRouterConstraint(AbstractConstraint):
    """ A constraint on routing
    """

    __slots__ = []
