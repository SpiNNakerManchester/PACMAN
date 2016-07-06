from pacman.model.graph.abstract_graph import AbstractGraph
from pacman.model.decorators import overrides.overrides
from pacman.exceptions import PacmanInvalidParameterException
from collections import defaultdict
from pacman.model.graph.outgoing_edge_partition import OutgoingEdgePartition
from pacman.exceptions import PacmanAlreadyExistsException


class SimpleGraph(AbstractGraph):
    """ A graph implementation that specifies the allowed types of the\
        vertices and edges
    """

    __slots__ = (

        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",

        # The classes of edges that are allowed in this graph
        "_allowed_edge_types",

        # The vertices of the graph
        "_vertices",

        # The outgoing edge partitions of the graph by name
        "_outgoing_edge_partitions_by_name",

        # The outgoing edges by pre-vertex
        "_outgoing_edges",

        # The incoming edges by post-vertex
        "_incoming_edges",

        # The outgoing edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex"
    )

    def __init__(self, allowed_vertex_types, allowed_edge_types):
        """

        :param allowed_vertex_types:\
            A tuple of types of vertex to be allowed in the graph
        :param allowed_edge_types:\
            A tuple of types of edges to be allowed in the graph
        """
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types

        self._vertices = list()
        self._outgoing_edge_partitions_by_name = dict()
        self._outgoing_edges = defaultdict(list)
        self._incoming_edges = defaultdict(list)
        self._outgoing_edge_partitions_by_pre_vertex = defaultdict(list)

    @overrides(AbstractGraph)
    def add_vertex(self, vertex):
        if not isinstance(vertex, self._allowed_vertex_types):
            raise PacmanInvalidParameterException(
                "vertex", vertex.__class__,
                "Vertices of this graph must be one of the following types:"
                " {}".format(self._allowed_vertex_types))

        self._vertices.append(vertex)

    @overrides(AbstractGraph)
    def add_edge(self, edge, outgoing_edge_partition_name):
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__)

        # Add the edge to the partition
        partition = None
        if ((edge.pre_vertex, outgoing_edge_partition_name) not in
                self._outgoing_edge_partitions_by_name):
            partition = OutgoingEdgePartition(outgoing_edge_partition_name)
            self._outgoing_edge_partitions_by_pre_vertex[
                edge.pre_vertex].append(partition)
            self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name] = partition
        else:
            partition = self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name]
        partition.add_edge(edge)

        # Add the edge to the indices
        self._outgoing_edges[edge.pre_vertex].append(edge)
        self._incoming_edges[edge.post_vertex].append(edge)

    @overrides(AbstractGraph)
    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        if ((outgoing_edge_partition.pre_vertex,
                outgoing_edge_partition.identifier) in
                self._outgoing_edge_partitions_by_name):
            raise PacmanAlreadyExistsException(
                OutgoingEdgePartition.__class__,
                (outgoing_edge_partition.pre_vertex,
                    outgoing_edge_partition.identifier))

        self._outgoing_edge_partitions_by_pre_vertex[
            outgoing_edge_partition.pre_vertex].append(outgoing_edge_partition)
        self._outgoing_edge_partitions_by_name[
            outgoing_edge_partition.pre_vertex,
            outgoing_edge_partition.identifier] = outgoing_edge_partition

    @property
    @overrides(AbstractGraph)
    def vertices(self):
        return self._vertices

    @property
    @overrides(AbstractGraph)
    def edges(self):
        return self._outgoing_edges.values()

    @property
    @overrides(AbstractGraph)
    def outgoing_edge_partitions(self):
        return self._outgoing_edge_partitions_by_name.values()

    @overrides(AbstractGraph)
    def get_edges_starting_at_vertex(self, vertex):
        return self._outgoing_edges[vertex]

    @overrides(AbstractGraph)
    def get_edges_ending_at_vertex(self, vertex):
        return self._incoming_edges[vertex]

    @overrides(AbstractGraph)
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    @overrides(AbstractGraph)
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)
