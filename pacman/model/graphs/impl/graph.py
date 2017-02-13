from collections import defaultdict

from pacman import exceptions
from pacman.exceptions import PacmanAlreadyExistsException
from spinn_machine.utilities.ordered_set import OrderedSet
from pacman.model.abstract_classes.impl.constrained_object \
    import ConstrainedObject
from pacman.model.decorators.delegates_to import delegates_to
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.abstract_graph import AbstractGraph
from pacman.model.graphs.impl.outgoing_edge_partition \
    import OutgoingEdgePartition


class Graph(AbstractGraph):
    """ A graph implementation that specifies the allowed types of the\
        vertices and edges
    """

    __slots__ = (

        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",

        # The classes of edges that are allowed in this graph
        "_allowed_edge_types",

        # The classes of outgoing edge partition that are allowed in this
        # graph
        "_allowed_partition_types",

        # The vertices of the graph
        "_vertices",

        # The outgoing edge partitions of the graph by name
        "_outgoing_edge_partitions_by_name",

        # The outgoing edges by pre-vertex
        "_outgoing_edges",

        # The incoming edges by post-vertex
        "_incoming_edges",

        # The outgoing edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",

        # The outgoing edge partitions by traffic type
        "_outgoing_edge_partitions_by_traffic_type",

        # The constraints delegate
        "_constraints"
    )

    def __init__(
            self, allowed_vertex_types, allowed_edge_types,
            allowed_partition_types):
        """

        :param allowed_vertex_types:\
            A single or tuple of types of vertex to be allowed in the graph
        :param allowed_edge_types:\
            A single or tuple of types of edges to be allowed in the graph
        :param allowed_partition_types:\
            A single or tuple of types of partitions to be allowed in the graph

        """
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types
        self._allowed_partition_types = allowed_partition_types

        self._vertices = OrderedSet()
        self._outgoing_edge_partitions_by_name = dict()
        self._outgoing_edges = defaultdict(OrderedSet)
        self._incoming_edges = defaultdict(OrderedSet)
        self._outgoing_edge_partitions_by_pre_vertex = defaultdict(OrderedSet)
        self._outgoing_edge_partitions_by_traffic_type = defaultdict(OrderedSet)

        self._constraints = ConstrainedObject()

    @delegates_to("_constraints", ConstrainedObject.add_constraint)
    def add_constraint(self, constraint):
        pass

    @delegates_to("_constraints", ConstrainedObject.add_constraints)
    def add_constraints(self, constraints):
        pass

    @delegates_to("_constraints", ConstrainedObject.constraints)
    def constraints(self):
        pass

    @overrides(AbstractGraph.add_vertex)
    def add_vertex(self, vertex):
        if not isinstance(vertex, self._allowed_vertex_types):
            raise exceptions.PacmanInvalidParameterException(
                "vertex", vertex.__class__,
                "Vertices of this graph must be one of the following types:"
                " {}".format(self._allowed_vertex_types))
        self._vertices.add(vertex)

    @overrides(AbstractGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        # verify that the edge is one suitable for this graph
        if not isinstance(edge, self._allowed_edge_types):
            raise exceptions.PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        # Add the edge to the partition
        partition = None
        if ((edge.pre_vertex, outgoing_edge_partition_name) not in
                self._outgoing_edge_partitions_by_name):
            partition = OutgoingEdgePartition(
                outgoing_edge_partition_name, self._allowed_edge_types)
            self._outgoing_edge_partitions_by_pre_vertex[
                edge.pre_vertex].add(partition)
            self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name] = partition
        else:
            partition = self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name]
        partition.add_edge(edge)

        # Add the edge to the indices
        self._outgoing_edges[edge.pre_vertex].add(edge)
        self._incoming_edges[edge.post_vertex].add(edge)

    @overrides(AbstractGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, outgoing_edge_partition):

        # verify that this partition is suitable for this graph
        if not isinstance(
                outgoing_edge_partition, self._allowed_partition_types):
            raise exceptions.PacmanInvalidParameterException(
                "outgoing_edge_partition", outgoing_edge_partition.__class__,
                "Partitions of this graph must be one of the following types:"
                " {}".format(self._allowed_partition_types))

        # check this partition doesn't already exist
        if ((outgoing_edge_partition.pre_vertex,
                outgoing_edge_partition.identifier) in
                self._outgoing_edge_partitions_by_name):
            raise PacmanAlreadyExistsException(
                "{}".format(OutgoingEdgePartition.__class__),
                (outgoing_edge_partition.pre_vertex,
                 outgoing_edge_partition.identifier))

        self._outgoing_edge_partitions_by_pre_vertex[
            outgoing_edge_partition.pre_vertex].add(outgoing_edge_partition)
        self._outgoing_edge_partitions_by_name[
            outgoing_edge_partition.pre_vertex,
            outgoing_edge_partition.identifier] = outgoing_edge_partition

    @property
    @overrides(AbstractGraph.vertices)
    def vertices(self):
        return self._vertices

    @property
    @overrides(AbstractGraph.edges)
    def edges(self):
        data = list()
        for edge_list in self._outgoing_edges.itervalues():
            for edge in edge_list:
                data.append(edge)
        return data

    @property
    @overrides(AbstractGraph.outgoing_edge_partitions)
    def outgoing_edge_partitions(self):
        return self._outgoing_edge_partitions_by_name.values()

    @overrides(AbstractGraph.get_edges_starting_at_vertex)
    def get_edges_starting_at_vertex(self, vertex):
        return self._outgoing_edges[vertex]

    @overrides(AbstractGraph.get_edges_ending_at_vertex)
    def get_edges_ending_at_vertex(self, vertex):
        return self._incoming_edges[vertex]

    @overrides(AbstractGraph.get_outgoing_edge_partitions_starting_at_vertex)
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    @overrides(AbstractGraph.get_outgoing_edge_partition_starting_at_vertex)
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)

    @overrides(AbstractGraph.get_outgoing_edge_partitions_with_traffic_type)
    def get_outgoing_edge_partitions_with_traffic_type(self, traffic_type):
        return self._outgoing_edge_partitions_by_traffic_type[traffic_type]
