from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty

from pacman.model.abstract_classes.abstract_has_constraints \
    import AbstractHasConstraints
from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel


@add_metaclass(ABCMeta)
class AbstractOutgoingEdgePartition(AbstractHasConstraints, AbstractHasLabel):
    """ A group of edges that start at the same vertex and share the same\
        semantics; used to group edges that can use the same multicast key
    """

    __slots__ = ()

    @abstractmethod
    def add_edge(self, edge):
        """ Add an edge to the partition

        :param edge: the edge to add
        :type: :py:class:`pacman.model.graph.abstract_edge.AbstractEdge`
        :raises:\
            :py:class:`pacman.execptions.PacmanInvalidParameterException`\
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
            :py:class:`pacman.model.graph.abstract_edge.AbstractEdge`
        """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at which all edges in this partition start

        :rtype: :py:class:`pacman.model.graph.AbstractVertex`
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
            :py:class:`pacman.model.graph.edge_traffic_type.EdgeTrafficType`
        """

    @abstractmethod
    def __contains__(self, edge):
        """ Determine if an edge is in the partition

        :param edge: The edge to check for the existence of
        :type edge: :py:class:`pacman.model.graph.abstract_edge.AbstractEdge`
        """
