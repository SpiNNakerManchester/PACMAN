from six import add_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from pacman.model.graphs.common.constrained_object import ConstrainedObject


@add_metaclass(ABCMeta)
class AbstractOutgoingEdgePartition(ConstrainedObject):
    """ A group of edges that start at the same vertex and share the same\
        semantics; used to group edges that can use the same multicast key
    """

    __slots__ = ("_label")

    def __init__(self, label, constraints):
        ConstrainedObject.__init__(self, constraints)
        self._label = label

    @property
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @abstractmethod
    def add_edge(self, edge):
        """ Add an edge to the partition

        :param edge: the edge to add
        :type: :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        :raises:\
            :py:class:`pacman.exceptions.PacmanInvalidParameterException`\
            if the starting vertex of the edge does not match that of the\
            edges already in the partition
        """

    @abstractproperty
    def identifier(self):
        """ The identifier of this outgoing edge partition

        :rtype: str
        """

    @abstractproperty
    def edges(self):
        """ The edges in this outgoing edge partition

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """

    @abstractproperty
    def n_edges(self):
        """ The number of edges in the partition

        :rtype: int
        """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at which all edges in this partition start

        :rtype: :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def traffic_weight(self):
        """ The weight of the traffic in this partition compared to other\
            partitions

        :rtype: int
        """

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of all the edges in this partition

        :rtype:\
            :py:class:`pacman.model.graphs.common.edge_traffic_type.EdgeTrafficType`
        """

    @abstractmethod
    def __contains__(self, edge):
        """ Determine if an edge is in the partition

        :param edge: The edge to check for the existence of
        :type edge: :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """
