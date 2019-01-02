from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase
from pacman.model.constraints import AbstractConstraint


@add_metaclass(AbstractBase)
class AbstractPlacerConstraint(AbstractConstraint):
    """ A constraint on placement
    """

    __slots__ = []
