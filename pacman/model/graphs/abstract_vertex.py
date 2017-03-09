from six import add_metaclass
from abc import ABCMeta
from pacman.model.graphs.common.constrained_object import ConstrainedObject


@add_metaclass(ABCMeta)
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
