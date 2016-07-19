from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractConstraint(object):
    """ A constraint of some sort which an algorithm might or might not support
    """
