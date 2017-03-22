from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractproperty


@add_metaclass(AbstractBase)
class AbstractEdge(object):
    """ A directed edge in a graph between two vertices
    """

    __slots__ = ("_label")

    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        """ The label of the edge

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at the start of the edge

        :rtype: :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def post_vertex(self):
        """ The vertex at the end of the edge

        :rtype: :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of the edge

        :rtype:\
            py:class:`pacman.model.graphs.common.edge_traffic_type.EdgeTrafficType`
        """
