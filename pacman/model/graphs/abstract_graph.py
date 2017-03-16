from six import add_metaclass

from pacman.model.graphs.common.constrained_object import ConstrainedObject
from spinn_utilities.abstract_base import AbstractBase, abstractmethod, abstractproperty

@add_metaclass(AbstractBase)
class AbstractGraph(ConstrainedObject):
    """ A graph
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
    def add_vertex(self, vertex):
        """ Add a vertex to the graph

        :param vertex: The vertex to add
        :type vertex:\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :raises PacmanInvalidParameterException:\
            If the vertex is not of a valid type
        """

    def add_vertices(self, vertices):
        """ Add a collection of vertices to the graph.

        :param vertices: The vertices to add
        :type vertices: an iterable of \
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :raises PacmanInvalidParameterException:\
            If any vertex is not of a valid type
        """
        for v in vertices:
            self.add_vertex(v)

    @abstractmethod
    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph

        :param edge: The edge to add
        :type edge: :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        :param outgoing_edge_partition_name: \
            The name of the edge partition to add the edge to; each edge\
            partition is the partition of edges that start at the same vertex
        :type outgoing_edge_partition_name: str
        :raises PacmanInvalidParameterException:\
            If the edge is not of a valid type or if edges have already been\
            added to this partition that start at a different vertex to this\
            one
        """

    def add_edges(self, edges, outgoing_edge_partition_name):
        """ Add a collection of edges to the graph

        :param edges: The edges to add
        :type edges: an iterable of \
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        :param outgoing_edge_partition_name: \
            The name of the edge partition to add the edges to; each edge\
            partition is the partition of edges that start at the same vertex
        :type outgoing_edge_partition_name: str
        :raises PacmanInvalidParameterException:\
            If any edge is not of a valid type or if edges have already been\
            added to this partition that start at a different vertex to this\
            one
        """
        for e in edges:
            self.add_edge(e, outgoing_edge_partition_name)

    @abstractmethod
    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        """ Add an outgoing edge partition to the graph

        :param outgoing_edge_partition: The outgoing edge partition to add
        :type outgoing_edge_partition:\
            :py:class:`pacman.model.graphs.abstract_outgoing_edge_partition.AbstractOutgoingEdgePartition`
        :raises PacmanAlreadyExistsException:\
            If a partition already exists with the same pre_vertex and\
            identifier
        """

    @abstractproperty
    def vertices(self):
        """ The vertices in the graph

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def n_vertices(self):
        """ The number of vertices in the graph

        :rtype: int
        """

    @abstractproperty
    def edges(self):
        """ The edges in the graph

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """

    @abstractproperty
    def outgoing_edge_partitions(self):
        """ The outgoing edge partitions in the graph

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_outgoing_edge_partition.AbstractOutgoingEdgePartition`
        """

    @abstractproperty
    def n_outgoing_edge_partitions(self):
        """ The number of outgoing edge partitions in the graph

        :rtype: int
        """

    @abstractmethod
    def get_edges_starting_at_vertex(self, vertex):
        """ Get all the edges that start at the given vertex

        :param vertex: The vertex at which the edges to get start
        :type vertex:\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """

    @abstractmethod
    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex

        :param vertex: The vertex at which the edges to get end
        :type vertex:\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """

    @abstractmethod
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex

        :param vertex: The vertex at which the edge partitions to find starts
        :type vertex:\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :rtype: \
            iterable of\
            :py:class:`pacman.model.graphs.abstract_outgoing_edge_partition.AbstractOutgoingEdgePartition`
        """

    @abstractmethod
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """ Get the given outgoing edge partition that starts at the\
            given vertex, or None if no such edge partition exists

        :param vertex: The vertex at the start of the edges in the partition
        :type vertex:\
            :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        :param outgoing_edge_partition_name: The name of the edge partition
        :type outgoing_edge_partition_name: str
        :rtype:\
            :py:class:`pacman.model.graphs.abstract_outgoing_edge_partition.AbstractOutgoingEdgePartition`
        """

    @abstractmethod
    def get_outgoing_edge_partitions_with_traffic_type(self, traffic_type):
        """ Get the outgoing edge partitions with a given traffic type

        :param traffic_type: The traffic type to look for
        :type traffic_type:\
            :py:class:`pacman.model.graphs.common.edge_traffic_type.EdgeTrafficType`
        """
