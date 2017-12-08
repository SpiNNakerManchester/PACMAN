from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import \
    PacmanInvalidParameterException, PacmanConfigurationException
from pacman.model.decorators import overrides
from pacman.model.graphs import AbstractOutgoingEdgePartition
from pacman.model.graphs.common import ConstrainedObject

_REPR_TEMPLATE = \
    "OutgoingEdgePartition(identifier={}, edges={}, constraints={}, label={})"


class OutgoingEdgePartition(ConstrainedObject, AbstractOutgoingEdgePartition):
    """ A collection of edges which start at a single vertex which have the
        same semantics and so can share a single key

    :param identifier: The identifier of the partition
    :param allowed_edge_types: The types of edges allowed
    :param constraints: Any initial constraints
    :param label: An optional label of the partition
    :param traffic_weight: The weight of traffic going down this partition
    """

    __slots__ = [
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
        # The vertex at the start of all the edges
        "_pre_vertex",
        # The traffic type of all the edges
        "_traffic_type",
        # The type of edges to accept
        "_allowed_edge_types",
        # The weight of traffic going down this partition
        "_traffic_weight",
        # The label of the graph
        "_label"
    ]

    def __init__(
            self, identifier, allowed_edge_types, constraints=None,
            label=None, traffic_weight=1):
        ConstrainedObject.__init__(self, constraints)
        self._label = label
        self._identifier = identifier
        self._edges = OrderedSet()
        self._allowed_edge_types = allowed_edge_types
        self._pre_vertex = None
        self._traffic_type = None
        self._traffic_weight = traffic_weight

    @property
    @overrides(AbstractOutgoingEdgePartition.label)
    def label(self):
        return self._label

    @overrides(AbstractOutgoingEdgePartition.add_edge)
    def add_edge(self, edge):
        # Check for an incompatible edge
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        # Check for an incompatible pre vertex
        if self._pre_vertex is None:
            self._pre_vertex = edge.pre_vertex

        elif edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                "pre_vertex")

        # Check for an incompatible traffic type
        if self._traffic_type is None:
            self._traffic_type = edge.traffic_type
        elif edge.traffic_type != self._traffic_type:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                " traffic_type")

        self._edges.add(edge)

    @property
    @overrides(AbstractOutgoingEdgePartition.identifier)
    def identifier(self):
        return self._identifier

    @property
    @overrides(AbstractOutgoingEdgePartition.edges)
    def edges(self):
        return self._edges

    @property
    @overrides(AbstractOutgoingEdgePartition.n_edges)
    def n_edges(self):
        return len(self._edges)

    @property
    @overrides(AbstractOutgoingEdgePartition.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractOutgoingEdgePartition.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    @overrides(AbstractOutgoingEdgePartition.traffic_weight)
    def traffic_weight(self):
        return self._traffic_weight

    def __repr__(self):
        return _REPR_TEMPLATE.format(
            self._identifier, self._edges, self.constraints, self.label)

    @overrides(AbstractOutgoingEdgePartition.__contains__)
    def __contains__(self, edge):
        """ Check if the edge is contained within this partition

        :param edge: the edge to search for.
        :return: boolean of true of false otherwise
        """
        return edge in self._edges
