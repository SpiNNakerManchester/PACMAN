from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint

@add_metaclass(AbstractBase)
class AbstractRouterConstraint(AbstractConstraint):
    """ A constraint on routing
    """

    __slots__ = []
