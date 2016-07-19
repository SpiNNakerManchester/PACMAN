from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractTagAllocatorConstraint(AbstractConstraint):
    """ A constraint on (ip or reverse ip) tag allocation
    """
