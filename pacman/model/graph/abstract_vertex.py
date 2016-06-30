from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractVertex(object):
    """ A vertex in a graph
    """
