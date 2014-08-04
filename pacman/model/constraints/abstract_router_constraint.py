from abc import ABCMeta
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractRouterConstraint(AbstractConstraint):
    """ A constraint that will be used by the router
    """

    def __init__(self, label):
        AbstractConstraint.__init__(self, label)
