from abc import ABCMeta
from six import add_metaclass

from pacman.model.abstract_classes.abstract_has_constraints import \
    AbstractHasConstraints
from pacman.model.abstract_classes.simple_labeled_object import \
    SimpleLabeledObject


@add_metaclass(ABCMeta)
class AbstractConstrainedEdge(AbstractHasConstraints, SimpleLabeledObject):

    def __init__(self, label, constraints=None):
        AbstractHasConstraints.__init__(self, constraints)
        SimpleLabeledObject.__init__(self, label)
