from collections import defaultdict, OrderedDict

from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet

from pacman.exceptions import \
    PacmanAlreadyExistsException, PacmanInvalidParameterException
from pacman.model.graphs import AbstractGraph
from pacman.model.graphs.common import ConstrainedObject
from .outgoing_edge_partition import OutgoingEdgePartition


class Graph(ConstrainedObject, AbstractGraph):
    """ A graph implementation that specifies the allowed types of the\
        vertices and edges.
    """

    __slots__ = [
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
        # map between incoming edges and their associated partitions
        "_incoming_edges_by_partition_name",
        # The outgoing edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",
        # The label of the graph
        "_label"]

    def __init__(self, allowed_vertex_types, allowed_edge_types,
                 allowed_partition_types, label):
        """
        :param allowed_vertex_types:\
            A single or tuple of types of vertex to be allowed in the graph
        :param allowed_edge_types:\
            A single or tuple of types of edges to be allowed in the graph
        :param allowed_partition_types:\
            A single or tuple of types of partitions to be allowed in the graph
        :param label: The label on the graph, or None
        """
        super(Graph, self).__init__(None)
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types
        self._allowed_partition_types = allowed_partition_types

        self._vertices = OrderedSet()
        self._outgoing_edge_partitions_by_name = OrderedDict()
        self._outgoing_edges = defaultdict(OrderedSet)
        self._incoming_edges = defaultdict(OrderedSet)
        self._incoming_edges_by_partition_name = defaultdict(list)
        self._outgoing_edge_partitions_by_pre_vertex = defaultdict(OrderedSet)
        self._label = label

    @property
    @overrides(AbstractGraph.label)
    def label(self):
        return self._label

    @overrides(AbstractGraph.add_vertex)
    def add_vertex(self, vertex):
        if not isinstance(vertex, self._allowed_vertex_types):
            raise PacmanInvalidParameterException(
                "vertex", vertex.__class__,
                "Vertices of this graph must be one of the following types:"
                " {}".format(self._allowed_vertex_types))
        self._vertices.add(vertex)

    @overrides(AbstractGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        # verify that the edge is one suitable for this graph
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        if edge.pre_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", edge.pre_vertex, "pre-vertex must be known in graph")
        if edge.post_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", edge.post_vertex, "post-vertex must be known in graph")

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
        self._incoming_edges_by_partition_name[
            (edge.post_vertex, outgoing_edge_partition_name)].append(edge)
        self._incoming_edges[edge.post_vertex].add(edge)

    @overrides(AbstractGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, outgoing_edge_partition):

        # verify that this partition is suitable for this graph
        if not isinstance(
                outgoing_edge_partition, self._allowed_partition_types):
            raise PacmanInvalidParameterException(
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
    @overrides(AbstractGraph.n_vertices)
    def n_vertices(self):
        return len(self._vertices)

    @property
    @overrides(AbstractGraph.edges)
    def edges(self):
        return [
            edge
            for partition in self._outgoing_edge_partitions_by_name.values()
            for edge in partition.edges]

    @property
    @overrides(AbstractGraph.outgoing_edge_partitions)
    def outgoing_edge_partitions(self):
        return self._outgoing_edge_partitions_by_name.values()

    @property
    @overrides(AbstractGraph.n_outgoing_edge_partitions)
    def n_outgoing_edge_partitions(self):
        return len(self._outgoing_edge_partitions_by_name)

    @overrides(AbstractGraph.get_edges_starting_at_vertex)
    def get_edges_starting_at_vertex(self, vertex):
        return self._outgoing_edges[vertex]

    @overrides(AbstractGraph.get_edges_ending_at_vertex)
    def get_edges_ending_at_vertex(self, vertex):
        if vertex not in self._incoming_edges:
            return []
        return self._incoming_edges[vertex]

    @overrides(AbstractGraph.get_edges_ending_at_vertex_with_partition_name)
    def get_edges_ending_at_vertex_with_partition_name(
            self, vertex, partition_name):
        key = (vertex, partition_name)
        if key not in self._incoming_edges_by_partition_name:
            return []
        return self._incoming_edges_by_partition_name[key]

    @overrides(AbstractGraph.get_outgoing_edge_partitions_starting_at_vertex)
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    @overrides(AbstractGraph.get_outgoing_edge_partition_starting_at_vertex)
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)
