from abc import ABCMeta, abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractConstraint(object):
    """ A constraint of some sort which an algorithm might or might not support
    """

    __slots__ = []

    @abstractmethod
    def label(self):
        pass