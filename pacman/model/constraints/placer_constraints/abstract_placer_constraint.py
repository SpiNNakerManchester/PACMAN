from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint

@add_metaclass(AbstractBase)
class AbstractPlacerConstraint(AbstractConstraint):
    """ A constraint on placement
    """

    __slots__ = []
