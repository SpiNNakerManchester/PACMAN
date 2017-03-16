from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

@add_metaclass(AbstractBase)
class AbstractConstraint(object):
    """ A constraint of some sort which an algorithm might or might not support
    """

    __slots__ = []
