from enum import Enum
from pacman.model.partitionable_graph.fixed_route_partitionable_edge import \
    FixedRoutePartitionableEdge
from pacman.model.partitionable_graph.multi_cast_partitionable_edge import \
    MultiCastPartitionableEdge
from pacman.model.partitioned_graph.fixed_route_partitioned_edge import \
    FixedRoutePartitionedEdge
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman import exceptions

EDGE_TYPES = Enum(
    value="EDGE_TYPES",
    names=[("MULTI_CAST", 0),
           ("NEAREST_NEIGBOUR", 1),
           ("PEER_TO_PEER", 2),
           ("FIXED_ROUTE", 3)])


class OutgoingEdgePartition(object):
    """ A collection of edges from a single vertex which have the same\
        semantics and so can share a single key
    """

    def __init__(self, identifier):
        self._identifier = identifier
        self._type = None
        self._edges = list()

    def add_edge(self, edge):
        """ Add an edge into this outgoing edge partition
        :param edge: the instance of abstract edge to add to the list
        :return:
        """
        self._edges.append(edge)
        if self._type is None:
            self._type = self._deduce_type(edge)
        elif self._type != self._deduce_type(edge):
            raise exceptions.PacmanConfigurationException(
                "The edge {} was trying to be added to a partition {} which "
                "contains edges of type {}, yet the edge was of type {}. This"
                " is deemed an error. Please rectify this and try again.")

    @staticmethod
    def _deduce_type(edge):
        """ Deduce the enum from the edge type

        :param edge: the edge to deduce the type of
        :return: a enum type of edge_types
        """
        if isinstance(edge, MultiCastPartitionedEdge):
            return EDGE_TYPES.MULTI_CAST
        elif isinstance(edge, FixedRoutePartitionedEdge):
            return EDGE_TYPES.FIXED_ROUTE
        elif isinstance(edge, MultiCastPartitionableEdge):
            return EDGE_TYPES.MULTI_CAST
        elif isinstance(edge, FixedRoutePartitionableEdge):
            return EDGE_TYPES.FIXED_ROUTE
        else:
            raise exceptions.PacmanConfigurationException(
                "I don't recognise this type of edge, please rectify this and "
                "try again.")

    @property
    def identifier(self):
        """ The identifier for this outgoing edge partition
        :return:
        """
        return self._identifier

    @property
    def edges(self):
        """ The edges that are associated with this outgoing edge partition
        :return:
        """
        return self._edges

    @property
    def type(self):
        """ The type of the partition
        :return:
        """
        return self._type
