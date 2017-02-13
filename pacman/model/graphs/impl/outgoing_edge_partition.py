from pacman import exceptions
from spinn_machine.utilities.ordered_set import OrderedSet
from pacman.model.abstract_classes.impl.constrained_object \
    import ConstrainedObject
from pacman.model.decorators.delegates_to import delegates_to
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.abstract_outgoing_edge_partition \
    import AbstractOutgoingEdgePartition


class OutgoingEdgePartition(AbstractOutgoingEdgePartition):
    """ A collection of edges which start at a single vertex which have the\
        same semantics and so can share a single key
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

        # The constraints delegate
        "_constraints",

        # The label
        "_label",

        # The type of edges to accept
        "_allowed_edge_types",

        # The weight of traffic going down this partition
        "_traffic_weight"
    ]

    def __init__(
            self, identifier, allowed_edge_types, constraints=None,
            label=None, traffic_weight=1):
        """

        :param identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        """
        self._identifier = identifier
        self._edges = OrderedSet()
        self._allowed_edge_types = allowed_edge_types
        self._pre_vertex = None
        self._traffic_type = None
        self._label = label
        self._traffic_weight = traffic_weight

        self._constraints = ConstrainedObject(constraints)

    @delegates_to("_constraints", ConstrainedObject.add_constraint)
    def add_constraint(self, constraint):
        pass

    @delegates_to("_constraints", ConstrainedObject.add_constraints)
    def add_constraints(self, constraints):
        pass

    @delegates_to("_constraints", ConstrainedObject.constraints)
    def constraints(self):
        pass

    @property
    @overrides(AbstractOutgoingEdgePartition.label)
    def label(self):
        return self._label

    @overrides(AbstractOutgoingEdgePartition.add_edge)
    def add_edge(self, edge):

        # Check for an incompatible edge
        if not isinstance(edge, self._allowed_edge_types):
            raise exceptions.PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        # Check for an incompatible pre vertex
        if self._pre_vertex is None:
            self._pre_vertex = edge.pre_vertex

        elif edge.pre_vertex != self._pre_vertex:
            raise exceptions.PacmanConfigurationException(
                "A partition can only contain edges with the same"
                "pre_vertex")

        # Check for an incompatible traffic type
        if self._traffic_type is None:
            self._traffic_type = edge.traffic_type
        elif edge.traffic_type != self._traffic_type:
            raise exceptions.PacmanConfigurationException(
                "A partition can only contain edges with the same"
                " traffic_type")

        self._edges.append(edge)

    @property
    @overrides(AbstractOutgoingEdgePartition.identifier)
    def identifier(self):
        return self._identifier

    @property
    @overrides(AbstractOutgoingEdgePartition.edges)
    def edges(self):
        return self._edges

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
        return (
            "OutgoingEdgePartition("
            "identifier={}, edges={}, constraints={}, label={})".format(
                self._identifier, self._edges, self.constraints, self.label)
        )

    @overrides(AbstractOutgoingEdgePartition.__contains__)
    def __contains__(self, edge):
        """ Check if the edge is contained within this partition

        :param edge: the edge to search for.
        :return: boolean of true of false otherwise
        """
        return edge in self._edges
