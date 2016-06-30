from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractGraph(object):
    """ A graph
    """

    @abstractmethod
    def add_vertex(self, vertex):
        """ Add a vertex to the graph

        :param vertex: The vertex to add
        :type vertex: :py:class:`pacman.model.graph.AbstractVertex`
        :raises PacmanInvalidParameterException:\
            If the vertex is not of a valid type
        """

    @abstractmethod
    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph

        :param edge: The edge to add
        :type edge: :py:class:`pacman.model.graph.AbstractEdge`
        :param outgoing_edge_partition_name: \
            The name of the edge partition to add the edge to; each edge\
            partition is the partition of edges that start at the same vertex
        :type outgoing_edge_partition_name: str
        :raises PacmanInvalidParameterException:\
            If the edge is not of a valid type or if edges have already been\
            added to this partition that start at a different vertex to this\
            one
        """

    @abstractmethod
    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        """ Add an outgoing edge partition to the graph

        :param outgoing_edge_partition: The outgoing edge partition to add
        :type outgoing_edge_partition:\
            :py:class:`pacman.model.graph.AbstractOutgoingEdgePartition`
        :raises PacmanAlreadyExistsException:\
            If a partition already exists with the same pre_vertex and\
            identifier
        """

    @abstractproperty
    def vertices(self):
        """ The vertices in the graph

        :rtype: iterable of :py:class:`pacman.model.graph.AbstractVertex`
        """

    @abstractproperty
    def edges(self):
        """ The edges in the graph

        :rtype: iterable of :py:class:`pacman.model.graph.AbstractEdge`
        """

    @abstractproperty
    def outgoing_edge_partitions(self):
        """ The outgoing edge partitions in the graph

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graph.AbstractOutgoingEdgePartition`
        """

    @abstractmethod
    def get_edges_starting_at_vertex(self, vertex):
        """ Get all the edges that start at the given vertex

        :param vertex: The vertex at which the edges to get start
        :type vertex: :py:class:`pacman.model.graph.AbstractVertex`
        :rtype: iterable of :py:class:`pacman.model.graph.AbstractEdge`
        """

    @abstractmethod
    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex

        :param vertex: The vertex at which the edges to get end
        :type vertex: :py:class:`pacman.model.graph.AbstractVertex`
        :rtype: iterable of :py:class:`pacman.model.graph.AbstractEdge`
        """

    @abstractmethod
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex

        :param vertex: The vertex at which the edge partitions to find starts
        :type vertex: :py:class:`pacman.model.graph.AbstractVertex`
        :rtype: \
            iterable of\
            :py:class:`pacman.model.graph.AbstractOutgoingEdgePartition`
        """

    @abstractmethod
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """ Get the given outgoing edge partition that starts at the\
            given vertex, or None if no such edge partition exists

        :param vertex: The vertex at the start of the edges in the partition
        :type vertex: :py:class:`pacman.model.graph.AbstractVertex`
        :param outgoing_edge_partition_name: The name of the edge partition
        :type outgoing_edge_partition_name: str
        :rtype: :py:class:`pacman.model.graph.AbstractOutgoingEdgePartition`
        """
