from six import add_metaclass

from spinn_utilities.abstract_base import \
    AbstractBase, abstractmethod, abstractproperty


@add_metaclass(AbstractBase)
class AbstractGraph(object):
    """ A graph
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """

    @abstractproperty
    def constraints(self):
        """ The constraints of the vertex

        :rtype: iterable(:py:class:`AbstractConstraint`)
        """

    @abstractmethod
    def add_constraint(self, constraint):
        """ Add a constraint

        :param constraint: The constraint to add
        :type constraint: :py:class:`AbstractConstraint`
        """

    def add_constraints(self, constraints):
        """ Add a list of constraints

        :param constraints: The list of constraints to add
        :type constraints: list(:py:class:`AbstractConstraint`)
        """
        for constraint in constraints:
            self.add_constraint(constraint)

    @abstractmethod
    def add_vertex(self, vertex):
        """ Add a vertex to the graph

        :param vertex: The vertex to add
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :raises PacmanInvalidParameterException:\
            If the vertex is not of a valid type
        """

    def add_vertices(self, vertices):
        """ Add a collection of vertices to the graph.

        :param vertices: The vertices to add
        :type vertices: \
            iterable(:py:class:`pacman.model.graphs.AbstractVertex`)
        :raises PacmanInvalidParameterException:\
            If any vertex is not of a valid type
        """
        for v in vertices:
            self.add_vertex(v)

    @abstractmethod
    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph

        :param edge: The edge to add
        :type edge: :py:class:`pacman.model.graphs.AbstractEdge`
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
        :type edges: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
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
            :py:class:`pacman.model.graphs.AbstractOutgoingEdgePartition`
        :raises PacmanAlreadyExistsException:\
            If a partition already exists with the same pre_vertex and\
            identifier
        """

    @abstractproperty
    def vertices(self):
        """ The vertices in the graph

        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractVertex`)
        """

    @abstractproperty
    def n_vertices(self):
        """ The number of vertices in the graph

        :rtype: int
        """

    @abstractproperty
    def edges(self):
        """ The edges in the graph

        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """

    @abstractproperty
    def outgoing_edge_partitions(self):
        """ The outgoing edge partitions in the graph

        :rtype: \
            iterable(:py:class:`pacman.model.graphs.AbstractOutgoingEdgePartition`)
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
            :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """

    @abstractmethod
    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex

        :param vertex: The vertex at which the edges to get end
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """

    @abstractmethod
    def get_edges_ending_at_vertex_with_partition_name(
            self, vertex, partition_name):
        """ Get all the edges that end at the given vertex, and reside in the\
            correct partition ID

        :param vertex:  The vertex at which the edges to get end
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :param partition_name: the label for the partition
        :type partition_name: str
        :return: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """

    @abstractmethod
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex

        :param vertex: The vertex at which the edge partitions to find starts
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: \
            iterable(:py:class:`pacman.model.graphs.AbstractOutgoingEdgePartition`)
        """

    @abstractmethod
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """ Get the given outgoing edge partition that starts at the\
            given vertex, or None if no such edge partition exists

        :param vertex: The vertex at the start of the edges in the partition
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :param outgoing_edge_partition_name: The name of the edge partition
        :type outgoing_edge_partition_name: str
        :rtype:\
            :py:class:`pacman.model.graphs.AbstractOutgoingEdgePartition`
        """
