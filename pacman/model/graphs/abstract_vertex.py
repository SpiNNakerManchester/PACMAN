from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod, abstractproperty

@add_metaclass(AbstractBase)
class AbstractVertex(object):
    """ A vertex in a graph
    """

    __slots__ = ()

    @property
    def label(self):
        """ The label of the vertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
