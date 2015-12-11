
# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman.exceptions import PacmanInvalidParameterException
from pacman.utilities.utility_objs.outgoing_edge_partition \
    import OutgoingEdgePartition

# general imports
import uuid


class PartitionableGraph(object):
    """ Represents a collection of vertices and edges between vertices that \
        make up a partitionable graph i.e. a graph whose vertices can be \
        divided up.
    """

    def __init__(self, label=None):
        """

        :param label: An identifier for the partitionable_graph
        :type label: str
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the edges is not valid
                    * If one of the vertices in not valid
        """
        self._label = label
        self._vertices = list()
        self._edges = list()

        self._outgoing_edges = dict()
        self._incoming_edges = dict()

    def add_vertex(self, vertex):
        """ Add a vertex to this partitionable_graph

        :param vertex: a vertex to be added to the partitionable graph
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: \
                    If the vertex is not valid
        """
        if vertex is not None and isinstance(vertex,
                                             AbstractPartitionableVertex):
            self._vertices.append(vertex)
            self._outgoing_edges[vertex] = dict()
            self._incoming_edges[vertex] = list()
        else:
            raise PacmanInvalidParameterException(
                "vertex", str(vertex),
                "Must be an instance of pacman.model.partitionable_graph"
                ".abstract_partitionable_vertex.AbstractPartitionableVertex")

    def add_vertices(self, vertices):
        """ Add an iterable of vertices to this partitionable graph

        :param vertices: an iterable of vertices to be added to the graph
        :type vertices: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: \
                    If any vertex in the iterable is not valid
        """
        if vertices is not None:
            for next_vertex in vertices:
                self.add_vertex(next_vertex)

    def add_edge(self, edge, partition_id=None, partition_constraints=None):
        """ Add an edge to this partitionable_graph

        :param edge: an edge to be added to the partitionable_graph
        :type edge:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :param partition_id: the id for the outgoing partition that this edge
        is associated with
        :type partition_id: str
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the edge\
                    is not valid
        """
        if edge is not None and isinstance(edge, AbstractPartitionableEdge):
            self._edges.append(edge)

            # if the partition id is none, make a unique one for storage
            if partition_id is None:
                partition_id = str(uuid.uuid4())

            # if this partition id not been seen before, add a new partition
            if partition_id not in self._outgoing_edges[edge.pre_vertex]:
                self._outgoing_edges[edge.pre_vertex][partition_id] = \
                    OutgoingEdgePartition(partition_id, partition_constraints)
            self._outgoing_edges[edge.pre_vertex][partition_id].add_edge(edge)
            self._incoming_edges[edge.post_vertex].append(edge)
        else:
            raise PacmanInvalidParameterException(
                "edge", str(edge),
                "Must be an instance of pacman.model.partitionable_graph"
                ".edge.AbstractPartitionableEdge")

    def add_edges(self, edges, partition_id=None, constraints=None):
        """ Add an iterable of edges to this partitionable_graph

        :param edges: an iterable of edges to be added to the graph
        :type edges: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :param partition_id: the id for the outgoing partition that this edge\
                    is associated with
        :type partition_id: str
        :param constraints: constraints added to a edge
        :type constraints: iterable of \
                :py:class:`pacman.model.constraints.abstract_constraints.abstract_constrant.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If any edge\
                    in the iterable is not valid
        """
        if edges is not None:
            for next_edge in edges:
                self.add_edge(next_edge, partition_id, constraints)

    def outgoing_edges_from_vertex(self, vertex, partition_identifier=None):
        """ Locate a collection of edges for which vertex is the pre_vertex.\
            Can return an empty collection.

        :param vertex: the vertex for which to find the outgoing edges
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :param partition_identifier: the identifier for the partition that\
                   the edges being returned should associate with. If set to\
                   None, returns all edges from all partitions
        :type partition_identifier: string or None
        :return: an iterable of edges which have vertex as their pre_vertex
        :rtype: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :raise None: does not raise any known exceptions
        """
        # if no partition, given edges from all partitions
        if partition_identifier is None:
            edges = list()
            for partition in self._outgoing_edges[vertex]:
                edges.extend(self._outgoing_edges[vertex][partition].edges)
            return edges
        # if no partition then return empty list
        elif partition_identifier not in self._outgoing_edges[vertex]:
            return ()
        else:
            return self._outgoing_edges[vertex][partition_identifier]

    def outgoing_edges_partitions_from_vertex(self, vertex):
        """ Locates all the outgoing edge partitions for a given vertex

        :param vertex: the vertex for which the outgoing edge partitions are to
         be located for.
         :type vertex: \
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: iterable of\
                     :py:class:`pacman.utilities.outgoing_edge_partition.OutgoingEdgePartition`
                     or a empty list if none are available
        :raise None: does not raise any known exceptions
        """
        if vertex in self._outgoing_edges:
            return self._outgoing_edges[vertex]
        else:
            return ()

    def partition_from_vertex(self, vertex, partition_id):
        """

        :param vertex:
        :param partition_id:
        :return:
        """
        if partition_id is None:
            return None
        return self._outgoing_edges[vertex][partition_id]

    @property
    def partitions(self):
        """
        property method for all the partitions in the graph
        :return: iterable of\
                     :py:class:`pacman.utilities.outgoing_edge_partition.OutgoingEdgePartition`
        """
        partitions = list()
        for vertex in self._vertices:
            partitions.extend(
                self.outgoing_edges_partitions_from_vertex(vertex))
        return partitions

    def incoming_edges_to_vertex(self, vertex):
        """ Locate a collection of edges for which vertex is the post_vertex.\
            Can return an empty collection.

        :param vertex: the vertex for which to find the incoming edges
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: an iterable of edges which have vertex as their post_vertex
        :rtype: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :raise None: does not raise any known exceptions
        """
        return self._incoming_edges[vertex]

    @property
    def label(self):
        """ The label of the partitionable_graph

        :return: The label or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @property
    def vertices(self):
        """ The vertices of the partitionable_graph

        :return: an iterable of vertices
        :rtype: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        """
        return self._vertices

    @property
    def edges(self):
        """ The edges of the partitionable_graph

        :return: an iterable of edges
        :rtype: iterable of\
                    :py:class:`pacman.model.partitionable_graph.edge.AbstractPartitionableEdge`
        """
        return self._edges
