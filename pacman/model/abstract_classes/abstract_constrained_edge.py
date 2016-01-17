from abc import ABCMeta
from six import add_metaclass

from pacman.model.abstract_classes.abstract_constrained_object import \
    AbstractConstrainedObject
from pacman.model.abstract_classes.abstract_labeled import \
    AbstractLabeled


@add_metaclass(ABCMeta)
class AbstractConstrainedEdge(AbstractConstrainedObject):

    def __init__(self, label, constraints=None):
        AbstractConstrainedObject.__init__(self, constraints)
        AbstractLabeled.__init__(self, label)
