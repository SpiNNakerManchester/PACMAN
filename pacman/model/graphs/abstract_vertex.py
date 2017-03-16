from six import add_metaclass

from pacman.model.graphs.common.constrained_object import ConstrainedObject
from spinn_utilities.abstract_base import AbstractBase, abstractmethod, abstractproperty

@add_metaclass(AbstractBase)
class AbstractVertex(ConstrainedObject):
    """ A vertex in a graph
    """

    __slots__ = ("_label")

    def __init__(self, label, constraints):
        ConstrainedObject.__init__(self, constraints)
        self._label = label

    @property
    def label(self):
        """ The label of the vertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
