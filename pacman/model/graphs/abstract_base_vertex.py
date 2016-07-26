from six import add_metaclass
from abc import ABCMeta

from pacman.model.abstract_classes.abstract_has_constraints \
    import AbstractHasConstraints
from pacman.model.abstract_classes.abstract_has_label \
    import AbstractHasLabel


@add_metaclass(ABCMeta)
class AbstractBaseVertex(AbstractHasConstraints, AbstractHasLabel):
    """ A vertex in a graph
    """

    __slots__ = ()
